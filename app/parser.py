import json, re
from google import genai
from google.genai import types
from .config import GEMINI_API_KEY, GEMINI_MODEL

PROMPT = r"""
Read this JEE Main page image and return valid JSON only:
{"questions":[{"id":26,"type":"mcq","hasFigure":true,
"figure_bbox":[100,200,800,600],"question":"...","options":["...","...","...","..."],
"correct":null,"solution":""}]}
Coordinates are normalized 0-1000 relative to the FULL page, ordered [left,top,right,bottom].
Include every visible question and use its printed number. Types: mcq, numerical, match_list, assertion_reason.
If a diagram/graph/circuit exists, hasFigure=true and figure_bbox must tightly enclose ONLY the visual, excluding question text and options. Otherwise hasFigure=false and figure_bbox=null.
Use LaTeX for math. Do not guess answers: use null and empty solution unless confident. JSON only.
"""

def parse_page(image):
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY missing. Add it to .env.")
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL, contents=[PROMPT, image],
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1)
    )
    raw = re.sub(r"^```(?:json)?\\s*|\\s*```$", "", (response.text or "").strip(), flags=re.I)
    data = json.loads(raw)
    if not isinstance(data.get("questions"), list):
        raise ValueError("Gemini response has no questions array")
    return data["questions"]
