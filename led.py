"""
LED 控制
RPi5 上用 RPi.GPIO；Mac 开发模式打印状态。
"""

from config import IS_RPI, LED_IDLE_PIN, LED_REC_PIN, LED_THINK_PIN, LED_SPEAK_PIN

_gpio = None

def _get_gpio():
    global _gpio
    if _gpio is None and IS_RPI:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in [LED_IDLE_PIN, LED_REC_PIN, LED_THINK_PIN, LED_SPEAK_PIN]:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
        _gpio = GPIO
    return _gpio

def _all_off():
    gpio = _get_gpio()
    if gpio:
        for pin in [LED_IDLE_PIN, LED_REC_PIN, LED_THINK_PIN, LED_SPEAK_PIN]:
            gpio.output(pin, gpio.LOW)

def set_idle():
    _all_off()
    gpio = _get_gpio()
    if gpio:
        gpio.output(LED_IDLE_PIN, gpio.HIGH)
    else:
        print("[LED] 🟢 idle")

def set_recording():
    _all_off()
    gpio = _get_gpio()
    if gpio:
        gpio.output(LED_REC_PIN, gpio.HIGH)
    else:
        print("[LED] 🔴 recording")

def set_thinking():
    _all_off()
    gpio = _get_gpio()
    if gpio:
        gpio.output(LED_THINK_PIN, gpio.HIGH)
    else:
        print("[LED] 🔵 thinking")

def set_speaking():
    _all_off()
    gpio = _get_gpio()
    if gpio:
        gpio.output(LED_SPEAK_PIN, gpio.HIGH)
    else:
        print("[LED] 🟡 speaking")

def cleanup():
    gpio = _get_gpio()
    if gpio:
        gpio.cleanup()
