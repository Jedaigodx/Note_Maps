import pandas as pd
import customtkinter as ctk
from fpdf import FPDF
from tkinter import filedialog

class PDFTabela(FPDF):
    def tabela(self, dados, colunas):
        usar_cnpj = dados['CNPJ'].apply(lambda x: str(x).strip() not in ["", "0", "nan", "None"]).any()
        usar_cpf = not usar_cnpj

        colunas_usadas = [c for c in colunas if c != 'CNPJ' and c != 'CPF']
        if usar_cnpj:
            colunas_usadas.insert(0, 'CNPJ')
        elif usar_cpf:
            colunas_usadas.insert(0, 'CPF')

        larguras = {
            'CNPJ': 22,
            'CPF': 22,
            'Guia': 12,
            'Plano Interno': 22,
            'Fatura': 12,
            'enc titular': 50,
            'enc dependente': 50,
            'Valor': 20
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
    def __init__(self, master, app=None):
        super().__init__(master)
        self.app = app
        self.df = None
        self.faturas_unicas = []
        self.selected_faturas = []
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="Relatório financeiro", font=("Arial", 22, "bold")).pack(pady=20)

        # Frame horizontal para checkboxes + botão limpar
        self.check_filtros_frame = ctk.CTkFrame(self)
        self.check_filtros_frame.pack(pady=5)

        self.check_frame = ctk.CTkScrollableFrame(self.check_filtros_frame, height=250, width=200)
        self.check_frame.pack(side='left', padx=(0, 10))

        self.limpar_btn = ctk.CTkButton(self.check_filtros_frame, text="Limpar", command=self.limpar_filtros)
        self.limpar_btn.pack(side='left', pady=5)

        self.checkboxes = []

        ctk.CTkLabel(self, text="Plano Interno:").pack(pady=10)
        self.plano_combo = ctk.CTkComboBox(self, values=[], state='disabled')
        self.plano_combo.pack()

        self.gerar_btn = ctk.CTkButton(self, text="Gerar PDF", command=self.gerar_pdf, state='disabled')
        self.gerar_btn.pack(pady=30)

        self.status = ctk.CTkLabel(self, text="", text_color="green")
        self.status.pack()

    def carregar_excel(self):
        if self.app and self.app.arquivo_mapa:
            caminho_excel = self.app.arquivo_mapa
        else:
            caminho_excel = filedialog.askopenfilename(title="Selecione o arquivo Excel", filetypes=[("Excel files", "*.xlsx *.xls")])
            if self.app:
                self.app.arquivo_mapa = caminho_excel

        if not caminho_excel:
            self.status.configure(text="Arquivo Excel não selecionado.", text_color="red")
            return

        try:
            self.df = pd.read_excel(caminho_excel, sheet_name="Sheet1")
            self.faturas_unicas = sorted(self.df['Fatura'].dropna().unique())
        except Exception as e:
            self.status.configure(text=f"Erro ao ler arquivo: {str(e)}", text_color="red")
            return

        for _, cb in self.checkboxes:
            if cb.winfo_exists():
                cb.destroy()
        self.checkboxes.clear()

        for fat in self.faturas_unicas:
            cb = ctk.CTkCheckBox(self.check_frame, text=str(int(fat)), command=self.atualizar_planos)
            cb.pack(anchor='w')
            self.checkboxes.append((fat, cb))

        self.plano_combo.configure(values=[], state='disabled')
        self.gerar_btn.configure(state='disabled')
        self.status.configure(text="Arquivo carregado com sucesso.", text_color="green")

    def atualizar_planos(self):
        self.selected_faturas = [fat for fat, cb in self.checkboxes if cb.get()]
        if not self.selected_faturas:
            self.plano_combo.configure(values=[], state='disabled')
            self.gerar_btn.configure(state='disabled')
            return

        planos = self.df[self.df['Fatura'].isin(self.selected_faturas)]['Plano Interno'].dropna().unique()
        planos_ordenados = sorted(planos)   
        self.plano_combo.configure(values=planos_ordenados, state='normal')
        if planos_ordenados:
            self.plano_combo.set(planos_ordenados[0])
        self.gerar_btn.configure(state='normal')

    def gerar_pdf(self):
        if self.df is None:
            self.status.configure(text="Nenhum arquivo Excel carregado.", text_color="red")
            return

        plano = self.plano_combo.get()
        if not plano:
            self.status.configure(text="Selecione um Plano Interno válido.", text_color="red")
            return

        dados_filtrados = self.df[(self.df['Fatura'].isin(self.selected_faturas)) & (self.df['Plano Interno'] == plano)]
        dados_filtrados = dados_filtrados.sort_values(by='Fatura')

        if dados_filtrados.empty:
            self.status.configure(text="Nenhum dado encontrado com os filtros!", text_color="red")
            return

        nome_clinica = str(dados_filtrados['Nome'].iloc[0])
        colunas_exibir = ['CNPJ', 'CPF', 'Guia', 'Fatura', 'Plano Interno', 'enc titular', 'enc dependente', 'Valor']

        pdf = PDFTabela()
        pdf.titulo = nome_clinica
        pdf.add_page()
        pdf.tabela(dados_filtrados, colunas_exibir)

        pasta_destino = self.app.pasta_destino if (self.app and self.app.pasta_destino) else None
        nome_arquivo = f"Fatura_{'_'.join(map(str, map(int, self.selected_faturas)))}_{plano}.pdf"
        caminho_arquivo = nome_arquivo

        if pasta_destino:
            import os
            caminho_arquivo = os.path.join(pasta_destino, nome_arquivo)

        try:
            pdf.output(caminho_arquivo)
            self.status.configure(text=f"✅ PDF gerado: {caminho_arquivo}", text_color="green")
        except Exception as e:
            self.status.configure(text=f"Erro ao salvar PDF: {str(e)}", text_color="red")

    def limpar_filtros(self):
        for _, cb in self.checkboxes:
            cb.deselect()   
        self.atualizar_planos()

    def atualizar_arquivo_mapa(self, caminho):
        self.app.arquivo_mapa = caminho
        self.status.configure(text=f"Arquivo mapa anexado: {caminho}", text_color="green")
        self.after(100, self.carregar_excel)

    def atualizar_pasta_destino(self, caminho):
        self.app.pasta_destino = caminho
        self.status.configure(text=f"Pasta destino definida: {caminho}", text_color="green")
