# Roda uma vez: assets/originais/*.png (1024 px, fundo magenta com ruído)
# -> assets/sloth_01.png ... sloth_12.png (140 px, fundo #FF00FF exato).
# O tkinter só deixa transparente a cor EXATA, então o ruído do fundo precisa sumir.
# Requer Pillow (só para este script): pip install pillow
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
ORIGINAIS = RAIZ / "assets" / "originais"
DESTINO = RAIZ / "assets"
TAMANHO = 140
MAGENTA = (255, 0, 255)


def limpar_fundo(imagem):
    pixels = np.array(imagem.convert("RGB")).astype(int)
    r, g, b = pixels[..., 0], pixels[..., 1], pixels[..., 2]
    # magenta = vermelho e azul altos, verde baixo; o sloth (marrom, bege, amarelo) nunca é assim
    eh_fundo = (r - g > 60) & (b - g > 60)
    pixels[eh_fundo] = MAGENTA
    return Image.fromarray(pixels.astype(np.uint8))


for i, original in enumerate(sorted(ORIGINAIS.glob("*.png")), start=1):
    imagem = Image.open(original).resize((TAMANHO, TAMANHO), Image.LANCZOS)
    # limpa DEPOIS de reduzir: assim os pixels da borda misturados com magenta também viram fundo
    destino = DESTINO / f"sloth_{i:02d}.png"
    limpar_fundo(imagem).save(destino)
    print(f"{original.name} -> {destino.name}")
