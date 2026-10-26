import json
import sys
import time
import urllib.request
from pathlib import Path

from name_detector import NAME, menciona_nome

# raiz do projeto, para funcionar rodando de qualquer pasta
RAIZ = Path(__file__).resolve().parent.parent
PROMPT = RAIZ / "prompts" / "minutes.txt"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO = "qwen2.5:7b"


def secao_mencoes(transcript):
    # feito no código, não no LLM: o detector acha todas, o modelo esquecia metade
    linhas = [linha for linha in transcript.splitlines() if menciona_nome(linha)]
    itens = "\n".join(f'- "{linha}"' for linha in linhas) or "Nenhuma"
    return f"## Menções ao {NAME}\n{itens}\n"


def gerar_ata(caminho_transcript):
    caminho_transcript = Path(caminho_transcript)
    transcript = caminho_transcript.read_text(encoding="utf-8")
    prompt = PROMPT.read_text(encoding="utf-8").replace("{nome}", NAME).replace("{transcript}", transcript)

    corpo = {
        "model": MODELO,
        "prompt": prompt,
        "stream": False,
        "options": {
            # pouca criatividade: a ata tem que se prender ao que foi dito
            "temperature": 0.2,
            # o padrão do Ollama é pequeno e corta transcripts longos sem avisar
            "num_ctx": 16384,
        },
    }
    requisicao = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(corpo).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    inicio = time.perf_counter()
    # em CPU a ata pode levar alguns minutos
    with urllib.request.urlopen(requisicao, timeout=900) as resposta:
        resultado = json.loads(resposta.read())
    duracao = time.perf_counter() - inicio

    # transcript-2026-10-25-1333.txt -> ata-2026-10-25-1333.md
    carimbo = caminho_transcript.stem.removeprefix("transcript-")
    caminho_ata = RAIZ / "output" / f"ata-{carimbo}.md"
    ata = resultado["response"].strip() + "\n\n" + secao_mencoes(transcript)
    caminho_ata.write_text(ata, encoding="utf-8")

    tokens_prompt = resultado.get("prompt_eval_count", 0)
    print(f"ata salva em {caminho_ata}")
    print(f"   [gerou em {duracao:.1f} s | {tokens_prompt} tokens de entrada | limite {corpo['options']['num_ctx']}]")
    return caminho_ata


if __name__ == "__main__":
    gerar_ata(sys.argv[1])
