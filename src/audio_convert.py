import numpy as np

WHISPER_RATE = 16000


def to_whisper_format(audio_bytes, rate, channels):
    samples = np.frombuffer(audio_bytes, dtype=np.int16)
    samples = samples.astype(np.float32) / 32768.0

    mono = samples.reshape(-1, channels).mean(axis=1)

    if rate == WHISPER_RATE:
        return mono

    total_saida = int(len(mono) * WHISPER_RATE / rate)
    posicoes_novas = np.linspace(0, len(mono) - 1, total_saida)
    return np.interp(posicoes_novas, np.arange(len(mono)), mono).astype(np.float32)
