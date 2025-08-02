import customtkinter as ctk
from tkinter import filedialog
import os
from conversor import ConversorMapasFrame
from gerador_pdf import GeradorPDFFaturaFrame

# Cores
BTN_FG = "#0B8052"
BTN_HOVER = "#0E9E66"
SIDEBAR_BG = "#0F172A"
CONTAINER_BG = "#1E293B"
SIDEBAR_BTN_FG = "#134E8B"
SIDEBAR_BTN_HOVER = "#1D67B5"
SIDEBAR_BTN_ACTIVE = "#288ED3"
TEXT_COLOR_GRAY = "#A0A0A0"
HEADER_COLOR = "#E0E0E0"

# Configuração do tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class InicioFrame(ctk.CTkFrame):
    def __init__(self, master, app=None):
        super().__init__(master)
        self.app = app

        self.columnconfigure((0, 1), weight=1)
        self.rowconfigure((0,1,2,3,4), weight=1)

        titulo = ctk.CTkLabel(
            self, 
            text="Sistema Administrativo - COPESP",
            font=("Segoe UI", 30, "bold"),
            text_color=HEADER_COLOR
        )
        titulo.grid(row=0, column=0, columnspan=2, pady=(30,10))

        subtitulo = ctk.CTkLabel(
            self,
            text="Selecione o arquivo do mapa (.xlsx) e a pasta onde serão salvos os resultados.",
            font=("Segoe UI", 16),
            wraplength=600,
            justify="center",
            text_color=TEXT_COLOR_GRAY
        )
        subtitulo.grid(row=1, column=0, columnspan=2, pady=(20, 10), padx=20)

        btn_anexar = ctk.CTkButton(
            self,
            text="➕ Anexar Mapa",
            command=self.app.anexar_mapa,
            fg_color=BTN_FG,
            hover_color=BTN_HOVER,
            font=("Segoe UI", 18, "bold"),
            width=180,
            height=60,
            corner_radius=10
        )
        btn_anexar.grid(row=2, column=0, padx=30, sticky="e")

        btn_pasta = ctk.CTkButton(
            self,
            text="📁 Selecionar Pasta",
            command=self.app.selecionar_pasta_destino,
            fg_color=BTN_FG,
            hover_color=BTN_HOVER,
            font=("Segoe UI", 18, "bold"),
            width=180,
            height=60,
            corner_radius=10
        )
        btn_pasta.grid(row=2, column=1, padx=30, sticky="w")

        info = ctk.CTkLabel(
            self,
            text="Escolha uma das opções ao lado para iniciar.",
            font=("Segoe UI", 16),
            text_color=TEXT_COLOR_GRAY
        )
        info.grid(row=3, column=0, columnspan=2, pady=20)

        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 14),
            text_color=TEXT_COLOR_GRAY
        )
        self.status_label.grid(row=4, column=0, columnspan=2, pady=(0,10))

        rodape = ctk.CTkLabel(
            self,
            text="Desenvolvido por Cb Pacífico",
            font=("Segoe UI", 12, "italic"),
            text_color=TEXT_COLOR_GRAY
        )
        rodape.grid(row=5, column=0, columnspan=2, pady=(10,30))

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Note Maps - COPESP")
        self.geometry("970x700")
        self.minsize(950, 650)
        self.configure(bg=SIDEBAR_BG)

        self.arquivo_mapa = None
        self.pasta_destino = None

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=260, fg_color=SIDEBAR_BG)
        self.sidebar.pack(side="left", fill="y")

        # Container principal
        self.container = ctk.CTkFrame(self, fg_color=CONTAINER_BG)
        self.container.pack(side="right", fill="both", expand=True)

        # Título Sidebar
        ctk.CTkLabel(
            self.sidebar,
            text="Menu Principal",
            font=("Segoe UI", 26, "bold"),
            pady=30,
            text_color=HEADER_COLOR
        ).pack()

        # Função para criar botões da sidebar
        def criar_botao_sidebar(texto, comando, ativo=False):
            cor_fundo = SIDEBAR_BTN_ACTIVE if ativo else SIDEBAR_BTN_FG
            return ctk.CTkButton(
                self.sidebar,
                text=texto,
                command=comando,
                fg_color=cor_fundo,
                hover_color=SIDEBAR_BTN_HOVER,
                font=("Segoe UI", 17 if ativo else 14, "bold"),
                height=40,
                anchor="w",
                corner_radius=12
            )

        ctk.CTkButton(
            self.sidebar,
            text="🏠 Início",
            command=self.show_inicio,
            fg_color=SIDEBAR_BTN_ACTIVE,          
            hover_color=SIDEBAR_BTN_HOVER,        
            text_color="#ffffff",         
            font=("Segoe UI", 18, "bold"),
            height=38,                    
            corner_radius=7,             
            border_width=0.5,               
            border_color=CONTAINER_BG,       
            anchor="center",              
            )\
        .pack(fill="x", pady=(10,20), padx=15)

        ctk.CTkButton(self.sidebar, text="🧾 Gerar Extrato NF", 
            command=self.show_conversor,
            fg_color=SIDEBAR_BTN_ACTIVE,           
            hover_color=SIDEBAR_BTN_HOVER,        
            text_color="#ffffff",         
            font=("Segoe UI", 18, "bold"),
            height=38,                    
            corner_radius=7,            
            border_width=2,               
            border_color=CONTAINER_BG,       
            anchor="center",              
            )\
        .pack(fill="x", pady=(5,7), padx=15)

        ctk.CTkButton(self.sidebar, text="📄 Relatório Detalhado", 
            command=self.show_pdf,
            fg_color=SIDEBAR_BTN_ACTIVE,           
            hover_color=SIDEBAR_BTN_HOVER,        
            text_color="#ffffff",         
            font=("Segoe UI", 18, "bold"),
            height=38,                    
            corner_radius=7,            
            border_width=2,               
            border_color=CONTAINER_BG,       
            anchor="center",              
            )\
        .pack(fill="x", pady=(5,7), padx=15)

        ctk.CTkFrame( self.sidebar,height=2,fg_color=CONTAINER_BG,  corner_radius=1).pack(fill="x", padx=24, pady=12)
        
        self.status_label = ctk.CTkLabel(
            self.sidebar,
            text="Nenhum arquivo anexado",
            font=("Segoe UI", 12),
            text_color=TEXT_COLOR_GRAY,
            wraplength=220,
            justify="center"
        )
        self.status_label.pack(side="bottom", pady=20, padx=20)

        self.frames = {}
        self.current_frame = None
        self.show_inicio()

        # Atalhos de teclado para trocar telas
        self.bind_all("<Control-1>", lambda e: self.show_inicio())
        self.bind_all("<Control-2>", lambda e: self.show_conversor())
        self.bind_all("<Control-3>", lambda e: self.show_pdf())

    def anexar_mapa(self):
        path = filedialog.askopenfilename(
            title="Selecione o arquivo Excel do mapa",
            filetypes=[("Arquivos Excel", "*.xlsx *.xls")]
        )
        if path:
            self.arquivo_mapa = path
            self.status_label.configure(text=f"Arquivo mapa anexado:\n{os.path.basename(path)}")
            self.atualizar_frames_arquivo(path)

    def selecionar_pasta_destino(self):
        path = filedialog.askdirectory(title="Selecione a pasta destino")
        if path:
            self.pasta_destino = path
            self.status_label.configure(text=f"Pasta destino selecionada:\n{path}")
            self.atualizar_frames_pasta(path)

    def atualizar_frames_arquivo(self, path):
        for frame in self.frames.values():
            if hasattr(frame, "atualizar_arquivo_mapa"):
                frame.atualizar_arquivo_mapa(path)

    def atualizar_frames_pasta(self, path):
        for frame in self.frames.values():
            if hasattr(frame, "atualizar_pasta_destino"):
                frame.atualizar_pasta_destino(path)

    def show_frame(self, frame_class):
        if frame_class not in self.frames:
            frame = frame_class(self.container, app=self)
            self.frames[frame_class] = frame
            frame.pack(fill="both", expand=True)
        if self.current_frame:
            self.current_frame.pack_forget()
        self.current_frame = self.frames[frame_class]
        self.current_frame.pack(fill="both", expand=True)

    def show_inicio(self):
        self.show_frame(InicioFrame)

    def show_conversor(self):
        self.show_frame(ConversorMapasFrame)

    def show_pdf(self):
        self.show_frame(GeradorPDFFaturaFrame)

if __name__ == "__main__":
    app = App()
    app.mainloop()
