"""
Pawsitive Coach - AI Dog Training Assistant
A Flask web app powered by OpenAI's GPT-4o-mini, specializing in
positive reinforcement dog training and relationship building.
"""

import json
import os

from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
from openai import OpenAI

load_dotenv()

app = Flask(__name__)

# Stable signing key from env so sessions survive server restarts.
# Falls back to a default for local dev — set FLASK_SECRET_KEY in .env for production.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me-for-production")

# Server-side filesystem session store. Avoids the ~4KB browser cookie limit
# that would otherwise drop long conversations and lose AI context.
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./flask_session"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
Session(app)

SYSTEM_PROMPT = (
    "You are Pawsitive Coach, an expert dog training assistant who specializes in "
    "positive reinforcement methods and building a strong, trusting relationship "
    "between dogs and their humans. "
    "\n\n"
    "Your core training philosophy:\n"
    "- Reward-based training only. Never recommend punishment, dominance-based methods, "
    "alpha theory, prong collars, shock collars, or leash corrections.\n"
    "- Focus on understanding why a dog behaves a certain way, not just stopping the behavior.\n"
    "- Emphasize building trust, communication, and a joyful bond between dog and owner.\n"
    "- Acknowledge that every dog is an individual — breed, age, history, and temperament matter.\n"
    "- Celebrate small wins and encourage patience. Behavior change takes time.\n"
    "\n"
    "When helping someone:\n"
    "- Ask about their dog's breed, age, and history if relevant and not already provided.\n"
    "- Give step-by-step training plans when appropriate.\n"
    "- Explain the 'why' behind your advice so owners truly understand their dog.\n"
    "- Suggest when to consult a certified professional (CPDT-KA, veterinary behaviorist) "
    "for serious issues like aggression or severe anxiety.\n"
    "- Keep your tone warm, encouraging, and judgment-free — everyone is learning.\n"
    "\n"
    "Keep responses concise but thorough. Use short paragraphs for readability. "
    "If you don't know something, say so honestly."
    "\n\n"
    "Formatting your responses:\n"
    "- Use markdown to make answers easy to scan: **bold** for key terms, *italics* "
    "for gentle emphasis, and bullet lists for steps or tips.\n"
    "- Use numbered lists for step-by-step training plans.\n"
    "- Keep paragraphs short (2-4 sentences) with line breaks between them.\n"
    "- Don't over-format short, conversational replies — markdown should help, not clutter."
    "\n\n"
    "Response format (IMPORTANT):\n"
    "Always respond with a single JSON object containing exactly these two keys:\n"
    '- "reply": your full answer to the user as a string (markdown is fine inside the string).\n'
    '- "followups": an array of EXACTLY 2 short follow-up questions the user might naturally '
    "ask next, written from the user's perspective (first-person, e.g. "
    "\"What if she pulls on the leash anyway?\"). Each follow-up must be under 70 characters "
    "and specifically tied to what you just discussed."
)


def _clean_str(value):
    """Coerce a JSON value to a stripped string. Non-strings become ''."""
    if isinstance(value, str):
        return value.strip()
    return ""


def _get_json():
    """Return the request body as a dict. Empty dict if missing or malformed."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def get_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set. Check your .env file.")
    return OpenAI(api_key=api_key)


def build_system_prompt():
    prompt = SYSTEM_PROMPT
    profile = session.get("dog_profile")
    if profile and profile.get("name"):
        parts = [f"\n\nThe user's dog profile:"]
        parts.append(f"- Name: {profile['name']}")
        if profile.get("breed"):
            parts.append(f"- Breed: {profile['breed']}")
        if profile.get("age"):
            parts.append(f"- Age: {profile['age']}")
        if profile.get("notes"):
            parts.append(f"- Notes: {profile['notes']}")
        parts.append("Use this info to personalize your advice. Address the dog by name.")
        prompt += "\n".join(parts)
    return prompt


@app.route("/")
def home():
    session["conversation"] = []
    return render_template("index.html")


@app.route("/profile", methods=["POST"])
def profile():
    data = _get_json()
    session["dog_profile"] = {
        "name": _clean_str(data.get("name")),
        "breed": _clean_str(data.get("breed")),
        "age": _clean_str(data.get("age")),
        "notes": _clean_str(data.get("notes")),
    }
    session.modified = True
    return jsonify({"status": "saved"})


@app.route("/chat", methods=["POST"])
def chat():
    data = _get_json()
    user_message = _clean_str(data.get("message"))
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    if "conversation" not in session:
        session["conversation"] = []

    session["conversation"].append({"role": "user", "content": user_message})

    messages = [{"role": "system", "content": build_system_prompt()}] + session["conversation"]

    try:
        client = get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=700,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        try:
            parsed = json.loads(raw)
            reply = (parsed.get("reply") or "").strip()
            raw_followups = parsed.get("followups") or []
            followups = [
                f.strip() for f in raw_followups
                if isinstance(f, str) and f.strip()
            ][:2]
        except json.JSONDecodeError:
            reply = raw
            followups = []

        if not reply:
            session["conversation"].pop()
            return jsonify({"error": "Empty AI response"}), 500

        session["conversation"].append({"role": "assistant", "content": reply})
        session.modified = True
        return jsonify({"reply": reply, "followups": followups})
    except Exception as e:
        session["conversation"].pop()
        return jsonify({"error": str(e)}), 500


@app.route("/clear", methods=["POST"])
def clear():
    session["conversation"] = []
    return jsonify({"status": "cleared"})


@app.route("/restore", methods=["POST"])
def restore():
    data = _get_json()
    raw_messages = data.get("messages")
    if not isinstance(raw_messages, list):
        raw_messages = []

    cleaned = []
    for m in raw_messages:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        content = m.get("content")
        if role in ("user", "assistant") and isinstance(content, str):
            cleaned.append({"role": role, "content": content})

    session["conversation"] = cleaned
    session.modified = True
    return jsonify({"status": "restored"})


if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
