import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import sys
from conversor import ConversorMapasFrame
from gerador_pdf import GeradorPDFFaturaFrame
from relatorio_cnpj_pdf import RelatorioCNPJFrame

# ──────────────────────────────────────────────
#  Utilitarios
# ──────────────────────────────────────────────
MAX_FILE_MB = 50
EXTENSOES_VALIDAS = {".xlsx", ".xls"}


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def _desktop_padrao():
    """
    Retorna o caminho da Area de Trabalho do usuario atual (Windows/Mac/Linux).
    Tenta OneDrive, Desktop e Area de Trabalho em ordem.
    Fallback para pasta home se nenhuma for encontrada.
    """
    home = os.path.expanduser("~")
    candidatos = [
        os.path.join(home, "OneDrive", "Desktop"),
        os.path.join(home, "OneDrive", "Area de Trabalho"),
        os.path.join(home, "Desktop"),
        os.path.join(home, "Area de Trabalho"),
        # Windows em PT-BR nativo
        os.path.join(os.environ.get("USERPROFILE", home), "Desktop"),
        os.path.join(os.environ.get("USERPROFILE", home), "Area de Trabalho"),
    ]
    for p in candidatos:
        if os.path.isdir(p) and os.access(p, os.W_OK):
            return p
    return home


def validar_arquivo_excel(path):
    if not path:
        return False, "Nenhum arquivo selecionado."
    ext = os.path.splitext(path)[1].lower()
    if ext not in EXTENSOES_VALIDAS:
        return False, f"Extensao invalida: '{ext}'. Use .xlsx ou .xls."
    try:
        tamanho_mb = os.path.getsize(path) / (1024 * 1024)
    except OSError:
        return False, "Nao foi possivel verificar o tamanho do arquivo."
    if tamanho_mb > MAX_FILE_MB:
        return False, f"Arquivo muito grande ({tamanho_mb:.1f} MB). Limite: {MAX_FILE_MB} MB."
    return True, ""


