"""CET-6 Vocabulary Learning - FastAPI Backend"""
import json
import os
import re
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI(title="CET-6 Vocabulary Learning")
BASE_DIR = Path(__file__).parent

# --- Load data ---
with open(BASE_DIR / "cet6_words.json", "r", encoding="utf-8") as f:
    CET6_DB = {w["word"]: {"meaning": w["meaning"], "freq": w["freq"]} for w in json.load(f)["words"]}

USER_WORDS_FILE = BASE_DIR / "user_words.json"
if USER_WORDS_FILE.exists():
    with open(USER_WORDS_FILE, "r", encoding="utf-8") as f:
        USER_WORDS = json.load(f)
else:
    USER_WORDS = {}

def save_user_words():
    with open(USER_WORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(USER_WORDS, f, ensure_ascii=False, indent=2)

def get_llm_client():
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY", "")
    base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("LLM_BASE_URL") or "https://api.openai.com/v1"
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    return OpenAI(api_key=api_key, base_url=base_url), model

# --- Models ---
class WordAdd(BaseModel):
    word: str
    meaning: str
    custom_color: Optional[str] = None  # Override color: "red","blue","green","gray","none"

class WordUpdate(BaseModel):
    meaning: Optional[str] = None
    custom_color: Optional[str] = None  # none to reset to default

class TextGenRequest(BaseModel):
    style: Optional[str] = None
    structure: Optional[str] = None
    length: Optional[int] = None
    topic: Optional[str] = None

class ChatRequest(BaseModel):
    persona: str
    message: str
    history: list[dict] = []

# --- Helpers ---
def get_cet6_info(word_clean: str) -> dict:
    return CET6_DB.get(word_clean, {"meaning": "", "freq": 0})

def get_freq_color(freq: int, custom_color: Optional[str] = None) -> str:
    if custom_color and custom_color != "none":
        return custom_color
    if freq >= 10:
        return "red"
    elif freq >= 3:
        return "blue"
    elif freq >= 1:
        return "green"
    else:
        return "gray"

# --- API: Words ---
@app.get("/api/words")
def get_words():
    result = []
    for word, data in USER_WORDS.items():
        cet6 = get_cet6_info(word)
        freq = cet6["freq"]
        color = get_freq_color(freq, data.get("custom_color"))
        result.append({
            "word": word,
            "meaning": data["meaning"],
            "cet6_meaning": cet6["meaning"],
            "freq": freq,
            "color": color,
            "custom_color": data.get("custom_color", "none"),
        })
    return {"words": sorted(result, key=lambda x: x["word"])}

@app.post("/api/words")
def add_word(body: WordAdd):
    word = body.word.strip().lower()
    if not word or not re.match(r"^[a-z\-']+$", word):
        raise HTTPException(400, "Invalid English word")
    if word in USER_WORDS:
        raise HTTPException(400, f"'{word}' already exists")
    cet6 = get_cet6_info(word)
    USER_WORDS[word] = {
        "meaning": body.meaning.strip(),
        "cet6_freq": cet6["freq"],
        "custom_color": body.custom_color,
    }
    save_user_words()
    return {"word": word, "freq": cet6["freq"], "in_cet6": cet6["freq"] > 0}

@app.delete("/api/words/{word}")
def delete_word(word: str):
    word = word.strip().lower()
    if word not in USER_WORDS:
        raise HTTPException(404, f"'{word}' not found")
    del USER_WORDS[word]
    save_user_words()
    return {"ok": True}

@app.put("/api/words/{word}")
def update_word(word: str, body: WordUpdate):
    word = word.strip().lower()
    if word not in USER_WORDS:
        raise HTTPException(404, f"'{word}' not found")
    if body.meaning is not None:
        USER_WORDS[word]["meaning"] = body.meaning.strip()
    if body.custom_color is not None:
        USER_WORDS[word]["custom_color"] = body.custom_color if body.custom_color != "none" else None
    save_user_words()
    cet6 = get_cet6_info(word)
    return {
        "word": word,
        "meaning": USER_WORDS[word]["meaning"],
        "freq": cet6["freq"],
        "color": get_freq_color(cet6["freq"], USER_WORDS[word].get("custom_color")),
    }

@app.get("/api/cet6/check/{word}")
def check_word(word: str):
    word = word.strip().lower()
    cet6 = get_cet6_info(word)
    return {"word": word, "freq": cet6["freq"], "meaning": cet6["meaning"], "in_cet6": cet6["freq"] > 0}

# --- CET-6 word list for prompts ---
def get_user_words_list() -> list[str]:
    return list(USER_WORDS.keys())

def get_cet6_sample(count: int = 50) -> list[str]:
    import random
    all_words = list(CET6_DB.keys())
    random.shuffle(all_words)
    return all_words[:count]

# --- Module 1: Reading Text ---
@app.post("/api/generate-text")
def generate_text(body: TextGenRequest):
    word_list = get_user_words_list()
    user_words_str = ", ".join(word_list) if word_list else "(none)"
    cet6_sample = get_cet6_sample(80)

    length = body.length if body.length else 250
    style = body.style if body.style else "descriptive essay"
    structure = body.structure if body.structure else "introduction-body-conclusion"
    topic = body.topic if body.topic else "a topic suitable for CET-6 level"

    prompt = f"""You are an CET-6 English exam expert. Write an English passage with the following requirements:

Topic: {topic}
Style: {style}
Structure: {structure}
Length: approximately {length} words

Vocabulary requirements:
1. You MUST include these user-provided words in the passage: {user_words_str}
2. Use ONLY words at or below CET-6 difficulty level (no GRE/TOEFL/advanced vocabulary)
3. Use simple grammar structures suitable for Chinese college students
4. Sentence length should be moderate (15-25 words per sentence)

Format the passage in plain text. Mark user-provided words with **[word]** format when they appear the first time, and use regular format for subsequent occurrences. At the end, list the CET-6 vocabulary used with Chinese meanings in a "Vocabulary Notes" section.

IMPORTANT: Keep all words and grammar at or below CET-6 level. Do NOT use advanced vocabulary."""

    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("LLM_API_KEY"):
        return {"text": generate_mock_reading(word_list, topic), "mode": "mock", "user_words_used": word_list}

    try:
        client, model = get_llm_client()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500,
        )
        text = response.choices[0].message.content
        return {"text": text, "mode": "ai", "user_words_used": word_list}
    except Exception as e:
        return {"text": generate_mock_reading(word_list, topic), "mode": "mock (API error)", "user_words_used": word_list, "error": str(e)}

