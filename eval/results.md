# Validation results

Machine: Windows 11 laptop, 16 GB RAM, RTX 3050 Laptop (6 GB).
Whisper `small` on CPU (`int8`), `qwen2.5:7b` through Ollama (GPU, picked automatically).

## Summary

| Metric | How it was measured | Target | Result |
|---|---|---|---|
| Name detection | Live call, 10 lines containing the name | ≥ 80% | **8/10** ✅ |
| False alarms | Same call, lines with "Bruno", "Brenda", "treino" | ≤ 2 | **0** ✅ |
| Name detection (scripted) | Recording with 20 mentions + 6 decoys | ≥ 16/20 | **16/20**, 0 false alarms ✅ |
| Alert latency | Phone stopwatch, name spoken → sloth wakes up | < 10 s | **2.5 s** average (4 measurements) ✅ |
| Minutes fidelity | Scripted meeting with 5 decisions + 5 tasks | ≥ 80%, 0 invented | **8/10**, **0 invented** ✅ |
| Hallucinations in silence | Paused video / silence during live runs | 0 | **0** ✅ |
| Offline | — | works | Not recorded on video yet |
| Peak RAM (transcription) | Working set of the Python process | note | **583 MB** |
| LLM speed | Ollama log, call minutes | note | 14 tokens/s, 42 s total (7.8 s model load) |
| WER | — | < 20% | Not measured (cut for time) |

## 1. Name detection, scripted recording

Same recording played twice: 20 sentences with "Breno" and 6 decoys
("O Bruno vai apresentar...", "A Brenda mandou...", "O treino...", "pleno vapor", "freio").

| | Without `hotwords` | With `hotwords="Breno"` |
|---|---|---|
| Detected | 15/20 | 16/20 |
| False alarms | 0/6 | 0/6 (5 observable) |
| Misspellings that hid the name | "Brenna", "Brena", "Bruno", "branco" | "Brenéana" |
| Sentences that never reached the detector | 1 | 3 |

`hotwords` fixed every misspelling except one, without turning the real "Bruno" and "Brenda"
into "Breno". Lowering the fuzzy threshold to 80 would also have caught "Bruno" and "Brena",
but the decoy sentences would then wake the sloth.

## 2. Live call

A friend read a scripted planning meeting (a year-end barbecue) over a voice call.
Only the friend's voice is captured: loopback records what the PC plays, not the microphone.

**Name:** 8 of 10 lines woke the sloth. In both misses the word "Breno" is simply absent
from the transcript (lost at a block boundary), so the detector never saw it.
No decoy line woke it up.

**Latency:** 3 s, 3 s, 2 s, 2 s. One more attempt didn't wake the sloth (the missed line above).
The theoretical worst case is ~7 s: a name at the very start of a 5 s block waits for the
block to close, plus ~1.7 s of transcription.

**Minutes fidelity:**

| Expected | In the minutes |
|---|---|
| D1 Saturday, Nov 15 | ✅ |
| D2 At Ana's house | ✅ (merged with D1) |
| D3 Starts at noon | ✅ (merged with D1) |
| D4 R$ 50 each | ✅ |
| D5 No secret Santa this year | ❌ |
| T1 Expense spreadsheet — Breno | ✅ |
| T2 Buy the meat — Pedro | ✅ |
| T3 Drinks — Carla | ❌ Whisper transcribed "A Cala vai ficar responsável pelas..." and cut "bebidas" |
| T4 Borrow chairs — Ana | ✅ (responsible person missing) |
| T5 Create the group and send invites — Breno | ✅ |

8/10 captured. None of the six traps (announcements, "maybe next year", "nobody needs to")
became a task or a decision. One quote was paraphrased by the model instead of copied.

## 3. 20-minute public lecture

| | |
|---|---|
| Transcript | 2,655 words → 5,091 input tokens |
| Minutes | ~36 s on GPU |
| Invented tasks | 0 (the lecture has none, and the minutes listed none) |

5,091 tokens is above Ollama's default context window. Without `num_ctx: 16384`, the
model would have silently read only the beginning of the lecture.

## 4. Transcription speed

38 blocks of 5 s from a public talk: 1.68 s average processing (min 1.49, max 2.33),
queue always empty. Real-time factor ≈ 0.34 per 5 s block, vs 0.15 for a single
30 s file: each call to Whisper has a fixed cost.
