import queue
import threading
import time

import pyaudiowpatch as pyaudio
from audio_convert import to_whisper_format
from faster_whisper import WhisperModel

CHUNK = 1024
data_format = pyaudio.paInt16
model_size = "small"

# frases que o Whisper inventa no silêncio (vêm de legendas da internet)
FRASES_FANTASMA = ["amara.org", "legendas pela comunidade"]

fila = queue.Queue()
chunk = []
frames_no_bloco = 0


def ao_receber_audio(in_data, frame_count, time_info, status):
    # chamado pelo PortAudio numa thread dele a cada ~CHUNK frames; só junta e entrega
    global frames_no_bloco
    chunk.append(in_data)
    frames_no_bloco += frame_count
    if frames_no_bloco >= total_frames:
        fila.put(b"".join(chunk))
        chunk.clear()
        frames_no_bloco = 0
    return (None, pyaudio.paContinue)


def eh_alucinacao(segment):
    if segment.no_speech_prob > 0.6 and segment.avg_logprob < -1:
        return True
    texto = segment.text.lower()
    return any(frase in texto for frase in FRASES_FANTASMA)


def transcrever(rate, channels):
    while True:
        audio = fila.get()
        audio_whisper = to_whisper_format(audio, rate, channels)
        segments, info = model.transcribe(audio_whisper, language="pt", vad_filter=True)
        for segment in segments:
            if not eh_alucinacao(segment):
                print(segment.text)


model = WhisperModel(model_size, device="cpu", compute_type="int8")

with pyaudio.PyAudio() as p:
    default_speakers = p.get_default_wasapi_loopback()
    rate = int(default_speakers["defaultSampleRate"])
    channels = default_speakers["maxInputChannels"]
    total_frames = rate * 5

    transcritor = threading.Thread(target=transcrever, args=(rate, channels), daemon=True)
    transcritor.start()

    # modo callback: o read() bloqueante travava no silêncio e ignorava o Ctrl+C
    stream = p.open(
                    format=data_format,
                    channels=channels,
                    rate=rate,
                    input=True,
                    input_device_index=int(default_speakers["index"]),
                    frames_per_buffer=CHUNK,
                    stream_callback=ao_receber_audio
                )

    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("encerrando...")
    finally:
        stream.stop_stream(); stream.close()
