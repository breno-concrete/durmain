import queue
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import pyaudiowpatch as pyaudio
from audio_convert import to_whisper_format
from faster_whisper import WhisperModel
from minutes import gerar_ata
from name_detector import NAME, menciona_nome
from overlay import Overlay

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
        fila.put((time.perf_counter(), b"".join(chunk)))
        chunk.clear()
        frames_no_bloco = 0
    return (None, pyaudio.paContinue)


def eh_alucinacao(segment):
    if segment.no_speech_prob > 0.6 and segment.avg_logprob < -1:
        return True
    texto = segment.text.lower()
    return any(frase in texto for frase in FRASES_FANTASMA)


def transcrever(rate, channels):
    # últimas frases ditas, mostradas como contexto quando o nome aparece
    contexto = deque(maxlen=3)
    # fica aberto a sessão toda; sem close() porque a thread daemon morre no Ctrl+C,
    # por isso o flush() a cada frase
    arquivo = open(caminho_transcript, "a", encoding="utf-8")
    while True:
        fechou_em, audio = fila.get()
        audio_whisper = to_whisper_format(audio, rate, channels)
        segments, info = model.transcribe(audio_whisper, language="pt", vad_filter=True, hotwords=NAME)
        for segment in segments:
            if not eh_alucinacao(segment):
                print(segment.text)

                arquivo.write(segment.text.strip() + "\n")
                arquivo.flush()

                contexto.append(segment.text)
                if menciona_nome(segment.text):
                    print("Mencionaram seu nome!!!")
                    print(" ".join(contexto))
                    overlay.acordar()

        # pior caso: fala no início do bloco esperou os 5 s do bloco + o processamento
        processamento = time.perf_counter() - fechou_em
        print(f"   [processou em {processamento:.2f} s | atraso máx {5 + processamento:.2f} s | fila {fila.qsize()}]")


# output/ da raiz do projeto, para funcionar rodando de qualquer pasta
pasta_saida = Path(__file__).resolve().parent.parent / "output"
pasta_saida.mkdir(exist_ok=True)
carimbo = datetime.now().strftime("%Y-%m-%d-%H%M")
caminho_transcript = pasta_saida / f"transcript-{carimbo}.txt"

model = WhisperModel(model_size, device="cpu", compute_type="int8")
# criado antes da thread de transcrição, que chama overlay.acordar()
overlay = Overlay()

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
        # a janela ocupa a thread principal (armadilha 5); fecha com Ctrl+C ou botão direito
        overlay.rodar()
        print("encerrando...")
    finally:
        stream.stop_stream(); stream.close()

# o LLM só roda depois que a captura parou, nunca junto com a transcrição
if caminho_transcript.stat().st_size > 0:
    print("gerando a ata...")
    try:
        gerar_ata(caminho_transcript)
    except Exception as erro:
        # o transcript já está salvo; dá para gerar a ata depois
        print(f"falhou ao gerar a ata ({erro})")
        print(f"rode: python src/minutes.py {caminho_transcript}")
else:
    print("transcript vazio, sem ata")