def generate_mock_reading(user_words: list[str], topic: str) -> str:
    """Generate a simple reading passage without AI"""
    if not user_words:
        return f"""Title: The Importance of Learning

In today's rapidly changing world, the ability to acquire new knowledge has become increasingly significant. Many people recognize that education is not merely a phase of life but a continuous process. As we encounter various challenges in our daily lives, we must be prepared to adapt and grow.

The modern workplace demands that employees possess a wide range of skills. Beyond technical expertise, employers value critical thinking and effective communication. Those who can analyze complex problems and propose innovative solutions tend to be more competitive in the job market.

However, learning is not just about professional development. It enriches our lives in profound ways, allowing us to appreciate different cultures and perspectives. Reading literature, for example, helps us understand the human experience across time and space. Through learning, we not only improve our career prospects but also become better citizens of the global community.

In conclusion, the pursuit of knowledge is both a practical necessity and a source of personal fulfillment. Whether we are learning for career advancement or personal growth, the effort we invest in education always yields valuable results.

Vocabulary Notes:
- acquire: 获得；习得
- significant: 重要的；显著的
- recognize: 认出；承认
- merely: 仅仅；只不过
- encounter: 遇到；邂逅
- adapt: 适应；改编
- possess: 拥有
- expertise: 专业知识；专长
- critical: 关键的；批判的
- analyze: 分析
- complex: 复杂的
- innovative: 创新的
- competitive: 竞争的
- profound: 深刻的
- appreciate: 欣赏；感激
- perspective: 观点；视角
- literature: 文学
- community: 社区；团体
- pursuit: 追求
- yield: 产出；产出"""
    
    parts = []
    for w in user_words:
        info = CET6_DB.get(w, {"meaning": "", "freq": 0})
        parts.append(f"**{w}** ({info['meaning']})")
    vocab_notes = "\n".join(parts)
    
    return f"""Title: The Power of Vocabulary

Every language learner knows that building a strong vocabulary is essential to mastering a new language. The words we choose to learn reflect our interests and goals. As we explore new topics and engage with different types of content, we naturally encounter unfamiliar words that expand our understanding.

In the context of CET-6 preparation, students must be diligent and persistent. They need to cultivate good study habits and maintain a positive attitude toward learning. While some may find the process challenging, those who dedicate themselves to regular practice will undoubtedly see significant improvement over time.

Reading English texts is one of the most effective ways to reinforce vocabulary knowledge. When we read, we see words used in authentic contexts, which helps us grasp their subtle meanings and appropriate usage. Writing exercises also play a crucial role, as they require us to actively produce language rather than simply recognize it.

{generate_word_paragraph(user_words[:20])}

In conclusion, vocabulary acquisition is a gradual process that requires patience and consistent effort. By combining reading, writing, and regular review, learners can steadily expand their command of English and achieve their academic goals.

Vocabulary Notes:
{vocab_notes}"""

