# DEVLOG — SlothNotes

## 2026-10-23 — Marco 0
- Feito: venv criado; faster-whisper, pyaudiowpatch, rapidfuzz e jiwer instalados via requirements.txt; ffmpeg 9.0.2 via winget; Ollama com qwen2.5:7b. Testes de aceite passaram.
- Travou em: `ffmpeg` não reconhecido depois de instalar. Causa: o terminal integrado da IDE herda o PATH de quando a IDE abriu; foi preciso fechar a IDE inteira.
- Aprendi: venv isola as libs por projeto (≈ pom.xml + .m2 próprio); o Ollama é um servidor local (localhost:11434) e o comando `ollama` é só cliente; `qwen2.5vl` ≠ `qwen2.5` (VL = visão, mais pesado e desnecessário aqui).
- Números medidos: máquina com 15,7 GB de RAM; Python 3.13.7; qwen2.5:7b ocupa ~4,7 GB.
- Próximo passo: Marco 1 — capturar 30 s do áudio do PC via WASAPI loopback e salvar em .wav.

