# DEVLOG — SlothNotes

## 2026-10-23 — Marco 0
- Feito: venv criado; faster-whisper, pyaudiowpatch, rapidfuzz e jiwer instalados via requirements.txt; ffmpeg 9.0.2 via winget; Ollama com qwen2.5:7b. Testes de aceite passaram.
- Travou em: `ffmpeg` não reconhecido depois de instalar. Causa: o terminal integrado da IDE herda o PATH de quando a IDE abriu; foi preciso fechar a IDE inteira.
- Aprendi: venv isola as libs por projeto (≈ pom.xml + .m2 próprio); o Ollama é um servidor local (localhost:11434) e o comando `ollama` é só cliente; `qwen2.5vl` ≠ `qwen2.5` (VL = visão, mais pesado e desnecessário aqui).
- Números medidos: máquina com 15,7 GB de RAM; Python 3.13.7; qwen2.5:7b ocupa ~4,7 GB.
- Próximo passo: Marco 1 — capturar 30 s do áudio do PC via WASAPI loopback e salvar em .wav.

## 2026-10-24 — Marco 1
- Feito: captura de 30 s do áudio do PC via WASAPI loopback (pyaudiowpatch) salva em `teste.wav` com o módulo `wave`; o arquivo tocou o áudio do YouTube. Aceite ok.
- Travou em: usar o `wave` — passei os bytes no lugar do nome do arquivo, abri com `'rb'` em vez de `'wb'`, usei `setnframes(CHUNK)` achando que era necessário e passei `paInt16` direto pro `setsampwidth` (é uma constante interna = 8, não o tamanho em bytes).
- Aprendi: um .wav é cabeçalho + bytes crus; o cabeçalho precisa de channels, sample width (em bytes) e frame rate pro player interpretar os bytes. `p.get_sample_size(paInt16)` = 2 bytes. O `wave` conta os frames sozinho e corrige o cabeçalho no fechamento. `with` em Python ≈ try-with-resources do Java.
- Números medidos: loopback "Fones de ouvido (Lenovo thinkplus XT62)" em 48000 Hz, 2 canais (estéreo), 16 bits; 30 s = 1406 leituras de 1024 frames (≈ 29,99 s); 5.758.976 bytes de áudio → `teste.wav` com 5.759.020 bytes (os 44 a mais são o cabeçalho).
- Próximo passo: Marco 2 — transcrever o `teste.wav` com faster-whisper e medir o tempo. Atenção: o áudio está em 48 kHz estéreo e o Whisper espera 16 kHz mono (armadilha 2).

