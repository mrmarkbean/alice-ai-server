import os, base64, json
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

INSTRUCTIONS = (
    "You are a whimsical narrator in the world of Alice in Wonderland. "
    "Invent a strange character inspired by the image. "
    "Return ONLY valid JSON with keys: title, story. "
    "Story length 120–200 words, include one short line of dialogue."
)

@app.post("/analyze")
def analyze():
    jpg = request.data
    if not jpg:
        return jsonify({"title": "Error", "story": "No image received."}), 400

    b64 = base64.b64encode(jpg).decode("utf-8")
    data_url = f"data:image/jpeg;base64,{b64}"

    r = client.responses.create(
        model="gpt-4.1-mini",
        instructions=INSTRUCTIONS,
        input=[{
            "role": "user",
            "content": [
                {"type": "input_image", "image_url": data_url},
                {"type": "input_text", "text": "Respond with JSON only."}
            ]
        }],
    )

    text = r.output_text.strip()

    try:
        obj = json.loads(text)
        # minimal schema guard
        if "title" not in obj or "story" not in obj:
            raise ValueError("Missing keys")
        return jsonify(obj)
    except Exception:
        return jsonify({"title": "The Cheshire Parser", "story": text})
