import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import sys
from conversor import ConversorMapasFrame
from gerador_pdf import GeradorPDFFaturaFrame
from relatorio_cnpj_pdf import RelatorioCNPJFrame

# ──────────────────────────────────────────────
#  Utilitários
# ──────────────────────────────────────────────
MAX_FILE_MB = 50  # Limite de tamanho de arquivo (pentest / DoS)
EXTENSOES_VALIDAS = {".xlsx", ".xls"}


def resource_path(relative_path: str) -> str:
    """Resolve caminho de recursos compatível com PyInstaller."""
    try:
        base_path = sys._MEIPASS  # type: ignore
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def validar_arquivo_excel(path: str) -> tuple[bool, str]:
    """
    Valida extensão e tamanho do arquivo.
    Retorna (True, '') se válido ou (False, motivo) se inválido.
    """
    if not path:
        return False, "Nenhum arquivo selecionado."
    ext = os.path.splitext(path)[1].lower()
    if ext not in EXTENSOES_VALIDAS:
        return False, f"Extensão inválida: '{ext}'. Use .xlsx ou .xls."
    try:
        tamanho_mb = os.path.getsize(path) / (1024 * 1024)
    except OSError:
        return False, "Não foi possível verificar o tamanho do arquivo."
    if tamanho_mb > MAX_FILE_MB:
        return False, f"Arquivo muito grande ({tamanho_mb:.1f} MB). Limite: {MAX_FILE_MB} MB."
    return True, ""


def validar_pasta_destino(path: str) -> tuple[bool, str]:
    """Verifica se a pasta existe e tem permissão de escrita."""
    if not path:
        return False, "Nenhuma pasta selecionada."
    if not os.path.isdir(path):
        return False, "Pasta não encontrada."
    # Pentest: path traversal — garante que é um diretório real, não relativo malicioso
    path_real = os.path.realpath(path)
    if not os.access(path_real, os.W_OK):
        return False, "Sem permissão de escrita na pasta."
    return True, ""


# ──────────────────────────────────────────────
#  Cores
# ──────────────────────────────────────────────
BTN_FG            = "#0B8052"
BTN_HOVER         = "#0E9E66"
SIDEBAR_BG        = "#0F172A"
CONTAINER_BG      = "#1E293B"
SIDEBAR_BTN_FG    = "#134E8B"
SIDEBAR_BTN_HOVER = "#1D67B5"
SIDEBAR_BTN_ACTIVE= "#288ED3"
TEXT_COLOR_GRAY   = "#A0A0A0"
HEADER_COLOR      = "#E0E0E0"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ──────────────────────────────────────────────
#  Tela inicial
# ──────────────────────────────────────────────
class InicioFrame(ctk.CTkFrame):
    def __init__(self, master, app=None):
        super().__init__(master)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure((0, 1), weight=1)
        self.rowconfigure((0, 1, 2, 3, 4, 5), weight=1)

        ctk.CTkLabel(
            self,
            text="Sistema Administrativo - COPESP",
            font=("Segoe UI", 30, "bold"),
            text_color=HEADER_COLOR
        ).grid(row=0, column=0, columnspan=2, pady=(30, 10))

        ctk.CTkLabel(
            self,
            text="Selecione o arquivo do mapa (.xlsx) e a pasta onde serão salvos os resultados.",
            font=("Segoe UI", 16),
            wraplength=600,
            justify="center",
            text_color=TEXT_COLOR_GRAY
        ).grid(row=1, column=0, columnspan=2, pady=(20, 10), padx=20)

        ctk.CTkButton(
            self, text="➕ Anexar Mapa",
            command=self.app.anexar_mapa,
            fg_color=BTN_FG, hover_color=BTN_HOVER,
            font=("Segoe UI", 18, "bold"),
            width=180, height=60, corner_radius=10
        ).grid(row=2, column=0, padx=30, sticky="e")

        ctk.CTkButton(
            self, text="📁 Selecionar Pasta",
            command=self.app.selecionar_pasta_destino,
            fg_color=BTN_FG, hover_color=BTN_HOVER,
            font=("Segoe UI", 18, "bold"),
            width=180, height=60, corner_radius=10
        ).grid(row=2, column=1, padx=30, sticky="w")

        ctk.CTkLabel(
            self,
            text="Escolha uma das opções ao lado para iniciar.",
            font=("Segoe UI", 16),
            text_color=TEXT_COLOR_GRAY
        ).grid(row=3, column=0, columnspan=2, pady=20)

        self.status_label = ctk.CTkLabel(
            self, text="",
            font=("Segoe UI", 14),
            text_color=TEXT_COLOR_GRAY
        )
        self.status_label.grid(row=4, column=0, columnspan=2, pady=(0, 10))

        ctk.CTkLabel(
            self,
            text="Desenvolvido por Cb Pacífico",
            font=("Segoe UI", 12, "italic"),
            text_color=TEXT_COLOR_GRAY
        ).grid(row=5, column=0, columnspan=2, pady=(10, 30))

    def atualizar_status(self, mapa: str | None, pasta: str | None):
        partes = []
        if mapa:
            partes.append(f"📄 Mapa: {os.path.basename(mapa)}")
        if pasta:
            partes.append(f"📁 Pasta: {os.path.basename(pasta)}")
        self.status_label.configure(text="\n".join(partes) if partes else "")


