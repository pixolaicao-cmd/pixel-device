"""
文字转语音 (TTS)
使用 edge-tts（微软神经语音，免费）。
支持中文 / 挪威语 / 英文。
"""

from __future__ import annotations
import asyncio
import io
import tempfile
import os

from config import TTS_VOICES, TTS_RATE, TTS_VOLUME


def detect_lang(text: str) -> str:
    """简单语言检测。"""
    if any("\u4e00" <= c <= "\u9fff" for c in text):
        return "zh"
    # 挪威语特征字符
    if any(c in text for c in "æøåÆØÅ"):
        return "no"
    return "en"


async def _synthesize(text: str, lang: str) -> bytes:
    """异步合成 TTS，返回 MP3 bytes。"""
    import edge_tts
    voice = TTS_VOICES.get(lang, TTS_VOICES["en"])
    communicate = edge_tts.Communicate(text, voice, rate=TTS_RATE, volume=TTS_VOLUME)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    buf.seek(0)
    return buf.read()


def speak(text: str, lang: str | None = None) -> bytes:
    """
    合成语音并返回 MP3 bytes。
    lang 为 None 时自动检测。
    """
    if not text.strip():
        return b""
    if lang is None:
        lang = detect_lang(text)
    mp3_bytes = asyncio.run(_synthesize(text, lang))
    print(f"[tts] 合成完成 [{lang}] {len(mp3_bytes)} bytes")
    return mp3_bytes


def speak_and_play(text: str, lang: str | None = None):
    """合成并立即播放。"""
    import soundfile as sf
    import sounddevice as sd
    import pydub
    from pydub import AudioSegment

    mp3_bytes = speak(text, lang)
    if not mp3_bytes:
        return

    # MP3 → WAV in memory
    audio = AudioSegment.from_mp3(io.BytesIO(mp3_bytes))
    wav_buf = io.BytesIO()
    audio.export(wav_buf, format="wav")
    wav_buf.seek(0)

    data, sr = sf.read(wav_buf, dtype="float32")
    sd.play(data, sr)
    sd.wait()
