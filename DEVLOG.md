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

## 2026-10-24 — Marco 2
- Feito: `src/transcribe.py` transcreve o `teste.wav` com faster-whisper (`small`, CPU, `int8`, `language="pt"`, `vad_filter=True`); texto em português legível, idioma detectado como `pt` com probabilidade 1.0. Aceite ok.
- Travou em: `TypeError: open() got an unexpected keyword argument 'metadata_errors'`. Causa: faster-whisper 1.2.1 só exige `av>=11`, o pip instalou o PyAV 19.0.2, que removeu esse parâmetro. Solução: `pip install "av<19"` (18.1.0) e `av<19` fixado no requirements.txt. Também errei nomes de variável (`segements`) → `NameError`.
- Aprendi: `segments` é um generator (lazy, ≈ Stream do Java): o trabalho pesado só acontece dentro do `for`, então o cronômetro tem que parar depois dele. Medir carregamento do modelo separado da transcrição, porque o modelo carrega uma vez só. Passando o caminho do arquivo, o faster-whisper converte sozinho 48 kHz estéreo → 16 kHz mono (via PyAV); isso deixa de valer quando eu passar bytes da memória (Marco 3).
- Números medidos: carregar modelo = 1,47 s; transcrever 30 s de áudio = 4,42 s → fator de tempo real ≈ 0,15 (~6,8× mais rápido que o áudio).
- Próximo passo: Marco 3 — capturar em blocos de ~5 s e transcrever cada bloco enquanto o próximo é gravado (threads + fila), convertendo o áudio pra 16 kHz mono na mão.
