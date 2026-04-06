"""
AI 对话引擎
本地 Ollama (Gemma 4 E2B) — 低延迟，离线可用。
翻译模式：自动检测中↔挪威语。
"""

from __future__ import annotations
from config import OLLAMA_HOST, OLLAMA_MODEL, PIXEL_SYSTEM_PROMPT

_client = None


def _get_client():
    global _client
    if _client is None:
        import ollama
        _client = ollama.Client(host=OLLAMA_HOST)
    return _client


def chat(message: str, history: list[dict] | None = None) -> str:
    """
    发送消息，返回 Pixel 的回复文字。
    history: [{"role": "user"|"assistant", "content": "..."}]
    """
    client = _get_client()
    messages = [{"role": "system", "content": PIXEL_SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-10:])   # 最近 10 条上下文
    messages.append({"role": "user", "content": message})

    print(f"[ai] 发送给 {OLLAMA_MODEL}...")
    response = client.chat(model=OLLAMA_MODEL, messages=messages)
    reply = response["message"]["content"].strip()
    print(f"[ai] 回复: {reply!r}")
    return reply


def translate(text: str, source_lang: str) -> tuple[str, str]:
    """
    翻译文字。
    zh → no，no/en → zh。
    返回 (translated_text, target_lang)。
    """
    client = _get_client()
    if source_lang == "zh":
        target_lang = "no"
        instruction = f"请把以下中文翻译成挪威语，只输出翻译结果：\n{text}"
    else:
        target_lang = "zh"
        instruction = f"Please translate the following text to Chinese, output only the translation:\n{text}"

    messages = [
        {"role": "system", "content": "You are a professional translator. Output only the translation, no explanations."},
        {"role": "user", "content": instruction},
    ]
    response = client.chat(model=OLLAMA_MODEL, messages=messages)
    result = response["message"]["content"].strip()
    print(f"[ai] 翻译 [{source_lang}→{target_lang}]: {result!r}")
    return result, target_lang
