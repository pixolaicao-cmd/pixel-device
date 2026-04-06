"""
AI 对话引擎
支持三种运行模式（通过 RUNTIME_MODE 环境变量切换）：
  - "ollama"  : 本地 Ollama (Mac 开发 / RPi5)
  - "rkllama" : Orange Pi 5 原生 NPU (rkllama server)
  - "cloud"   : xAI Grok API (无本地 GPU 时降级)
"""

from __future__ import annotations
from config import (
    OLLAMA_HOST, OLLAMA_MODEL,
    RUNTIME_MODE, RKLLAMA_BASE_URL,
    XAI_API_KEY, PIXEL_SYSTEM_PROMPT,
)


# ── Ollama ────────────────────────────────────────────────

def _ollama_chat(messages: list) -> str:
    import ollama
    client = ollama.Client(host=OLLAMA_HOST)
    response = client.chat(model=OLLAMA_MODEL, messages=messages)
    return response["message"]["content"].strip()


# ── RKLLAMA（Orange Pi 5 NPU）────────────────────────────

def _rkllama_chat(messages: list) -> str:
    import httpx
    payload = {"model": OLLAMA_MODEL, "messages": messages, "stream": False}
    resp = httpx.post(f"{RKLLAMA_BASE_URL}/api/chat", json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()


# ── Cloud fallback（xAI Grok）────────────────────────────

def _cloud_chat(messages: list) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")
    response = client.chat.completions.create(
        model="grok-3-mini-fast",
        messages=messages,
        max_tokens=512,
    )
    return response.choices[0].message.content.strip()


# ── 统一入口 ──────────────────────────────────────────────

def _call(messages: list) -> str:
    """根据 RUNTIME_MODE 选择引擎，失败时自动降级。"""
    try:
        if RUNTIME_MODE == "rkllama":
            return _rkllama_chat(messages)
        elif RUNTIME_MODE == "cloud":
            return _cloud_chat(messages)
        else:
            return _ollama_chat(messages)  # 默认 ollama
    except Exception as e:
        print(f"[ai] {RUNTIME_MODE} 失败: {e}")
        if XAI_API_KEY and RUNTIME_MODE != "cloud":
            print("[ai] 降级到 xAI Cloud...")
            return _cloud_chat(messages)
        raise


def chat(message: str, history: list[dict] | None = None) -> str:
    """
    普通对话，返回 Pixel 回复文字。
    history: [{"role": "user"|"assistant", "content": "..."}]
    """
    messages = [{"role": "system", "content": PIXEL_SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-10:])
    messages.append({"role": "user", "content": message})
    print(f"[ai] [{RUNTIME_MODE}] 请求中...")
    reply = _call(messages)
    print(f"[ai] 回复: {reply!r}")
    return reply


def translate(text: str, source_lang: str) -> tuple[str, str]:
    """
    翻译。zh → no，no/en → zh。
    返回 (translated_text, target_lang)。
    """
    if source_lang == "zh":
        target_lang = "no"
        instruction = f"请把以下中文翻译成挪威语，只输出翻译结果：\n{text}"
    else:
        target_lang = "zh"
        instruction = f"Please translate the following to Chinese, output only the translation:\n{text}"

    messages = [
        {"role": "system", "content": "You are a professional translator. Output only the translation."},
        {"role": "user", "content": instruction},
    ]
    result = _call(messages)
    print(f"[ai] 翻译 [{source_lang}→{target_lang}]: {result!r}")
    return result, target_lang
