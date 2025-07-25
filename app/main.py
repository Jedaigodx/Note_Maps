import customtkinter as ctk
from tkinter import filedialog
import os
from conversor import ConversorMapasFrame
from gerador_pdf import GeradorPDFFaturaFrame

# Cores 
BTN_FG = "#04573B"
BTN_HOVER = "#093828"
SIDEBAR_BG = "#0F172A"
CONTAINER_BG = "#1E293B"
SIDEBAR_BTN_FG = "#062F88"
SIDEBAR_BTN_HOVER = "#1D47A0"
SIDEBAR_BTN_ACTIVE = "#288ED3"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class InicioFrame(ctk.CTkFrame):
    def __init__(self, master, app=None):
        super().__init__(master)
        self.app = app

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        ctk.CTkLabel(main_frame, text="Sistema Administrativo - COPESP", 
                    font=("Arial", 26, "bold")).pack(pady=30)

        ctk.CTkLabel(main_frame, text="Selecione o arquivo do mapa (arquivo Excel) e a pasta onde serão salvos os resultados", 
                    font=("Arial", 16)).pack(pady=10)

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=20)

        ctk.CTkButton(button_frame, text="➕ ANEXAR MAPA",
                     command=self.app.anexar_mapa,
                     fg_color=BTN_FG,
                     hover_color=BTN_HOVER,
                     font=("Arial", 14, "bold"),
                     height=50,
                     width=180).pack(side="left", padx=10)

        ctk.CTkButton(button_frame, text="➕ SELECIONAR PASTA",
                     command=self.app.selecionar_pasta_destino,
                     fg_color=BTN_FG,
                     hover_color=BTN_HOVER,
                     font=("Arial", 14, "bold"),
                     height=50,
                     width=180).pack(side="left", padx=10)

        ctk.CTkLabel(main_frame, text="Escolha uma das opções ao lado para iniciar.", 
                    font=("Arial", 16)).pack(pady=10)

        self.status_label = ctk.CTkLabel(main_frame, text="", font=("Arial", 12), text_color="gray")
        self.status_label.pack(side="bottom", pady=10)

        ctk.CTkLabel(main_frame, text="Desenvolvido por Cb Pacífico", 
                    font=("Arial", 12, "italic"), 
                    text_color="gray").pack(side="bottom", pady=10)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Note Maps")
        self.geometry("950x650")
        self.resizable(True, True)

        self.arquivo_mapa = None
        self.pasta_destino = None

        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=SIDEBAR_BG)
        self.sidebar.pack(side="left", fill="y")

        self.container = ctk.CTkFrame(self, fg_color=CONTAINER_BG)
        self.container.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(self.sidebar, text="Menu", font=("Arial", 20, "bold")).pack(pady=20)

        ctk.CTkButton(self.sidebar, text="🏠 Início", 
                     command=self.show_inicio, 
                     fg_color=SIDEBAR_BTN_FG,
                     hover_color=SIDEBAR_BTN_HOVER,
                     font=("Arial",16, "bold"),
                     height=30).pack(fill="x", pady=(10,20), padx=15)

        ctk.CTkButton(self.sidebar, text="🧾 Gerar Extrato NF", 
                     command=self.show_conversor,
                     fg_color=SIDEBAR_BTN_ACTIVE,
                     hover_color=SIDEBAR_BTN_HOVER,
                     font=("Arial",14, "bold"),
                     height=30,anchor="w").pack(fill="x", pady=(5,7), padx=15)

        ctk.CTkButton(self.sidebar, text="📄 Gerar Relatório", 
                     command=self.show_pdf,
                     fg_color=SIDEBAR_BTN_ACTIVE,
                     hover_color=SIDEBAR_BTN_HOVER,
                     font=("Arial",14, "bold"),
                     height=30, 
                     anchor="w").pack(fill="x", pady=(5,10), padx=15)

        self.status_label = ctk.CTkLabel(self.sidebar, text="Nenhum arquivo anexado", font=("Arial", 10), text_color="gray")
        self.status_label.pack(side="bottom", pady=10, padx=10)
        
        self.frames = {}
        self.current_frame = None
        self.show_inicio()

        self.bind_all("<Control-1>", lambda e: self.show_inicio())
        self.bind_all("<Control-2>", lambda e: self.show_conversor())
        self.bind_all("<Control-3>", lambda e: self.show_pdf())

    def anexar_mapa(self):
        path = filedialog.askopenfilename(title="Selecione o arquivo Excel do mapa", filetypes=[("Excel files", "*.xlsx *.xls")])
        if path:
            self.arquivo_mapa = path
            self.status_label.configure(text=f"Arquivo mapa anexado: {os.path.basename(path)}")
            self.atualizar_frames_arquivo(path)

    def selecionar_pasta_destino(self):
        path = filedialog.askdirectory(title="Selecione a pasta destino")
        if path:
            self.pasta_destino = path
            self.status_label.configure(text=f"Pasta destino selecionada: {path}")
            self.atualizar_frames_pasta(path)

    def atualizar_frames_arquivo(self, path):
        for frame in self.frames.values():
            if hasattr(frame, 'atualizar_arquivo_mapa'):
                frame.atualizar_arquivo_mapa(path)

    def atualizar_frames_pasta(self, path):
        for frame in self.frames.values():
            if hasattr(frame, 'atualizar_pasta_destino'):
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