# ──────────────────────────────────────────────
#  Aplicação principal
# ──────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        ico = resource_path("icone.ico")
        if os.path.isfile(ico):
            self.iconbitmap(ico)

        self.title("Note Maps v2.0 - COPESP")
        self.geometry("970x700")
        self.minsize(950, 650)
        self.configure(bg=SIDEBAR_BG)

        # Estado central — única fonte da verdade
        self.arquivo_mapa: str | None = None
        self.pasta_destino: str | None = None

        self._build_sidebar()
        self._build_container()

        # Instancia todos os frames de uma vez — evita bug de lazy init
        self.frames: dict = {}
        self._init_frames()
        self.show_inicio()

        # Atalhos de teclado
        self.bind_all("<Control-1>", lambda _: self.show_inicio())
        self.bind_all("<Control-2>", lambda _: self.show_conversor())
        self.bind_all("<Control-3>", lambda _: self.show_pdf())
        self.bind_all("<Control-4>", lambda _: self.show_relatorio_cnpj())

    # ── Layout ──────────────────────────────
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=260, fg_color=SIDEBAR_BG)
        self.sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(
            self.sidebar,
            text="Menu Principal",
            font=("Segoe UI", 26, "bold"),
            pady=30,
            text_color=HEADER_COLOR
        ).pack()

        def _btn(texto, cmd):
            return ctk.CTkButton(
                self.sidebar, text=texto, command=cmd,
                fg_color=SIDEBAR_BTN_ACTIVE, hover_color=SIDEBAR_BTN_HOVER,
                text_color="#ffffff", font=("Segoe UI", 16, "bold"),
                height=38, corner_radius=7,
                border_width=0.5, border_color=CONTAINER_BG,
                anchor="center",
            )

        _btn("🏠 Início", self.show_inicio).pack(fill="x", pady=(10, 8), padx=15)
        _btn("🧾 Gerar Extrato NF", self.show_conversor).pack(fill="x", pady=(5, 7), padx=15)
        _btn("📄 Relatório Detalhado", self.show_pdf).pack(fill="x", pady=(5, 7), padx=15)
        _btn("📑 Relatório por CNPJ/PI", self.show_relatorio_cnpj).pack(fill="x", pady=(5, 7), padx=15)

        ctk.CTkFrame(self.sidebar, height=2, fg_color=CONTAINER_BG, corner_radius=1).pack(
            fill="x", padx=24, pady=12
        )

        self.status_sidebar = ctk.CTkLabel(
            self.sidebar,
            text="Nenhum arquivo anexado",
            font=("Segoe UI", 12),
            text_color=TEXT_COLOR_GRAY,
            wraplength=220,
            justify="center"
        )
        self.status_sidebar.pack(side="bottom", pady=20, padx=20)

    def _build_container(self):
        self.container = ctk.CTkFrame(self, fg_color=CONTAINER_BG)
        self.container.pack(side="right", fill="both", expand=True)

    def _init_frames(self):
        """
        Instancia todos os frames antecipadamente para que
        atualizar_arquivo_mapa / atualizar_pasta_destino sempre funcionem,
        mesmo antes do usuário navegar para a aba.
        CORREÇÃO: elimina o bug em que GeradorPDF não carregava se a aba
        não havia sido visitada antes de anexar o mapa.
        """
        for cls in (InicioFrame, ConversorMapasFrame,
                    GeradorPDFFaturaFrame, RelatorioCNPJFrame):
            frame = cls(self.container, app=self)
            self.frames[cls] = frame
        self.current_frame = None

    # ── Navegação ────────────────────────────
    def show_frame(self, frame_class):
        if self.current_frame:
            self.current_frame.pack_forget()
        self.current_frame = self.frames[frame_class]
        self.current_frame.pack(fill="both", expand=True)

    def show_inicio(self):        self.show_frame(InicioFrame)
    def show_conversor(self):     self.show_frame(ConversorMapasFrame)
    def show_pdf(self):           self.show_frame(GeradorPDFFaturaFrame)
    def show_relatorio_cnpj(self): self.show_frame(RelatorioCNPJFrame)

    # ── Ações globais ────────────────────────
    def anexar_mapa(self):
        path = filedialog.askopenfilename(
            title="Selecione o arquivo Excel do mapa",
            filetypes=[("Arquivos Excel", "*.xlsx *.xls")]
        )
        if not path:
            return
        ok, msg = validar_arquivo_excel(path)
        if not ok:
            messagebox.showerror("Arquivo inválido", msg)
            return

        self.arquivo_mapa = path
        self._sincronizar_frames()

    def selecionar_pasta_destino(self):
        path = filedialog.askdirectory(title="Selecione a pasta destino")
        if not path:
            return
        ok, msg = validar_pasta_destino(path)
        if not ok:
            messagebox.showerror("Pasta inválida", msg)
            return

        self.pasta_destino = path
        self._sincronizar_frames()

    def _sincronizar_frames(self):
        """
        Propaga arquivo_mapa e pasta_destino para todos os frames.
        Centraliza a atualização — sem risco de sobrescrita parcial.
        """
        nome_mapa = os.path.basename(self.arquivo_mapa) if self.arquivo_mapa else "—"
        nome_pasta = os.path.basename(self.pasta_destino) if self.pasta_destino else "—"
        self.status_sidebar.configure(
            text=f"📄 {nome_mapa}\n📁 {nome_pasta}"
        )

        for frame in self.frames.values():
            if hasattr(frame, "atualizar_arquivo_mapa") and self.arquivo_mapa:
                frame.atualizar_arquivo_mapa(self.arquivo_mapa)
            if hasattr(frame, "atualizar_pasta_destino") and self.pasta_destino:
                frame.atualizar_pasta_destino(self.pasta_destino)

        # Atualiza tela inicial separadamente
        inicio = self.frames.get(InicioFrame)
        if inicio:
            inicio.atualizar_status(self.arquivo_mapa, self.pasta_destino)


if __name__ == "__main__":
    app = App()
    app.mainloop()
