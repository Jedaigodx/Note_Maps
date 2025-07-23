import customtkinter as ctk
import pandas as pd
from tkinter import filedialog
from fpdf import FPDF
import os
from datetime import datetime

# Configurações iniciais
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Dados compartilhados
shared_data = {
    "arquivo_mapa": None,
    "pasta_destino": None,
    "df_mapa": None
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema Administrativo - COPESP")
        self.geometry("950x650")
        self.resizable(False, False)

        # Solicita os dados iniciais
        self.anexar_mapa()
        self.selecionar_pasta_destino()

        # Layout principal
        self.sidebar = ctk.CTkFrame(self, width=200, fg_color="#0F172A")
        self.sidebar.pack(side="left", fill="y")

        self.container = ctk.CTkFrame(self, fg_color="#1E293B")
        self.container.pack(side="right", expand=True, fill="both")

        # Botões do menu lateral
        ctk.CTkLabel(self.sidebar, text="Menu", font=("Arial", 20, "bold")).pack(pady=20)
        ctk.CTkButton(self.sidebar, text="🏠 Início", command=self.show_inicio).pack(fill="x", pady=5, padx=10)
        ctk.CTkButton(self.sidebar, text="🧾 Conversor de Mapas", command=self.show_conversor).pack(fill="x", pady=5, padx=10)
        ctk.CTkButton(self.sidebar, text="📄 Gerador de PDF", command=self.show_pdf_generator).pack(fill="x", pady=5, padx=10)

        # Frames para cada página
        self.frames = {}
        for FrameClass in (InicioFrame, ConversorMapasFrame, GeradorPDFFaturaFrame):
            frame = FrameClass(self.container, self)
            self.frames[FrameClass] = frame
            frame.pack_forget()

        self.show_inicio()

    def show_inicio(self):
        self._switch_frame(InicioFrame)

    def show_conversor(self):
        self._switch_frame(ConversorMapasFrame)

    def show_pdf_generator(self):
        self._switch_frame(GeradorPDFFaturaFrame)

    def _switch_frame(self, frame_class):
        for f in self.frames.values():
            f.pack_forget()
        self.frames[frame_class].pack(fill="both", expand=True)

    def anexar_mapa(self):
        file_path = filedialog.askopenfilename(title="Selecione o mapa (xlsx)", filetypes=[("Excel", "*.xlsx *.xls")])
        if file_path:
            shared_data["arquivo_mapa"] = file_path
            shared_data["df_mapa"] = pd.read_excel(file_path)
        else:
            self.destroy()

    def selecionar_pasta_destino(self):
        folder = filedialog.askdirectory(title="Selecione a pasta de destino")
        if folder:
            shared_data["pasta_destino"] = folder
        else:
            self.destroy()

# Frames reaproveitam shared_data
# ... (o resto permanece igual ao que você já tem para ConversorMapasFrame e GeradorPDFFaturaFrame)

if __name__ == "__main__":
    app = App()
    app.mainloop()
