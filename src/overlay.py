import queue
import signal
import tkinter as tk
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_ASSETS = RAIZ / "assets"

# cor de fundo dos sprites; o Windows deixa essa cor invisível
# (scripts/prepare_sprites.py garante que o fundo é exatamente essa cor)
COR_TRANSPARENTE = "#ff00ff"
MARGEM = 20

# quadros 01–04: sono e ronco; 05–12: despertar até a surpresa
SONO = [0, 1, 2, 3, 2, 1]
DESPERTAR = list(range(4, 12))
VOLTAR = DESPERTAR[::-1]

RONCO_MS = 500
QUADRO_MS = 120
ACORDADO_MS = 8000


class Overlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # sem borda nem barra de título
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", COR_TRANSPARENTE)
        self.root.config(bg=COR_TRANSPARENTE)

        caminhos = sorted(PASTA_ASSETS.glob("sloth_??.png"))
        self.quadros = [tk.PhotoImage(file=c) for c in caminhos]

        self.label = tk.Label(self.root, bg=COR_TRANSPARENTE, bd=0)
        self.label.pack()
        self.atual = 0
        self.acordado = False
        self._job = None

        # canto inferior direito, acima da barra de tarefas
        largura, altura = self.quadros[0].width(), self.quadros[0].height()
        x = self.root.winfo_screenwidth() - largura - MARGEM
        y = self.root.winfo_screenheight() - altura - MARGEM - 40
        self.root.geometry(f"+{x}+{y}")

        # arrastar com o botão esquerdo, fechar com o direito
        self.label.bind("<Button-1>", self._inicio_arraste)
        self.label.bind("<B1-Motion>", self._arrastar)
        self.label.bind("<Button-3>", lambda e: self.fechar())

        # outras threads não podem mexer no tkinter: elas só deixam pedidos aqui
        self.pedidos = queue.Queue()
        self._verificar_pedidos()
        self._roncar()

    def acordar(self):
        # pode ser chamado de qualquer thread
        self.pedidos.put("acordar")

    def rodar(self):
        # Ctrl+C no terminal fecha a janela; o after() periódico deixa o Python tratar o sinal
        signal.signal(signal.SIGINT, lambda *_: self.fechar())
        self.root.mainloop()

    def fechar(self):
        self.root.destroy()

    def _verificar_pedidos(self):
        while not self.pedidos.empty():
            self.pedidos.get()
            self._acordar()
        self.root.after(100, self._verificar_pedidos)

    def _roncar(self, passo=0):
        self._mostrar(SONO[passo % len(SONO)])
        self._job = self.root.after(RONCO_MS, self._roncar, passo + 1)

    def _acordar(self):
        self._cancelar()
        # se já estava acordado, só recomeça a contagem dos 8 s
        if self.acordado:
            self._agendar_dormir()
            return
        self.acordado = True
        self._animar(DESPERTAR, self._agendar_dormir)

    def _agendar_dormir(self):
        self._job = self.root.after(ACORDADO_MS, self._voltar_a_dormir)

    def _voltar_a_dormir(self):
        self.acordado = False
        self._animar(VOLTAR, self._roncar)

    def _animar(self, indices, ao_terminar):
        if not indices:
            ao_terminar()
            return
        self._mostrar(indices[0])
        self._job = self.root.after(QUADRO_MS, self._animar, indices[1:], ao_terminar)

    def _cancelar(self):
        if self._job:
            self.root.after_cancel(self._job)
            self._job = None

    def _mostrar(self, indice):
        self.atual = indice
        self.label.config(image=self.quadros[indice])

    def _inicio_arraste(self, evento):
        self._dx, self._dy = evento.x, evento.y

    def _arrastar(self, evento):
        x = self.root.winfo_x() + evento.x - self._dx
        y = self.root.winfo_y() + evento.y - self._dy
        self.root.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    # demo: outra thread acorda o sloth a cada 15 s, como o detector vai fazer
    import threading
    import time

    overlay = Overlay()

    def simular_mencoes():
        while True:
            time.sleep(15)
            print("Mencionaram seu nome!!! (simulado)")
            overlay.acordar()

    threading.Thread(target=simular_mencoes, daemon=True).start()
    overlay.rodar()
