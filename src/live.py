import pyaudiowpatch as pyaudio
from audio_convert import to_whisper_format
from faster_whisper import WhisperModel

CHUNK = 1024
data_format = pyaudio.paInt16
model_size = "small"


model = WhisperModel(model_size, device="cpu", compute_type="int8")

with pyaudio.PyAudio() as p:
    default_speakers = p.get_default_wasapi_loopback()
    total_leituras = int(int(default_speakers["defaultSampleRate"]) * 5 / CHUNK)
    stream = p.open(
                    format=data_format,
                    channels=default_speakers["maxInputChannels"],
                    rate= int(default_speakers["defaultSampleRate"]),
                    input=True,
                    input_device_index=int(default_speakers["index"]),
                    frames_per_buffer=CHUNK
                )
    try:
        while True:
            chunk = []
            for _ in range(total_leituras):
                chunk.append(stream.read(CHUNK))

            audio = b"".join(chunk)
            audio_whisper = to_whisper_format(
                audio,
                int(default_speakers["defaultSampleRate"]),
                default_speakers["maxInputChannels"],
            )
            segments, info = model.transcribe(audio_whisper, language="pt", vad_filter=True)
            for segment in segments:
                print(segment.text)

    except KeyboardInterrupt:
        print("encerrando...")
    finally:
        stream.stop_stream(); stream.close()