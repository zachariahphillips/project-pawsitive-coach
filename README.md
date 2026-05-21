# Pawsitive Coach - AI Dog Training Assistant

An AI-powered dog training coach that specializes in **positive reinforcement** methods and building a strong, trusting relationship between you and your dog.

## Philosophy

Pawsitive Coach only recommends reward-based training. It will never suggest punishment, dominance-based methods, or aversive tools (prong collars, shock collars, etc.). The focus is on:

- Understanding *why* your dog behaves a certain way
- Building trust and communication
- Celebrating small wins and encouraging patience
- Treating every dog as an individual

## What you can ask about

- Puppy training (biting, potty training, socialization)
- Leash manners and loose-leash walking
- Fearful or anxious dogs
- Crate training
- Basic commands (sit, stay, come, leave it)
- Behavior problems (jumping, barking, resource guarding)
- Rescue dog adjustment

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up your environment variables

```bash
cp .env.example .env
```

Edit `.env` and set:

- `OPENAI_API_KEY` — your OpenAI API key. Get one at: https://platform.openai.com/api-keys
- `FLASK_SECRET_KEY` — any long random string. Used to sign session cookies. Generate one with:
  ```bash
  python3 -c "import secrets; print(secrets.token_hex(32))"
  ```

### 3. Run the web app

```bash
python3 app.py
```

Open http://localhost:5000 in your browser.

### 3b. Or run the terminal version

```bash
python3 chat.py
```

## Cost

Uses GPT-4o-mini (~$0.15/million input tokens, ~$0.60/million output tokens).
For casual use, expect to spend pennies per session.

## Disclaimer

This is an AI assistant, not a substitute for professional help. For serious behavioral issues (aggression, severe anxiety, etc.), please consult a certified professional dog trainer (CPDT-KA) or veterinary behaviorist.

## Project Structure

```
project-pawsitive-coach/
├── app.py              # Web app (Flask)
├── chat.py             # Terminal chatbot
├── requirements.txt    # Python dependencies
├── .env.example        # Template for env vars (API key + session signing key)
├── .gitignore          # Keeps secrets and session files out of GitHub
├── flask_session/      # Server-side session store (auto-created, gitignored)
├── templates/
│   └── index.html      # Chat UI
└── README.md
```
