import json, shutil, tempfile, zipfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from .config import PDF_DPI, GEMINI_MODEL
from .pdf_utils import render_pages, crop_figure, valid_bbox
from .parser import parse_page

app=FastAPI(title="RankPilot Diagram Engine MVP", version="0.1.0")
ROOT=Path(__file__).resolve().parent.parent
ROOT.mkdir(exist_ok=True)

@app.get("/")
def health():
    return {"status":"ready","model":GEMINI_MODEL,"usage":"Open /docs and POST a PDF to /process"}

@app.post("/process")
async def process_pdf(file: UploadFile=File(...), paper_id: str=Form("jee_paper")):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400,"Upload a PDF file")
    safe_id="".join(c for c in paper_id if c.isalnum() or c in "-_")[:80] or "jee_paper"
    job=Path(tempfile.mkdtemp(prefix="rankpilot_"))
    pdf=job/"input.pdf"; out=job/safe_id; images=out/"images"; images.mkdir(parents=True)
    try:
        with pdf.open("wb") as f: shutil.copyfileobj(file.file,f)
        questions=[]; warnings=[]
        for page_num, page_image in render_pages(str(pdf),PDF_DPI):
            try: found=parse_page(page_image)
            except Exception as e:
                warnings.append(f"Page {page_num} failed: {e}"); continue
            for item in found:
                qid=item.get("id")
                if not isinstance(qid,int):
                    warnings.append(f"Page {page_num}: skipped question with invalid ID"); continue
                has_fig=bool(item.get("hasFigure")); bbox=item.get("figure_bbox"); image_name=None
                if has_fig and valid_bbox(bbox):
                    image_name=f"{safe_id}_q{qid}.png"
                    try: crop_figure(page_image,bbox,images/image_name)
                    except Exception as e:
                        warnings.append(f"Q{qid}: crop failed: {e}"); image_name=None
                elif has_fig: warnings.append(f"Q{qid}: figure detected but bounding box invalid/missing")
                q={"id":qid,"type":item.get("type","mcq"),"hasFigure":bool(image_name),
                   "image":image_name,"question":item.get("question",""),
                   "options":item.get("options"),"correct":item.get("correct"),
                   "solution":item.get("solution",""),"sourcePage":page_num}
                if q["type"]=="numerical" and q["options"] is None: q.pop("options")
                questions.append(q)
        unique={}
        duplicates=[]
        for q in questions:
            if q["id"] in unique: duplicates.append(q["id"])
            else: unique[q["id"]]=q
        questions=sorted(unique.values(),key=lambda q:q["id"])
        result={"paper_id":safe_id,"total_questions":len(questions),"questions":questions,
                "review":{"warnings":warnings,"duplicate_ids":sorted(set(duplicates)),
                "note":"Verify question text, answers and diagram boundaries before publishing."}}
        json_path=out/f"{safe_id}.json"
        json_path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
        zip_path=job/f"{safe_id}_rankpilot_package.zip"
        with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED) as z:
            z.write(json_path,f"{safe_id}/{safe_id}.json")
            for p in sorted(images.glob("*.png")): z.write(p,f"{safe_id}/images/{p.name}")
            z.writestr(f"{safe_id}/IMPORT_NOTES.txt","Review JSON warnings and verify every crop before importing into RankPilot.\n")
        return FileResponse(str(zip_path),media_type="application/zip",filename=zip_path.name)
    finally:
        await file.close()
