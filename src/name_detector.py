import re
from rapidfuzz import fuzz

NAME = "breno"
LIMITE = 85

def menciona_nome(texto):
    texto1 = texto.lower()
    texto2 = re.sub(r"[^\w\s]", "", texto1)
    texto3 = texto2.split()
    return any(fuzz.ratio(NAME, palavra) >= 85 for palavra in texto3)