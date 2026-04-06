"""
语音转文字 (STT)
使用 faster-whisper 本地模型，ARM CPU int8 量化。
支持中文 / 挪威语 / 英文自动检测。
"""

from __future__ import annotations
from config import WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        print(f"[stt] 加载 Whisper {WHISPER_MODEL} 模型...")
        _model = WhisperModel(
            WHISPER_MODEL,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE,
        )
        print("[stt] 模型已就绪")
    return _model


def transcribe(wav_bytes: bytes) -> tuple[str, str]:
    """
    转写 WAV bytes，返回 (text, language)。
    language 为 ISO 639-1 代码，如 "zh", "no", "en"。
    """
    import io
    import tempfile
    import os

    # faster-whisper 需要文件路径
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav_bytes)
        tmp_path = f.name

    try:
        model = _get_model()
        segments, info = model.transcribe(
            tmp_path,
            beam_size=5,
            language=None,       # 自动检测语言
            vad_filter=True,     # 过滤静音段
            vad_parameters=dict(min_silence_duration_ms=300),
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        lang = info.language or "zh"
        # 挪威语检测：faster-whisper 返回 "no" 或 "nn"
        if lang in ("nn", "nb"):
            lang = "no"
        print(f"[stt] 识别结果: [{lang}] {text!r}")
        return text, lang
    finally:
        os.unlink(tmp_path)
