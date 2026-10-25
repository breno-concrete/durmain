from faster_whisper import WhisperModel
import time

inicio_modelo = time.perf_counter()
#como marca tempo? rs

model_size = "small"

model = WhisperModel(model_size, device="cpu", compute_type="int8")

print(f"levou {time.perf_counter() - inicio_modelo:.2f} s para carregar o modelo")
#como marca? rs

inicio_transcricao = time.perf_counter()

segments, info = model.transcribe("teste.wav", language="pt", vad_filter=True)

print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

print(f"levou {time.perf_counter() - inicio_transcricao:.2f} s para transcrever")