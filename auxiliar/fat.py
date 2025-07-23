import pandas as pd
import customtkinter as ctk
from fpdf import FPDF

# Inicializar o tema
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Caminho do Excel
caminho_excel = "GuiasOCSPSA_437467S-2024.xlsx"
df = pd.read_excel(caminho_excel, sheet_name="Sheet1")

# Obter faturas únicas
faturas_unicas = sorted(df['Fatura'].dropna().unique())

# Classe PDF
class PDFTabela(FPDF):
    def tabela(self, dados, colunas):
        # Verifica se usa CNPJ ou CPF
        usar_cnpj = dados['CNPJ'].notnull().any()
        usar_cpf = not usar_cnpj

        # Remove a coluna não usada
        colunas_usadas = [c for c in colunas if c != 'CNPJ' and c != 'CPF']
        if usar_cnpj:
            colunas_usadas.insert(0, 'CNPJ')
        elif usar_cpf:
            colunas_usadas.insert(0, 'CPF')

        # Larguras
        larguras = {
            'CNPJ': 25,
            'CPF': 25,
            'Guia': 12,
            'Plano Interno': 25,
            'enc titular': 45,
            'enc dependente': 45,
            'Valor': 22
        }

        # Cabeçalho (apenas na primeira página)
        if self.page_no() == 1:
            self.set_font("Arial", 'B', 12)
            self.set_fill_color(240, 240, 240)
            total_width = sum(larguras[c] for c in colunas_usadas)
            self.cell(total_width, 10, self.titulo, border=1, align='C', ln=True)
            self.ln(2)

        # Título da tabela
        self.set_fill_color(230, 230, 230)
        self.set_font("Arial", 'B', 9)
        for col in colunas_usadas:
            self.cell(larguras[col], 8, col, border=1, align='C', fill=True)
        self.ln()

        # Conteúdo
        self.set_font("Arial", '', 6)
        for _, row in dados.iterrows():
            for col in colunas_usadas:
                if col == 'Valor' and pd.notnull(row[col]):
                    texto = f"R$ {row[col]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                else:
                    texto = str(row[col])[:40] if pd.notnull(row[col]) else ''
                self.cell(larguras[col], 8, texto, border=1)
            self.ln()

        # Totalizador
        total_valor = dados['Valor'].sum()
        self.set_font("Arial", 'B', 8)
        total_texto = f"R$ {total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        largura_total = sum(larguras[col] for col in colunas_usadas[:-1])
        self.cell(largura_total, 8, "Total", border=1, align='C')
        self.cell(larguras['Valor'], 8, total_texto, border=1, align='C',)
        self.ln()

# GUI principal
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gerador de PDF por Fatura")
        self.geometry("500x600")

        ctk.CTkLabel(self, text="Selecione as Faturas:").pack(pady=10)
        self.checkboxes = []
        self.selected_faturas = []

        # Frame para checkboxes de faturas
        self.check_frame = ctk.CTkScrollableFrame(self, height=200)
        self.check_frame.pack(pady=5)

        for fat in faturas_unicas:
            cb = ctk.CTkCheckBox(self.check_frame, text=str(int(fat)), command=self.atualizar_planos)
            cb.pack(anchor='w')
            self.checkboxes.append((fat, cb))

        # Plano interno combobox
        ctk.CTkLabel(self, text="Plano Interno:").pack(pady=10)
        self.plano_combo = ctk.CTkComboBox(self, values=[], state='disabled')
        self.plano_combo.pack()

        # Botão gerar PDF
        self.gerar_btn = ctk.CTkButton(self, text="Gerar PDF", command=self.gerar_pdf, state='disabled')
        self.gerar_btn.pack(pady=30)

    def atualizar_planos(self):
        self.selected_faturas = [fat for fat, cb in self.checkboxes if cb.get()]
        if not self.selected_faturas:
            self.plano_combo.configure(values=[], state='disabled')
            self.gerar_btn.configure(state='disabled')
            return

        # Filtrar Planos Internos com base nas faturas selecionadas
        planos = df[df['Fatura'].isin(self.selected_faturas)]['Plano Interno'].dropna().unique()
        planos_ordenados = sorted(planos)
        self.plano_combo.configure(values=planos_ordenados, state='normal')
        if planos_ordenados:
            self.plano_combo.set(planos_ordenados[0])
        self.gerar_btn.configure(state='normal')

    def gerar_pdf(self):
        plano = self.plano_combo.get()
        if not plano:
            ctk.CTkLabel(self, text="Selecione um Plano Interno válido.", text_color="red").pack()
            return

        # Filtragem dos dados
        dados_filtrados = df[
            (df['Fatura'].isin(self.selected_faturas)) &
            (df['Plano Interno'] == plano)
        ]

        if dados_filtrados.empty:
            ctk.CTkLabel(self, text="Nenhum dado encontrado com os filtros!", text_color="red").pack()
            return

        nome_clinica = str(dados_filtrados['Nome'].iloc[0])
        colunas_exibir = ['CNPJ', 'CPF', 'Guia', 'Plano Interno', 'enc titular', 'enc dependente', 'Valor']

        pdf = PDFTabela()
        pdf.titulo = nome_clinica
        pdf.add_page()
        pdf.tabela(dados_filtrados, colunas_exibir)

        nome_arquivo = f"Fatura_{'_'.join(map(str, map(int, self.selected_faturas)))}_{plano}.pdf"
        pdf.output(nome_arquivo)

        ctk.CTkLabel(self, text=f"✅ PDF gerado: {nome_arquivo}", text_color="green").pack()

# Rodar app
if __name__ == "__main__":
    app = App()
    app.mainloop()