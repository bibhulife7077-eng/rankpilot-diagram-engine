# RankPilot Diagram Engine MVP

Separate PDF-to-JSON-and-diagram tool. It does not modify your live RankPilot website.

## Run in Termux
```bash
pkg update
pkg install python
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
```
Add your Gemini API key to `.env`, save, then:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Open `http://127.0.0.1:8000/docs`, use **POST /process**, upload a small JEE PDF, set `paper_id`, and download the ZIP.

## Output
```text
paper_id/
  paper_id.json
  images/
    paper_id_q26.png
  IMPORT_NOTES.txt
```

The JSON contains RankPilot fields: `id`, `type`, `hasFigure`, `image`, `question`, `options`, `correct`, and `solution`, plus `sourcePage`.

## Test plan
Use a 1–3 page PDF with at least one diagram. Confirm all questions are present, each `image` file exists, and the PNG shows only the diagram. Verify answers against an official key before publishing.

## Limitations
This MVP relies on AI-generated bounding boxes; some crops may include extra content or cut off part of a figure. It uses one Gemini request per page and may incur API costs. It does not deploy to Vercel or change RankPilot. Do not trust generated answers without review.
