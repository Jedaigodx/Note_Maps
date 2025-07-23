import customtkinter as ctk
from tkinter import filedialog
import os
from datetime import datetime
import pandas as pd
from fpdf import FPDF

class GeradorPDFFaturaFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.arquivo_mapa = None
        self.pasta_destino = os.path.join(os.path.expanduser("~"), "Downloads")
        self.status = None
        self.progress = None
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Gerador de PDF de Faturas", font=("Arial", 22, "bold")).pack(pady=20)
        ctk.CTkFrame(self, height=2, fg_color="gray").pack(fill="x", padx=30, pady=(0, 20))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="📂 Anexar Mapa", command=self.selecionar_arquivo, width=180, height=45).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="📁 Selecionar Pasta", command=self.selecionar_pasta, width=180, height=45).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="📤 Gerar PDF", command=self.gerar_pdf, width=180, height=45).pack(side="left", padx=10)

        self.progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=30, pady=10)
        self.progress.pack_forget()

        self.status = ctk.CTkLabel(self, text="📂 Selecione um mapa para gerar o PDF.", font=("Calibri", 14, "bold"), text_color="#1e7bc5")
        self.status.pack(pady=20)

    def selecionar_arquivo(self):
        path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.xls")])
        if path:
            self.arquivo_mapa = path
            self.status.configure(text=f"📄 Arquivo selecionado: {os.path.basename(path)}", text_color="#1E3A8A")

    def selecionar_pasta(self):
        folder = filedialog.askdirectory()
        if folder:
            self.pasta_destino = folder
            self.status.configure(text=f"📁 Pasta selecionada: {folder}", text_color="#1E3A8A")

    def gerar_pdf(self):
        if not self.arquivo_mapa:
            self.status.configure(text="❌ Por favor, selecione o arquivo mapa.", text_color="red")
            return
        self.progress.pack(fill="x", padx=30, pady=10)
        self.progress.start()
        self.status.configure(text="Gerando PDF...", text_color="#1E3A8A")
        self.update()

        try:
            df = pd.read_excel(self.arquivo_mapa)
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            for idx, row in df.head(10).iterrows():
                linha = " | ".join(str(x) for x in row.values)
                pdf.cell(0, 10, linha, ln=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"fatura_{timestamp}.pdf"
            caminho_completo = os.path.join(self.pasta_destino, nome_arquivo)
            pdf.output(caminho_completo)

            self.status.configure(text=f"✅ PDF salvo: {nome_arquivo}", text_color="green")
        except Exception as e:
            self.status.configure(text=f"❌ Erro: {str(e)}", text_color="red")
        finally:
            self.progress.stop()
            self.progress.pack_forget()
