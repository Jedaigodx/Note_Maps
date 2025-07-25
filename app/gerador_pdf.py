import pandas as pd
import customtkinter as ctk
from fpdf import FPDF
from tkinter import filedialog
import os

class PDFTabela(FPDF):
    def tabela(self, dados, colunas):
        usar_cnpj = dados['CNPJ'].notnull().any()
        usar_cpf = not usar_cnpj

        colunas_usadas = [c for c in colunas if c != 'CNPJ' and c != 'CPF']
        if usar_cnpj:
            colunas_usadas.insert(0, 'CNPJ')
        elif usar_cpf:
            colunas_usadas.insert(0, 'CPF')

        larguras = {
            'CNPJ': 25,
            'CPF': 25,
            'Guia': 12,
            'Plano Interno': 25,
            'enc titular': 45,
            'enc dependente': 45,
            'Valor': 22
        }

        if self.page_no() == 1:
            self.set_font("Arial", 'B', 12)
            self.set_fill_color(240, 240, 240)
            total_width = sum(larguras[c] for c in colunas_usadas)
            self.cell(total_width, 10, self.titulo, border=1, align='C', ln=True)
            self.ln(2)

        self.set_fill_color(230, 230, 230)
        self.set_font("Arial", 'B', 9)
        for col in colunas_usadas:
            self.cell(larguras[col], 8, col, border=1, align='C', fill=True)
        self.ln()

        self.set_font("Arial", '', 6)
        for _, row in dados.iterrows():
            for col in colunas_usadas:
                if col == 'Valor' and pd.notnull(row[col]):
                    texto = f"R$ {row[col]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                else:
                    texto = str(row[col])[:40] if pd.notnull(row[col]) else ''
                self.cell(larguras[col], 8, texto, border=1)
            self.ln()

        total_valor = dados['Valor'].sum()
        self.set_font("Arial", 'B', 8)
        total_texto = f"R$ {total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        largura_total = sum(larguras[col] for col in colunas_usadas[:-1])
        self.cell(largura_total, 8, "Total", border=1, align='C')
        self.cell(larguras['Valor'], 8, total_texto, border=1, align='C')
        self.ln()

class GeradorPDFFaturaFrame(ctk.CTkFrame):
    COLUNAS_EXIBIR = ['CNPJ', 'CPF', 'Guia', 'Plano Interno', 'enc titular', 'enc dependente', 'Valor']

    def __init__(self, master, app=None):
        super().__init__(master)
        self.app = app

        self.df = None
        self.faturas_unicas = []
        self.selected_faturas = []

        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="Gerador de PDF por Fatura", font=("Arial", 22, "bold")).pack(pady=20)

        self.check_frame = ctk.CTkScrollableFrame(self, height=200)
        self.check_frame.pack(pady=5)
        self.checkboxes = []

        ctk.CTkLabel(self, text="Plano Interno:").pack(pady=10)
        self.plano_combo = ctk.CTkComboBox(self, values=[], state='disabled')
