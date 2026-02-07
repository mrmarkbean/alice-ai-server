import os, base64, json
from flask import Flask, request, jsonify
from openai import OpenAI

@app.get("/")
def health():
    return "ok", 200

@app.get("/envcheck")
def envcheck():
    return {
        "has_key": bool(os.getenv("OPENAI_API_KEY")),
        "key_length": len(os.getenv("OPENAI_API_KEY", "")),
        "python_version": os.sys.version
    }

app = Flask(__name__)

INSTRUCTIONS = (
    "You are a whimsical narrator in the world of Alice in Wonderland. "
    "Invent a strange character inspired by the image. "
    "Return ONLY valid JSON with keys: title, story. "
    "Story length 120–200 words, include one short line of dialogue."
)

def get_client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    return OpenAI(api_key=key)

@app.get("/")
def health():
    return "ok", 200

@app.post("/analyze")
def analyze():
    client = get_client()
    if client is None:
        return jsonify({
            "title": "Config error",
            "story": "OPENAI_API_KEY not set"
        }), 500

    jpg = request.data
    if not jpg:
        return jsonify({"title": "Error", "story": "No image received"}), 400

    b64 = base64.b64encode(jpg).decode("utf-8")
    data_url = f"data:image/jpeg;base64,{b64}"

    r = client.responses.create(
        model="gpt-4.1-mini",
        instructions=INSTRUCTIONS,
        input=[{
            "role": "user",
            "content": [
                {"type": "input_image", "image_url": data_url},
                {"type": "input_text", "text": "Respond with JSON only"}
            ]
        }]
    )

    text = r.output_text.strip()
    try:
        return jsonify(json.loads(text))
    except Exception:
        return jsonify({"title": "Parser error", "story": text})
