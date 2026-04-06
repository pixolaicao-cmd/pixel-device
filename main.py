"""
Pixel 设备主程序
适用于：Raspberry Pi 5 / Orange Pi 5 / Mac（开发测试）

状态机：
  IDLE → RECORDING → TRANSCRIBING → THINKING → SPEAKING → IDLE

录音触发方式（二选一）：
  - 物理按钮（RPi5 GPIO）：按下开始，松开停止
  - VAD 自动检测（开发/无按钮模式）：检测到说话自动开始，静音自动停止

翻译模式：
  说 "翻译模式开启" 进入，"翻译模式关闭" 退出
  进入后每句话自动翻译 zh↔no/en
"""

import sys
import signal
import threading
import time

import led
import audio
import stt
import tts
import ai
import sync
from config import (
    IS_RPI, DEV_MODE,
    BTN_PIN,
    TRANSLATE_ON_WORDS, TRANSLATE_OFF_WORDS,
    PIXEL_USER_ID,
)


# ── 全局状态 ──────────────────────────────────────────────
translate_mode = False
conversation_history: list[dict] = []
memories: list[str] = []


def inject_memories_to_prompt() -> str:
    """把 memories 注入 system prompt。"""
    if not memories:
        return ai.PIXEL_SYSTEM_PROMPT if hasattr(ai, "PIXEL_SYSTEM_PROMPT") else ""
    from config import PIXEL_SYSTEM_PROMPT
    mem_text = "\n".join(f"- {m}" for m in memories[:5])
    return PIXEL_SYSTEM_PROMPT + f"\n\n【关于用户你记得的事情】\n{mem_text}"


# ── 核心流程 ──────────────────────────────────────────────

def handle_recording(wav_bytes: bytes):
    """录音完成后的完整处理流程。"""
    global translate_mode, conversation_history

    if not wav_bytes:
        print("[main] 没有录到声音，跳过")
        led.set_idle()
        return

    # 1. STT
    led.set_thinking()
    print("[main] 转写中...")
    text, lang = stt.transcribe(wav_bytes)
    if not text.strip():
        print("[main] 转写结果为空，跳过")
        led.set_idle()
        return

    print(f"[main] 用户说 [{lang}]: {text}")
    sync.save_message("user", text)

    # 2. 检测翻译模式切换
    text_lower = text.lower()
    if any(w in text_lower for w in TRANSLATE_ON_WORDS):
        translate_mode = True
        reply = "翻译模式已开启。" if lang == "zh" else "Translation mode on."
        _speak_reply(reply, lang)
        return
    if any(w in text_lower for w in TRANSLATE_OFF_WORDS):
        translate_mode = False
        reply = "翻译模式已关闭。" if lang == "zh" else "Translation mode off."
        _speak_reply(reply, lang)
        return

    # 3. 翻译模式
    if translate_mode:
        translated, target_lang = ai.translate(text, lang)
        _speak_reply(translated, target_lang)
        return

    # 4. 普通对话
    print("[main] AI 思考中...")
    reply = ai.chat(text, history=conversation_history)

    # 更新对话历史
    conversation_history.append({"role": "user", "content": text})
    conversation_history.append({"role": "assistant", "content": reply})
    if len(conversation_history) > 20:
        conversation_history = conversation_history[-20:]

    sync.save_message("pixel", reply)
    _speak_reply(reply, lang)


def _speak_reply(text: str, lang: str):
    """TTS 播放回复。"""
    led.set_speaking()
    print(f"[main] Pixel 说 [{lang}]: {text}")
    try:
        tts.speak_and_play(text, lang)
    except Exception as e:
        print(f"[main] TTS 失败: {e}")
    led.set_idle()


# ── 按钮模式（RPi5 GPIO）────────────────────────────────

def _setup_button_mode():
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BTN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    stop_event = threading.Event()

    def btn_pressed(channel):
        nonlocal stop_event
        print("[main] 按钮按下，开始录音")
        led.set_recording()
        stop_event = threading.Event()
        wav = audio.record_while_held(stop_event)
        handle_recording(wav)

    def btn_released(channel):
        stop_event.set()
        print("[main] 按钮松开，停止录音")

    GPIO.add_event_detect(BTN_PIN, GPIO.FALLING, callback=btn_pressed, bouncetime=200)
    GPIO.add_event_detect(BTN_PIN, GPIO.RISING,  callback=btn_released, bouncetime=200)
    print("[main] 按钮模式就绪，按住录音按钮开始说话")


# ── VAD 模式（开发/无按钮）──────────────────────────────

def _run_vad_loop():
    print("[main] VAD 模式：检测到说话自动录音")
    while True:
        try:
            led.set_idle()
            wav = audio.record_until_silence()
            if wav:
                handle_recording(wav)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[main] 循环错误: {e}")
            time.sleep(1)


# ── 主入口 ───────────────────────────────────────────────

def main():
    global memories

    print("=" * 50)
    print("  Pixel AI 设备启动")
    print(f"  模型: {ai.OLLAMA_MODEL}" if hasattr(ai, "OLLAMA_MODEL") else "")
    print(f"  平台: {'Raspberry Pi' if IS_RPI else 'Mac (开发模式)'}")
    print("=" * 50)

    # 加载 memories
    if PIXEL_USER_ID:
        memories = sync.get_memories()

    led.set_idle()

    def _shutdown(sig, frame):
        print("\n[main] 关闭中...")
        led.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    if IS_RPI:
        _setup_button_mode()
        # 主线程保持运行
        while True:
            time.sleep(1)
    else:
        # 开发模式：VAD 自动检测
        _run_vad_loop()


if __name__ == "__main__":
    main()
