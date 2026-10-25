import pyaudiowpatch as pyaudio

CHUNK = 1024
data_format = pyaudio.paInt16


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
            print(len(audio))

    except KeyboardInterrupt:
        print("encerrando...")
    finally:
        stream.stop_stream(); stream.close()