def validar_pasta_destino(path):
    if not path:
        return False, "Nenhuma pasta selecionada."
    if not os.path.isdir(path):
        return False, "Pasta nao encontrada."
    path_real = os.path.realpath(path)
    if not os.access(path_real, os.W_OK):
        return False, "Sem permissao de escrita na pasta."
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
SIDEBAR_BTN_ACTIVE= "#1a5fa8"
TEXT_COLOR_GRAY   = "#94A3B8"
HEADER_COLOR      = "#F1F5F9"
ACCENT            = "#0E9E66"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ──────────────────────────────────────────────
#  Tela inicial
# ──────────────────────────────────────────────
class InicioFrame(ctk.CTkFrame):
    def __init__(self, master, app=None):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure((0, 1), weight=1)
        self.rowconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

        # Titulo
        ctk.CTkLabel(
            self,
            text="Sistema Administrativo",
            font=("Segoe UI", 32, "bold"),
            text_color=HEADER_COLOR
        ).grid(row=0, column=0, columnspan=2, pady=(40, 2))

        ctk.CTkLabel(
            self,
            text="COPESP",
            font=("Segoe UI", 16),
            text_color=ACCENT
        ).grid(row=1, column=0, columnspan=2, pady=(0, 24))

        ctk.CTkLabel(
            self,
            text="Selecione o arquivo mapa (.xlsx) e a pasta de destino dos resultados.",
            font=("Segoe UI", 14),
            wraplength=540,
            justify="center",
            text_color=TEXT_COLOR_GRAY
        ).grid(row=2, column=0, columnspan=2, pady=(0, 28), padx=20)

        # Botoes principais
        ctk.CTkButton(
            self, text="  Anexar Mapa",
            image=None,
            command=self.app.anexar_mapa,
            fg_color=BTN_FG, hover_color=BTN_HOVER,
            font=("Segoe UI", 15, "bold"),
            width=190, height=52, corner_radius=8
        ).grid(row=3, column=0, padx=20, sticky="e")

        ctk.CTkButton(
            self, text="  Selecionar Pasta",
            command=self.app.selecionar_pasta_destino,
            fg_color=SIDEBAR_BTN_FG, hover_color=SIDEBAR_BTN_HOVER,
            font=("Segoe UI", 15, "bold"),
            width=190, height=52, corner_radius=8
        ).grid(row=3, column=1, padx=20, sticky="w")

        # Aviso pasta automatica
        self.lbl_pasta_auto = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 12),
            text_color=ACCENT,
            wraplength=540,
            justify="center"
        )
        self.lbl_pasta_auto.grid(row=4, column=0, columnspan=2, pady=(12, 0))

        # Status cards
        status_frame = ctk.CTkFrame(self, fg_color="#162032", corner_radius=10)
        status_frame.grid(row=5, column=0, columnspan=2, pady=(20, 0), padx=60, sticky="ew")
        status_frame.columnconfigure((0, 1), weight=1)

        self.lbl_mapa = ctk.CTkLabel(
            status_frame,
            text="Nenhum mapa selecionado",
            font=("Segoe UI", 12),
            text_color=TEXT_COLOR_GRAY,
            wraplength=280, justify="center"
        )
        self.lbl_mapa.grid(row=0, column=0, padx=20, pady=14)

        ctk.CTkFrame(status_frame, width=1, fg_color="#2d4060").grid(row=0, column=1, sticky="ns", pady=10)

        self.lbl_pasta = ctk.CTkLabel(
            status_frame,
            text="Nenhuma pasta selecionada",
            font=("Segoe UI", 12),
            text_color=TEXT_COLOR_GRAY,
            wraplength=280, justify="center"
        )
        self.lbl_pasta.grid(row=0, column=1, padx=20, pady=14)

        ctk.CTkLabel(
            self,
            text="Desenvolvido por Cb Pacifico",
            font=("Segoe UI", 11, "italic"),
            text_color="#3D5A7A"
        ).grid(row=6, column=0, columnspan=2, pady=(18, 20))

    def atualizar_status(self, mapa, pasta):
        if mapa:
            self.lbl_mapa.configure(
                text=f"Mapa ativo\n{os.path.basename(mapa)}",
                text_color=ACCENT
            )
        else:
            self.lbl_mapa.configure(text="Nenhum mapa selecionado", text_color=TEXT_COLOR_GRAY)

        if pasta:
            self.lbl_pasta.configure(
                text=f"Pasta destino\n{os.path.basename(pasta)}",
                text_color="#60A5FA"
            )
        else:
            self.lbl_pasta.configure(text="Nenhuma pasta selecionada", text_color=TEXT_COLOR_GRAY)

    def mostrar_aviso_pasta_auto(self, caminho):
        nome = os.path.basename(caminho)
        self.lbl_pasta_auto.configure(
            text=f"Pasta de destino definida automaticamente: {nome}",
        )