def generate_word_paragraph(words: list[str]) -> str:
    if not words:
        return ""
    joined = ", ".join(words[:15])
    return f"The following vocabulary items are particularly useful: {joined}. Mastering these words will help learners express their ideas more precisely and confidently in both academic and everyday settings."

# --- Module 2: Chat ---
@app.post("/api/chat")
def chat(body: ChatRequest):
    word_list = get_user_words_list()
    user_words_str = ", ".join(word_list) if word_list else "(none)"
    
    # Build vocabulary context
    vocab_context = ""
    if word_list:
        vocab_context = "\nUser's vocabulary list (you should try to use these words naturally in conversation):\n"
        for w in word_list[:30]:
            info = CET6_DB.get(w, {"meaning": "", "freq": 0})
            m = USER_WORDS.get(w, {}).get("meaning", info.get("meaning", ""))
            vocab_context += f"- {w}: {m}\n"

    persona = body.persona if body.persona else "a friendly English tutor who helps Chinese students practice CET-6 level English"

    system_prompt = f"""You are {persona}.

Rules:
1. Use ONLY vocabulary at or below CET-6 difficulty level
2. Use simple, clear grammar structures
3. Speak in English only (no Chinese unless the user specifically asks for Chinese translation)
4. Keep responses conversational and friendly
5. Try to incorporate the user's learned vocabulary words naturally into the conversation
6. When asked, you can explain word meanings or grammar points
{vocab_context}

Remember: NO advanced vocabulary beyond CET-6 level. Keep it simple and natural."""

    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("LLM_API_KEY"):
        return {"reply": mock_chat(body.message, body.persona, word_list), "mode": "mock"}

    messages = [{"role": "system", "content": system_prompt}]
    for h in body.history:
        messages.append(h)
    messages.append({"role": "user", "content": body.message})

    try:
        client, model = get_llm_client()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.8,
            max_tokens=600,
        )
        return {"reply": response.choices[0].message.content, "mode": "ai"}
    except Exception as e:
        return {"reply": mock_chat(body.message, body.persona, word_list), "mode": "mock (API error)", "error": str(e)}

def mock_chat(msg: str, persona: str, word_list: list[str]) -> str:
    msg_lower = msg.lower()
    if "hello" in msg_lower or "hi" in msg_lower:
        return f"Hello! I'm {persona}. How can I help you practice English today? Feel free to talk about any topic you like!"
    if "meaning" in msg_lower or "mean" in msg_lower or "meaning of" in msg_lower or "what is" in msg_lower or "what does" in msg_lower:
        for w in word_list:
            if w in msg_lower:
                info = CET6_DB.get(w, {"meaning": "", "freq": 0})
                return f"The word **{w}** means: {info.get('meaning', 'Not found in CET-6 database')}."
        return "I'm not sure which word you're referring to. Could you specify the exact word?"
    if "translate" in msg_lower or "翻译" in msg:
        return "I'd be happy to help translate! Please provide the word or sentence, and I'll do my best using CET-6 level vocabulary."
    if "bye" in msg_lower or "goodbye" in msg_lower:
        return "Goodbye! Keep practicing your English. Every little effort counts. See you next time!"
    
    # Incorporate user words in response
    used_words = ", ".join(word_list[:5]) if word_list else "vocabulary"
    return f"That's an interesting point! Using words like {used_words} can help you express your ideas more clearly. Keep practicing, and don't hesitate to ask if you need any word meanings explained!"

# --- Serve static files ---
@app.get("/api/info")
def info():
    return {
        "cet6_total_words": len(CET6_DB),
        "user_total_words": len(USER_WORDS),
        "has_llm": bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")),
    }

# Mount static files last
static_dir = BASE_DIR / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
