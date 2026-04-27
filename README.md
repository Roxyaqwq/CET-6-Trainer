# CET-6 Vocabulary Learning Tool

A full-stack web application for Chinese college students to learn CET-6 vocabulary through word management, AI-generated reading passages, and conversational practice.

## Features

### Word Management
- Add English words with Chinese meanings (auto-detects CET-6 status)
- **Auto-fill**: if the word is in the CET-6 database, the Chinese meaning is filled automatically
- Color-coded by CET-6 exam frequency:
  - **Red** (>= 10) — High frequency
  - **Blue** (3–10) — Medium frequency
  - **Green** (1–3) — Low frequency
  - **Gray** (0) — Not in CET-6
- Edit/delete words, override color
- Duplicate word prevention

### Reading Text Generation
- AI generates reading passages using only <= CET-6 level vocabulary
- Your learned words are naturally incorporated into the text
- Configurable: topic, style (narrative/descriptive/argumentative/expository), structure, and length
- Word annotations with Chinese meanings at the end

### AI Chat
- Chat with an AI persona you define (tutor, tour guide, interviewer, etc.)
- Conversations are limited to CET-6 level vocabulary and simple grammar
- Your vocabulary list is provided as context so the AI tries to use your words

### CET-6 Database
- 899 CET-6 words with exam frequencies and Chinese meanings
- Extensible: re-run `generate_cet6.py` to rebuild the database

## Tech Stack

- **Backend**: Python FastAPI
- **Frontend**: Vanilla HTML/CSS/JavaScript (SPA)
- **AI**: OpenAI-compatible API (DeepSeek, OpenAI, or any compatible LLM)
- **Data**: Local JSON files

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure LLM API

Copy the example env file and fill in your API key:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# DeepSeek example
LLM_API_KEY=sk-your-key-here
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# OpenAI example
# OPENAI_API_KEY=sk-your-key-here
```

> The app works **without** an API key in demo/mock mode — reading and chat use built-in templates.

### 3. Run the server

```bash
python -m uvicorn backend:app --host 0.0.0.0 --port 8000 --reload
```

Open http://localhost:8000 in your browser.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/words` | List all user words |
| POST | `/api/words` | Add a new word |
| PUT | `/api/words/{word}` | Update word meaning/color |
| DELETE | `/api/words/{word}` | Delete a word |
| GET | `/api/cet6/check/{word}` | Check CET-6 status & frequency |
| POST | `/api/generate-text` | Generate reading passage |
| POST | `/api/chat` | Chat with AI persona |
| GET | `/api/info` | System info |

## Project Structure

```
cet6-project/
├── backend.py          # FastAPI server
├── cet6_words.json     # CET-6 word database (899 words)
├── generate_cet6.py    # Script to regenerate the database
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── .gitignore
├── user_words.json     # Your personal word list (gitignored)
└── static/
    ├── index.html      # Frontend UI
    ├── style.css       # Styles
    └── app.js          # Frontend logic
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_API_KEY` / `OPENAI_API_KEY` | API key for LLM service | (required for AI mode) |
| `LLM_BASE_URL` / `OPENAI_BASE_URL` | LLM API endpoint | `https://api.openai.com/v1` |
| `LLM_MODEL` | Model name | `gpt-4o-mini` |

## License

MIT