# ──────────────────────────────────────────────
#  Aplicacao principal
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

        self.arquivo_mapa = None

        # Pasta destino: inicia automaticamente na area de trabalho
        self.pasta_destino = _desktop_padrao()

        self._build_sidebar()
        self._build_container()

        self.frames = {}
        self._init_frames()
        self.show_inicio()

        # Atualiza sidebar e inicio com pasta automatica
        self._sincronizar_frames()

        self.bind_all("<Control-1>", lambda _: self.show_inicio())
        self.bind_all("<Control-2>", lambda _: self.show_conversor())
        self.bind_all("<Control-3>", lambda _: self.show_pdf())
        self.bind_all("<Control-4>", lambda _: self.show_relatorio_cnpj())

    # ── Sidebar ─────────────────────────────
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=230, fg_color=SIDEBAR_BG)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo / titulo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(28, 6))

        ctk.CTkLabel(
            logo_frame,
            text="Note Maps",
            font=("Segoe UI", 20, "bold"),
            text_color=HEADER_COLOR
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_frame,
            text="v2.0",
            font=("Segoe UI", 11),
            text_color=ACCENT
        ).pack(anchor="w")

        # Divisor
        ctk.CTkFrame(self.sidebar, height=1, fg_color="#1E3050").pack(fill="x", padx=16, pady=(8, 16))

        # Itens do menu — texto limpo, sem emojis
        menu_items = [
            ("Inicio",              self.show_inicio),
            ("Gerar Extrato NF",    self.show_conversor),
            ("Relatorio Detalhado", self.show_pdf),
            ("Relatorio CNPJ / PI", self.show_relatorio_cnpj),
        ]

        self.sidebar_btns = []
        for label, cmd in menu_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                command=cmd,
                fg_color="transparent",
                hover_color="#1E3050",
                text_color=TEXT_COLOR_GRAY,
                font=("Segoe UI", 13),
                height=36,
                corner_radius=6,
                anchor="w",
            )
            btn.pack(fill="x", padx=12, pady=2)
            self.sidebar_btns.append((label, btn))

        # Divisor inferior
        ctk.CTkFrame(self.sidebar, height=1, fg_color="#1E3050").pack(fill="x", padx=16, pady=(12, 0), side="bottom")

        # Status sidebar
        self.status_sidebar = ctk.CTkLabel(
            self.sidebar,
            text="Sem arquivo anexado",
            font=("Segoe UI", 11),
            text_color="#3D5A7A",
            wraplength=200,
            justify="left"
        )
        self.status_sidebar.pack(side="bottom", pady=14, padx=16, anchor="w")

    def _highlight_btn(self, label_ativo):
        """Destaca visualmente o botao da aba ativa."""
        for label, btn in self.sidebar_btns:
            if label == label_ativo:
                btn.configure(fg_color=SIDEBAR_BTN_ACTIVE, text_color=HEADER_COLOR,
                              font=("Segoe UI", 13, "bold"))
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_COLOR_GRAY,
                              font=("Segoe UI", 13))

    def _build_container(self):
        self.container = ctk.CTkFrame(self, fg_color=CONTAINER_BG)
        self.container.pack(side="right", fill="both", expand=True)

    def _init_frames(self):
        for cls in (InicioFrame, ConversorMapasFrame,
                    GeradorPDFFaturaFrame, RelatorioCNPJFrame):
            frame = cls(self.container, app=self)
            self.frames[cls] = frame
        self.current_frame = None

    # ── Navegacao ───────────────────────────
    def show_frame(self, frame_class, label_menu):
        if self.current_frame:
            self.current_frame.pack_forget()
        self.current_frame = self.frames[frame_class]
        self.current_frame.pack(fill="both", expand=True)
        self._highlight_btn(label_menu)

    def show_inicio(self):
        self.show_frame(InicioFrame, "Inicio")

    def show_conversor(self):
        self.show_frame(ConversorMapasFrame, "Gerar Extrato NF")

    def show_pdf(self):
        self.show_frame(GeradorPDFFaturaFrame, "Relatorio Detalhado")

    def show_relatorio_cnpj(self):
        self.show_frame(RelatorioCNPJFrame, "Relatorio CNPJ / PI")

    # ── Acoes globais ───────────────────────
    def anexar_mapa(self):
        path = filedialog.askopenfilename(
            title="Selecione o arquivo Excel do mapa",
            filetypes=[("Arquivos Excel", "*.xlsx *.xls")]
        )
        if not path:
            return
        ok, msg = validar_arquivo_excel(path)
        if not ok:
            messagebox.showerror("Arquivo invalido", msg)
            return
        self.arquivo_mapa = path
        self._sincronizar_frames()

    def selecionar_pasta_destino(self):
        path = filedialog.askdirectory(title="Selecione a pasta destino")
        if not path:
            return
        ok, msg = validar_pasta_destino(path)
        if not ok:
            messagebox.showerror("Pasta invalida", msg)
            return
        self.pasta_destino = path
        self._sincronizar_frames()

    def _sincronizar_frames(self):
        nome_mapa   = os.path.basename(self.arquivo_mapa)  if self.arquivo_mapa  else "—"
        nome_pasta  = os.path.basename(self.pasta_destino) if self.pasta_destino else "—"

        self.status_sidebar.configure(
            text=f"Mapa: {nome_mapa}\nDestino: {nome_pasta}"
        )

        for frame in self.frames.values():
            if hasattr(frame, "atualizar_arquivo_mapa") and self.arquivo_mapa:
                frame.atualizar_arquivo_mapa(self.arquivo_mapa)
            if hasattr(frame, "atualizar_pasta_destino") and self.pasta_destino:
                frame.atualizar_pasta_destino(self.pasta_destino)

        inicio = self.frames.get(InicioFrame)
        if inicio:
            inicio.atualizar_status(self.arquivo_mapa, self.pasta_destino)
            # Mostra aviso de pasta automatica se ainda nao foi escolhida manualmente
            if self.pasta_destino and not self.arquivo_mapa:
                inicio.mostrar_aviso_pasta_auto(self.pasta_destino)


if __name__ == "__main__":
    app = App()
    app.mainloop()
