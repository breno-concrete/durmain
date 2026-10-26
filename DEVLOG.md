# DEVLOG — Durmain

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

## 2026-10-24 — Marco 3
- Feito: `src/live.py` grava o loopback em blocos de 5 s e transcreve cada bloco numa thread separada (fila entre as duas); `src/audio_convert.py` converte int16 48 kHz estéreo → float32 16 kHz mono (numpy). Filtro de alucinação por confiança (`no_speech_prob > 0.6` e `avg_logprob < -1`) + lista de frases fantasma. Aceite ok.
- Travou em:
  - `join`/`print` indentados dentro do `for` → imprimia o bloco crescendo a cada leitura.
  - Passei a lista `chunk` pro `transcribe` em vez do array convertido, e não percorri os `segments` (generator) → nada era transcrito.
  - Alucinação "Legendas pela comunidade de Amara.org" ao pausar o vídeo, mesmo com `vad_filter=True`.
  - **WASAPI loopback não entrega frames quando nada está tocando**: o `stream.read()` bloqueia dentro do C e o Ctrl+C é ignorado. Mover o `read` pra outra thread fez o Ctrl+C funcionar, mas o `p.terminate()` com a thread ainda no `read` deu **segmentation fault**. Solução: modo callback (`stream_callback`) — o PortAudio chama a função quando tem áudio, ninguém fica preso e o stream fecha limpo.
- Aprendi: produtor/consumidor com `queue.Queue` + `threading.Thread(daemon=True)` ≈ `BlockingQueue` + `Thread` do Java. Callback (listener) × read bloqueante (polling). `global` só é necessário pra reatribuir; `append`/`clear` modificam a lista sem ele. Python só trata Ctrl+C entre instruções Python, não dentro de código C.
- Números medidos: 38 blocos de 5 s com fala (~3 min de palestra pública do YouTube): processamento médio 1,68 s (mín 1,49, máx 2,33) → atraso máx médio 6,68 s, pior caso 7,33 s; fila sempre 0. Fator de tempo real em bloco de 5 s ≈ 0,34 (contra 0,15 com 30 s de uma vez — custo fixo por chamada). Silêncio: 0 frases inventadas.
- Limitação conhecida: sem sobreposição entre blocos, palavras na borda são cortadas ("mochila p..." / "pronta") — cortado pelo prazo.
- Próximo passo: Marco 4 — detectar o nome com rapidfuzz e imprimir alerta com as últimas 2–3 frases de contexto.

## 2026-10-25 — Marco 4
- Feito: `src/name_detector.py` com rapidfuzz (limiar 85, comparação palavra a palavra em minúsculo) e alerta no `live.py` com as últimas frases de contexto. `hotwords="Breno"` no transcribe. Aceite ok.
- Travou em: o detector funcionava, mas o Whisper escrevia o nome errado ("Brenna", "Brena", "Bruno", "branco", "Brennan"). Baixar o limiar pra 80 pegaria "Bruno"/"Brena", mas faria as pegadinhas com "Bruno" virarem alarme falso.
- Aprendi: o Whisper funciona como um autocomplete; com som ambíguo ele escolhe a palavra mais comum no treino. `hotwords` desempata a favor do nome sem mexer no detector. Risco: puxar outros nomes pra "Breno" ou inventar o nome no silêncio — não aconteceu no teste.
- Números medidos: roteiro com 20 "Breno" + 6 pegadinhas, mesma gravação nas duas rodadas. Sem hotwords: 15/20, 0 alarmes falsos. Com hotwords: 16/20, 0 alarmes falsos (5 pegadinhas observáveis; a 24 sumiu). Latência ~6,8 s.
- Limitação conhecida: 3 das 4 falhas com hotwords foram frases que não chegaram ao detector (borda de bloco ou filtro de confiança), não erro de grafia.
- Próximo passo: Marco 5 — prompt da ata e chamada ao Ollama.

