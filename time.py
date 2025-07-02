import numpy as np
import pyaudio
import datetime
import time

SAMPLE_RATE = 44100
FREQ = 1000  # 1kHz 脉冲频率
AMPLITUDE = 16000

def generate_tone(duration):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    tone = AMPLITUDE * np.sin(2 * np.pi * FREQ * t)
    return tone.astype(np.int16)

def pulse_for_bit(bit):
    # 每秒1位：bit=0 -> 200ms音频 + 800ms静音
    #         bit=1 -> 500ms音频 + 500ms静音
    if bit == 0:
        pulse = generate_tone(0.2)
        silence = np.zeros(int(SAMPLE_RATE * 0.8), dtype=np.int16)
    else:
        pulse = generate_tone(0.5)
        silence = np.zeros(int(SAMPLE_RATE * 0.5), dtype=np.int16)
    return np.concatenate((pulse, silence))

def bcd_bits(value, bits_count=8):
    # 输出BCD格式的 bits_count 位，默认8位（高4位 + 低4位）
    tens = value // 10
    ones = value % 10
    bits = []
    for i in range(3, -1, -1):
        bits.append((tens >> i) & 1)
    for i in range(3, -1, -1):
        bits.append((ones >> i) & 1)
    return bits[:bits_count]

def encode_bpm_time(dt):
    bits = []

    # bit 0：起始秒标志（第0秒）—— 长脉冲
    bits.append(1)

    # bit 1–4：年份的十位（如2025 → '20'）
    bits += bcd_bits(dt.year // 100, 4)
    # bit 5–8：年份的个位（25）
    bits += bcd_bits(dt.year % 100, 4)
    # bit 9–12：月份
    bits += bcd_bits(dt.month, 4)
    # bit 13–17：日（5位）
    bits += bcd_bits(dt.day, 5)
    # bit 18–20：星期（3位，周一=1，周日=7）
    weekday = dt.isoweekday()
    bits += [(weekday >> 2) & 1, (weekday >> 1) & 1, weekday & 1]
    # bit 21–28：小时（8位BCD）
    bits += bcd_bits(dt.hour, 8)
    # bit 29–36：分钟（8位BCD）
    bits += bcd_bits(dt.minute, 8)
    # bit 37–44：秒钟（8位BCD）
    bits += bcd_bits(dt.second, 8)
    # bit 45–53：保留位/校验位（可选，先填0）
    bits += [0] * 9
    # bit 54–58：夏令时/闰秒/备用标志位（先填0）
    bits += [0] * 5
    # bit 59：结尾空秒（静音1秒）
    bits.append(0)

    return bits

def generate_bpm_signal(bits):
    signal = np.array([], dtype=np.int16)
    for i, bit in enumerate(bits):
        if i == 0:
            # 起始位：1秒音频
            signal = np.concatenate((signal, generate_tone(1.0)))
        elif i == 59:
            # 最后一位：静音1秒
            signal = np.concatenate((signal, np.zeros(int(SAMPLE_RATE * 1.0), dtype=np.int16)))
        else:
            signal = np.concatenate((signal, pulse_for_bit(bit)))
    return signal

def play_bpm():
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE, output=True)

    print("开始播放 BPM 授时信号（每分钟同步），Ctrl+C 停止")

    try:
        while True:
            now = datetime.datetime.now()
            bits = encode_bpm_time(now)
            signal = generate_bpm_signal(bits)
            stream.write(signal.tobytes())

            # 同步到下一个整分钟
            now2 = datetime.datetime.now()
            wait_time = 60 - now2.second - now2.microsecond / 1_000_000
            if wait_time > 0:
                time.sleep(wait_time)
    except KeyboardInterrupt:
        print("用户中断，停止播放。")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    play_bpm()
