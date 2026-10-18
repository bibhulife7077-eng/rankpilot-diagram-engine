import fitz, io
from pathlib import Path
from PIL import Image

def render_pages(pdf_path, dpi):
    doc = fitz.open(pdf_path)
    pages = []
    matrix = fitz.Matrix(dpi/72, dpi/72)
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        pages.append((i+1, Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")))
    doc.close()
    return pages

def valid_bbox(b):
    try:
        x1,y1,x2,y2 = map(float,b)
        return len(b)==4 and 0 <= x1 < x2 <= 1000 and 0 <= y1 < y2 <= 1000
    except Exception:
        return False

def crop_figure(image, bbox, path):
    if not valid_bbox(bbox):
        raise ValueError("Invalid figure_bbox")
    w,h=image.size
    x1,y1,x2,y2=map(float,bbox)
    pad_x, pad_y=max(3,int(w*.008)), max(3,int(h*.008))
    box=(max(0,int(w*x1/1000)-pad_x), max(0,int(h*y1/1000)-pad_y),
         min(w,int(w*x2/1000)+pad_x), min(h,int(h*y2/1000)+pad_y))
    if box[2] <= box[0] or box[3] <= box[1]:
        raise ValueError("Empty crop")
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    image.crop(box).save(path,"PNG",optimize=True)
