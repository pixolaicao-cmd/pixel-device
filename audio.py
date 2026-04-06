"""
音频录制与播放
- 录制：sounddevice VAD（静音自动停止）
- 播放：soundfile + sounddevice
"""

import io
import tempfile
import threading
import numpy as np
import sounddevice as sd
import soundfile as sf

from config import (
    SAMPLE_RATE, CHANNELS, RECORD_DTYPE,
    SILENCE_THRESHOLD, SILENCE_DURATION, MAX_RECORD_SECONDS,
)


def record_until_silence() -> bytes:
    """
    录音直到用户停止说话（VAD 静音检测）。
    返回 WAV 格式 bytes。
    """
    print("[audio] 开始录音，请说话...")
    frames = []
    silence_frames = 0
    silence_limit = int(SAMPLE_RATE * SILENCE_DURATION / 512)  # 每块 512 帧
    max_frames = int(SAMPLE_RATE * MAX_RECORD_SECONDS / 512)
    speaking_started = False

    def callback(indata, frame_count, time_info, status):
        nonlocal silence_frames, speaking_started
        frames.append(indata.copy())
        rms = float(np.sqrt(np.mean(indata ** 2)))
        if rms > SILENCE_THRESHOLD:
            speaking_started = True
            silence_frames = 0
        elif speaking_started:
            silence_frames += 1

    stop_event = threading.Event()

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=RECORD_DTYPE,
        blocksize=512,
        callback=callback,
    ):
        while not stop_event.is_set():
            sd.sleep(50)
            if speaking_started and silence_frames >= silence_limit:
                break
            if len(frames) >= max_frames:
                break

    if not frames:
        return b""

    audio_data = np.concatenate(frames, axis=0)
    buf = io.BytesIO()
    sf.write(buf, audio_data, SAMPLE_RATE, format="WAV", subtype="PCM_16")
    buf.seek(0)
    print(f"[audio] 录音完成，时长 {len(audio_data)/SAMPLE_RATE:.1f}s")
    return buf.read()


def record_while_held(stop_event: threading.Event) -> bytes:
    """
    按住按钮期间录音（用于物理按钮模式）。
    stop_event.set() 时停止。
    返回 WAV bytes。
    """
    frames = []

    def callback(indata, frame_count, time_info, status):
        frames.append(indata.copy())

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=RECORD_DTYPE,
        blocksize=512,
        callback=callback,
    ):
        while not stop_event.is_set():
            sd.sleep(50)

    if not frames:
        return b""

    audio_data = np.concatenate(frames, axis=0)
    buf = io.BytesIO()
    sf.write(buf, audio_data, SAMPLE_RATE, format="WAV", subtype="PCM_16")
    buf.seek(0)
    return buf.read()


def play_wav_bytes(wav_bytes: bytes):
    """播放 WAV bytes。"""
    buf = io.BytesIO(wav_bytes)
    data, sr = sf.read(buf, dtype="float32")
    sd.play(data, sr)
    sd.wait()


def play_file(path: str):
    """播放音频文件。"""
    data, sr = sf.read(path, dtype="float32")
    sd.play(data, sr)
    sd.wait()
