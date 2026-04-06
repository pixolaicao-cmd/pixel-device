"""
Pixel 设备配置
支持 RPi5 / Orange Pi 5 / Mac（开发/测试）
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── 运行环境 ─────────────────────────────────────────────
IS_RPI = os.path.exists("/proc/device-tree/model")  # 只有真实 RPi 才有
DEV_MODE = not IS_RPI  # Mac 上开发模式，跳过 GPIO

# ── Ollama / AI ──────────────────────────────────────────
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e2b")

PIXEL_SYSTEM_PROMPT = """你是 Pixel，一个挂脖式 AI 智能伙伴。
性格友好、有温度，说话简洁自然。
支持中文、挪威语和英文，根据用户语言自动切换。
回复控制在 1-2 句话以内，因为要转成语音播放。"""

# ── STT (Whisper local) ──────────────────────────────────
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")   # tiny/base/small/medium
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE = "int8"   # ARM 上用 int8 最快

# ── TTS (Edge TTS) ───────────────────────────────────────
TTS_VOICES = {
    "zh": "zh-CN-XiaoxiaoNeural",
    "no": "nb-NO-PernilleNeural",
    "en": "en-US-AriaNeural",
}
TTS_RATE = "+0%"
TTS_VOLUME = "+0%"

# ── 音频设置 ─────────────────────────────────────────────
SAMPLE_RATE = 16000
CHANNELS = 1
RECORD_DTYPE = "float32"
SILENCE_THRESHOLD = 0.015   # RMS 低于此值视为静音
SILENCE_DURATION = 1.5      # 静音超过此秒数自动停止录音
MAX_RECORD_SECONDS = 30     # 最大录音时长

# ── 翻译模式触发词 ───────────────────────────────────────
TRANSLATE_ON_WORDS  = ["翻译模式开启", "translation mode on", "oversettelsesmodus på"]
TRANSLATE_OFF_WORDS = ["翻译模式关闭", "translation mode off", "oversettelsesmodus av"]

# ── Supabase 云同步（可选）──────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
PIXEL_USER_ID = os.getenv("PIXEL_USER_ID", "")   # 绑定的用户 UUID

# ── GPIO 引脚（RPi5）───────────────────────────────────
BTN_PIN = 17       # 录音按钮 (BCM)
LED_IDLE_PIN = 27  # 绿灯：空闲
LED_REC_PIN = 22   # 红灯：录音中
LED_THINK_PIN = 23 # 蓝灯：AI 思考中
LED_SPEAK_PIN = 24 # 黄灯：播放中
