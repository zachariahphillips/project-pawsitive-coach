"""
Pawsitive Coach - AI Dog Training Assistant
A Flask web app powered by OpenAI's GPT-4o-mini, specializing in
positive reinforcement dog training and relationship building.
"""

import os

from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

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
)


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
    session["dog_profile"] = {
        "name": request.json.get("name", "").strip(),
        "breed": request.json.get("breed", "").strip(),
        "age": request.json.get("age", "").strip(),
        "notes": request.json.get("notes", "").strip(),
    }
    session.modified = True
    return jsonify({"status": "saved"})


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").strip()
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
            max_tokens=500,
        )
        reply = response.choices[0].message.content
        session["conversation"].append({"role": "assistant", "content": reply})
        session.modified = True
        return jsonify({"reply": reply})
    except Exception as e:
        session["conversation"].pop()
        return jsonify({"error": str(e)}), 500


@app.route("/clear", methods=["POST"])
def clear():
    session["conversation"] = []
    return jsonify({"status": "cleared"})


@app.route("/restore", methods=["POST"])
def restore():
    messages = request.json.get("messages", [])
    session["conversation"] = [
        {"role": m["role"], "content": m["content"]}
        for m in messages
        if m.get("role") in ("user", "assistant")
    ]
    session.modified = True
    return jsonify({"status": "restored"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
