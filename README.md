<p align="center">
  <img src="docs/sloth_sleeping.png" width="160" alt="SlothNotes sleeping">
  &nbsp;&nbsp;&nbsp;
  <img src="docs/sloth_writing.png" width="160" alt="SlothNotes taking notes">
</p>

<h1 align="center">SlothNotes</h1>

<p align="center">
  A sloth that sleeps in the corner of your screen during calls and lectures,<br>
  wakes up when someone says your name, and writes the minutes when it's over.<br>
  <b>Everything runs on your machine. No audio or text ever leaves it.</b>
</p>

---

## Why

Some meetings only need you for the thirty seconds when someone asks you something. The rest of the time you're half listening, and that's exactly when your name gets called.

SlothNotes listens to your computer's audio, transcribes it locally, and stays asleep until your name comes up. Then it wakes up, shows what was just said, and starts taking notes. When the call ends, a local LLM turns the transcript into minutes: a summary, decisions, tasks, every time you were mentioned, and an honest score for "this could have been an email".

Meeting audio is other people's voices and other people's words. It shouldn't go to a third-party server just so you can get a summary, so it doesn't. The speech model and the LLM are both open, and both run offline.

## How it works

```
system audio ──► 5 s blocks ──► faster-whisper + VAD ──► transcript (.txt)
 (WASAPI loopback)                       │                        │
                                         ▼                        ▼ on exit
                                 name detector ──► sloth   Ollama (qwen2.5:7b)
                                 (fuzzy match)     wakes up        │
                                                                   ▼
                                                            minutes (.md)
```

