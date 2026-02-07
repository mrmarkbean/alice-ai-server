import os, base64, json
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

INSTRUCTIONS = (
    "You are a whimsical narrator in the world of Alice in Wonderland. "
    "Invent a strange character inspired by the image. "
    "Return ONLY valid JSON with keys: title, story. "
    "Story length 120–200 words, include one short line of dialogue."
)

def get_client():
    key = os.getenv("OPENAI_API_KEY", "")
    key = key.strip().strip('"').strip("'")
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
        return jsonify({
            "title": "Error",
            "story": "No image received"
        }), 400

    b64 = base64.b64encode(jpg).decode("utf-8")
    data_url = f"data:image/jpeg;base64,{b64}"

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": INSTRUCTIONS + "\nRespond with JSON only."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url}
                        }
                    ]
                }
            ]
        )

        text = (response.choices[0].message.content or "").strip()
        return jsonify(json.loads(text))

    except Exception as e:
        return jsonify({
            "title": "Server error",
            "story": str(e)
        }), 500