## 2026-10-25 — Marco 5
- Feito: `live.py` salva o transcript em `output/transcript-AAAA-MM-DD-HHMM.txt` aos poucos (modo `"a"` + `flush()` a cada frase) e, no Ctrl+C, chama `src/minutes.py`, que manda o transcript + `prompts/minutes.txt` pro Ollama (`qwen2.5:7b`, temperatura 0.2, `num_ctx` 16384) e salva `output/ata-AAAA-MM-DD-HHMM.md`. A seção "Menções ao Breno" é montada no código com o `name_detector`, não pelo LLM. Aceite ok: aula pública de economia de 20+ min, 0 tarefas inventadas.
- Travou em:
  - Rodar de dentro de `src/` jogava `output/` e até o prompt em `src/output/` (que está no `.gitignore`). Solução: caminhos a partir de `Path(__file__)`.
  - Prompt em 4+ rodadas. O 7B colocava introdução e bloco de código em volta da ata, escrevia "Nenhuma" no resumo, dava nota 10 com "não se aplica" no email, **copiou o exemplo do prompt como se fosse uma menção real**, juntava duas frases numa citação, e com exemplos de frases de tarefa passou a marcar tudo como tarefa. O que funcionou: template sem exemplo concreto, "na dúvida, não liste", citação de uma única linha, sem regras condicionais.
  - O modelo achava que o Breno falava no transcript. Mas o loopback não pega o microfone: tudo é fala dos outros. Virou regra explícita no prompt.
  - LLM listava só 6 de ~16 menções → menções saíram do LLM e foram pro código (determinístico).
  - Ollama caiu com `HTTP 500` / `CUDA error: shared object initialization failed` ao carregar o modelo na GPU (RTX 3050 6 GB) logo depois da sessão. Na segunda tentativa funcionou. Como o transcript é salvo aos poucos, nada se perdeu.
- Aprendi: o Ollama é uma API HTTP local (`POST /api/generate`); `num_ctx` padrão é pequeno e corta o transcript sem avisar; modelo pequeno copia exemplos e se perde com "se X então Y"; usar o LLM só onde ele é necessário.
- Números medidos: aula de 20 min = 2.655 palavras = 5.091 tokens de entrada (acima do contexto padrão do Ollama); ata em 36 s na GPU. Roteiro dos "Breno": ata em ~23 s; 14 menções pelo detector contra 6 pelo LLM.
- Limitação conhecida: o 7B ainda erra o rótulo (classifica decisões como tarefas, perde "o Bruno vai apresentar"); último bloco de ~5 s pode não entrar na ata se o Ctrl+C chegar durante a transcrição dele.
- Próximo passo: Marco 6 — overlay do sloth.

## 2026-10-25 — Marco 6
- Feito: `src/overlay.py` — janela tkinter sem borda, sempre no topo, fundo magenta transparente (`-transparentcolor`), 20 quadros: ronco em loop (01–04), despertar (05–12), pegar o caderninho (13–16) e anotar em loop (17–20) por 8 s; arrastar com o botão esquerdo, fechar com o direito. `scripts/prepare_sprites.py` reduz a arte pra 140 px e troca o fundo "quase magenta" pelo `#FF00FF` exato. Ligado no `live.py`: a janela ocupa a thread principal e a thread do Whisper só deixa pedidos numa fila. Aceite ok: o sloth acordou numa call real.
- Travou em: os sprites gerados por IA tinham fundo magenta com ruído, e o tkinter só deixa transparente a cor exata → script de limpeza. Com a animação de anotação, um timer só não bastava (renovar os 8 s parava a animação) → dois timers. O nome estava fixo em 3 lugares → `NAME` único em `name_detector.py`.
- Aprendi: tkinter só pode ser tocado pela thread principal (≈ `SwingUtilities.invokeLater`); `after()` agenda sem travar a janela, `time.sleep` congela; Ctrl+C dentro do `mainloop()` precisa de `signal` + um `after()` periódico.
- Próximo passo: Marco 7.

## 2026-10-26 — Marco 7
- Feito: call real com roteiro de reunião falsa (churrasco, 5 decisões + 5 tarefas + armadilhas); `eval/results.md`; README em inglês com licença MIT; repo renomeado para `durmain`; vídeo da demo gravado com o Wi-Fi desligado; post publicado: https://dev.to/breno-cardoso/i-dont-listen-to-meetings-anymore-my-sloth-does-39fg
- Travou em: o Ollama não aparece como `python` nem `ollama` no Gerenciador de Tarefas quando roda o modelo (processo separado, `llama-server`) — o pico de RAM do LLM não foi medido. A Xbox Game Bar grava só uma janela; a demo foi gravada com a Ferramenta de Captura.
- Aprendi: na call, o amigo tem que falar cada decisão e tarefa completa, porque a minha voz não entra no transcript. As falhas que sobraram são quase todas borda de bloco, não o detector nem o LLM.
- Números medidos: nome 8/10 na call, 0 alarmes falsos; latência média 2,5 s (4 medições); ata 8/10 com 0 inventado; Python 583 MB de pico; CPU ~40–50% por 1–2 s a cada bloco, ~3% entre blocos; ata da call em 42 s (14 tokens/s na GPU).
- Cortado pelo prazo: WER; sobreposição entre blocos.
- Próximo passo (extras): sobreposição curta entre blocos; mostrar o contexto da menção no overlay; testar Gemma no lugar do Qwen.