1. **Capture.** [`pyaudiowpatch`](https://github.com/s0d3s/PyAudioWPatch) records whatever your PC is playing (the call, the lecture) through WASAPI loopback, in 5-second blocks. Your microphone is not captured: the people saying your name are the others.
2. **Transcribe.** Each block is converted to 16 kHz mono and sent to [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (`small`, CPU, `int8`) on a separate thread, so recording never waits for transcription. Voice activity detection plus a confidence filter keeps Whisper from inventing sentences during silence.
3. **Detect the name.** Every sentence is checked word by word with [`rapidfuzz`](https://github.com/rapidfuzz/RapidFuzz), because Whisper rarely spells a name the same way twice. Whisper also gets the name as a `hotword`, which nudges it toward the right spelling in the first place.
4. **Wake up.** The sloth is a borderless, always-on-top `tkinter` window. It snores while nobody needs you, wakes up, grabs a notebook and writes for a few seconds every time your name comes up.
5. **Write the minutes.** When you close the sloth, the full transcript goes to [Ollama](https://ollama.com) running `qwen2.5:7b`. The prompt only allows things that were said explicitly, each one with the quote it came from. The "mentions" section isn't written by the LLM at all: the name detector already found them, and it doesn't forget any.

## Requirements

- **Windows 10 or 11.** Loopback capture uses WASAPI, and the transparent window uses a Windows-only `tkinter` feature.
- **Python 3.11+** (developed on 3.13).
- **[Ollama](https://ollama.com/download)** with the `qwen2.5:7b` model (~4.7 GB).
- **~8 GB of free RAM** for the LLM step. It only runs after the call ends, never at the same time as transcription.
- A GPU is optional. Whisper runs on CPU. Ollama will use your GPU if it has one.

## Setup

```powershell
git clone https://github.com/breno-concrete/slothnotes.git
cd slothnotes

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

ollama pull qwen2.5:7b
```

The first run downloads the Whisper `small` model (~480 MB). After that, everything works with Wi-Fi off.

## Usage

Make sure Ollama is running (open the app, or run `ollama serve`), then from the project folder:

```powershell
python src/live.py
```

- The sloth appears in the bottom-right corner. Drag it with the left mouse button.
- The terminal shows the live transcript and an alert with context whenever your name is mentioned.
- To end the session, **right-click the sloth** or press **Ctrl+C** in the terminal.

Two files land in `output/`:

| File | What's in it |
|---|---|
| `transcript-YYYY-MM-DD-HHMM.txt` | Everything that was said, written as it was transcribed, so a crash doesn't lose the session |
| `ata-YYYY-MM-DD-HHMM.md` | The minutes ("ata" is Portuguese for minutes) |

If generating the minutes fails (for example, Ollama isn't running), the transcript is still there. Run this to try again:

```powershell
python src/minutes.py output/transcript-YYYY-MM-DD-HHMM.txt
```

### Using your own name

Change one line in `src/name_detector.py`:

```python
NAME = "Breno"
```

The detector, the Whisper hotword and the minutes prompt all read it from there.

Transcription is set to Portuguese (`language="pt"`) and the prompt is written in Portuguese. Both are easy to change, but they're the only languages it has been tested with.

## Results

Measured on a laptop with 16 GB of RAM, an RTX 3050 (6 GB) and Whisper on CPU. Full numbers and method in [`eval/results.md`](eval/results.md); the story behind them is in [`DEVLOG.md`](DEVLOG.md).

| What | Result |
|---|---|
| Name detection, live call | **8/10** mentions caught, **0** false alarms ("Bruno", "Brenda", "treino") |
| Name detection, scripted recording | **16/20**, 0 false alarms (15/20 before adding the `hotword`) |
| Alert latency | **2.5 s** average on the live call, ~7 s worst case |
| Minutes fidelity | **8/10** decisions and tasks captured, **0 invented** |
| Minutes for a 20-minute lecture | 5,091 input tokens, ~36 s, 0 invented tasks |
| Mentions in the minutes | 14/14 found by the detector, vs 6 when the LLM was asked to list them |
| Transcription speed | A 5 s block takes ~1.7 s, so the queue never grows |
| Hallucinations in silence | 0 invented sentences |
| Peak RAM during transcription | 583 MB |

## Known limitations

- **Words cut at block boundaries.** Blocks don't overlap, so a word spoken right at the edge of a block can be split or lost. Most of the missed name mentions in testing were sentences that never reached the detector, not misspellings.
- **The LLM sometimes mislabels.** `qwen2.5:7b` doesn't invent tasks, but it sometimes files a decision as a task, or misses a task given to someone else.
- **No speaker names.** The transcript doesn't know who said what, so the minutes can't either.
- **The last few seconds may be dropped.** If you close the sloth while the last block is still being transcribed, that block doesn't make it into the minutes.
- **Windows only**, for now.

## Privacy and consent

- Audio is processed in memory and never saved. Transcripts and minutes stay in `output/`, which is in `.gitignore`.
- Nothing is sent over the network. The only connection the project makes is to Ollama on `localhost`.
- **Recording people requires their consent.** Tell the people on the call that you are transcribing it, and follow your school's and company's rules and the law where you live. Running locally protects the data. It doesn't replace asking.

## Project structure

```
src/
  live.py            capture, live transcription, alerts and the end of the session
  audio_convert.py   int16 stereo 48 kHz → float32 mono 16 kHz for Whisper
  name_detector.py   fuzzy name matching
  overlay.py         the sloth window and its animations
  minutes.py         sends the transcript to Ollama and saves the minutes
prompts/
  minutes.txt        the minutes prompt
assets/
  sloth_01..20.png   animation frames (snoring, waking up, taking notes)
  originais/         original 1024 px artwork
scripts/
  prepare_sprites.py resizes the artwork and cleans the background for the transparent window
```

## Built with

[faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [Ollama](https://ollama.com) · [Qwen2.5](https://github.com/QwenLM/Qwen2.5) · [PyAudioWPatch](https://github.com/s0d3s/PyAudioWPatch) · [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz)

Built for the Hacktoberfest Open-Source AI Challenge, week 3: *Slow and Steady*.

## License

[MIT](LICENSE)
