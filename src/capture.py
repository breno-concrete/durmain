import pyaudiowpatch as pyaudio
import wave

data_format = pyaudio.paInt16

CHUNK = 1024

with pyaudio.PyAudio() as p:

        try:
            default_speakers = p.get_default_wasapi_loopback()
            total_leituras = int(int(default_speakers["defaultSampleRate"]) * 30 / CHUNK)
            print(total_leituras)

            print(default_speakers)

            stream = p.open(
                format=data_format,
                channels=default_speakers["maxInputChannels"],
                rate= int(default_speakers["defaultSampleRate"]),
                input=True,
                input_device_index=int(default_speakers["index"]),
                frames_per_buffer=CHUNK      
            )

            chunk = []
            for _ in range(total_leituras):
                chunk.append(stream.read(CHUNK))

            stream.stop_stream()
            stream.close()

            audio = b"".join(chunk)

            with wave.open("teste.wav", "wb") as f:
                f.setnchannels(default_speakers["maxInputChannels"])
                f.setframerate(int(default_speakers["defaultSampleRate"]))
                f.setsampwidth(p.get_sample_size(data_format))
                f.writeframes(audio)
            
            


            print(len(audio))

        except OSError:
            print("Looks like WASAPI is not available on the system. Exiting...")
            
