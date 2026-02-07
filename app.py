import os, base64, json
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

INSTRUCTIONS = (
    "You are a whimsical narrator in the world of Alice in Wonderland. "
    "Invent a strange character inspired by the image. "
    "Return a title and a 120–200 word story. Include one short line of dialogue."
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
        return jsonify({"title": "Config error", "story": "OPENAI_API_KEY not set"}), 500

    jpg = request.data
    if not jpg:
        return jsonify({"title": "Error", "story": "No image received"}), 400

    b64 = base64.b64encode(jpg).decode("utf-8")
    data_url = f"data:image/jpeg;base64,{b64}"

    tools = [{
        "type": "function",
        "function": {
            "name": "make_story",
            "description": "Create an Alice-in-Wonderland character story inspired by the image.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "story": {"type": "string"}
                },
                "required": ["title", "story"],
                "additionalProperties": False
            }
        }
    }]

    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": INSTRUCTIONS},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }],
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "make_story"}},
        )

        msg = resp.choices[0].message
        if not msg.tool_calls:
            return jsonify({"title": "Server error", "story": "No tool call returned"}), 500

        args = msg.tool_calls[0].function.arguments  # JSON string
        obj = json.loads(args)

        # final guard
        title = (obj.get("title") or "").strip()
        story = (obj.get("story") or "").strip()
        if not title or not story:
            return jsonify({"title": "Server error", "story": "Tool call missing fields"}), 500

        return jsonify({"title": title, "story": story})

    except Exception as e:
        return jsonify({"title": "Server error", "story": str(e)}), 500
