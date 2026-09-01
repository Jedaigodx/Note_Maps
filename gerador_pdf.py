import pandas as pd
import customtkinter as ctk
from fpdf import FPDF
from tkinter import filedialog, messagebox
import os
import re

# Cores
BTN_FG            = "#0B8052"
BTN_HOVER         = "#0E9E66"
TEXT_COLOR_GRAY   = "#A0A0A0"
HEADER_COLOR      = "#FFFFFF"
SIDEBAR_BTN_FG    = "#134E8B"
SIDEBAR_BTN_HOVER = "#1D67B5"
ACCENT            = "#0E9E66"

def _latin1(texto):
    """Converte strings com caracteres perigosos para Latin-1 evitando erros no FPDF."""
    if pd.isna(texto): return ""
    s = str(texto)
    return s.encode("latin-1", errors="replace").decode("latin-1")

def _linhas_multicell(pdf, texto, largura, padding=2):
    """Calcula quantas linhas o multi_cell vai realmente desenhar, usando a largura
    real dos caracteres na fonte atualmente selecionada no pdf (em vez de uma
    estimativa fixa de 'caracteres por mm'). Isso evita que a altura da linha seja
    subestimada e o texto seja cortado/quebrado de forma inesperada."""
    largura_util = max(largura - padding, 1)
    linhas = 1
    linha_atual = ""
    for palavra in str(texto).split(" "):
        candidato = f"{linha_atual} {palavra}".strip()
        if pdf.get_string_width(candidato) <= largura_util:
            linha_atual = candidato
        else:
            linhas += 1
            linha_atual = palavra
    return max(1, linhas)

def _truncar_para_largura(pdf, texto, largura, padding=2):
    """Trunca um texto de coluna que não deve quebrar linha (ex: código, CNPJ),
    adicionando reticências, em vez de deixá-lo sobrepor a célula vizinha ou ser
    dividido no meio por um multi_cell."""
    texto = str(texto)
    largura_util = max(largura - padding, 1)
    if pdf.get_string_width(texto) <= largura_util:
        return texto
    base = texto
    while base and pdf.get_string_width(base + "...") > largura_util:
        base = base[:-1]
    return f"{base}..." if base else texto[:1]

COLUNAS_PDF = ["CNPJ", "CPF", "Guia", "Fatura", "Plano Interno",
               "enc titular", "enc dependente", "Valor"]

# Larguras em mm ajustadas para o formato paisagem (~277mm de área útil)
LARGURAS = {
    "CNPJ": 25, "CPF": 25, "Guia": 15, "Fatura": 15, "Plano Interno": 32,
    "enc titular": 77, "enc dependente": 77, "Valor": 25
}

class _PDFTabela(FPDF):
    """Gerador de PDF com tabela formatada ajustável para quebras de linha."""
    titulo: str = ""

    def header(self): pass

    def tabela(self, dados: pd.DataFrame, colunas_disponiveis: list[str]):
        usa_cnpj = dados["CNPJ"].apply(lambda x: str(x).strip() not in ["", "0", "nan", "None"]).any()
        id_col = "CNPJ" if usa_cnpj else "CPF"

        colunas_usadas = [c for c in colunas_disponiveis if c not in ("CNPJ", "CPF")]
        colunas_usadas.insert(0, id_col)
        colunas_usadas = [c for c in colunas_usadas if c in dados.columns or c in ("CNPJ", "CPF")]

        larguras_usadas = {c: LARGURAS.get(c, 20) for c in colunas_usadas}
        total_width = sum(larguras_usadas.values())

        if self.page_no() == 1:
            self.set_font("Arial", "B", 12)
            self.set_fill_color(240, 240, 240)
            self.cell(total_width, 10, _latin1(self.titulo[:100]), border=1, align="C", ln=True, fill=True)
            self.ln(2)

        def desenhar_cabecalho():
            self.set_fill_color(230, 230, 230)
            self.set_font("Arial", "B", 9)
            for col in colunas_usadas:
                self.cell(larguras_usadas[col], 8, _latin1(col), border=1, align="C", fill=True)
            self.ln()

        desenhar_cabecalho()
        self.set_font("Arial", "", 7)
        ROW_H = 6

        # Apenas colunas de texto livre (nomes) podem quebrar em mais de uma linha.
        # Códigos e identificadores (CNPJ/CPF, Guia, Fatura, Plano Interno) nunca
        # devem ser divididos no meio por um multi_cell.
        COLUNAS_WRAP = {"enc titular", "enc dependente"}

        for _, row in dados.iterrows():
            # Coleta os textos para descobrir a altura máxima da linha
            textos = {}
            max_linhas = 1
            for col in colunas_usadas:
                val = row.get(col, "")
                if col == "Valor" and pd.notnull(val):
                    try:
                        texto = f"R$ {float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    except:
                        texto = str(val)
                else:
                    texto = str(val) if pd.notnull(val) else ""
                    if texto.strip().lower() in ["nan", "none"]: texto = "-"

                texto = _latin1(texto)
                textos[col] = texto

                if col in COLUNAS_WRAP:
                    # Quantidade real de linhas que o multi_cell vai desenhar nesta
                    # fonte/largura (medida com get_string_width, não estimada)
                    linhas_necessarias = _linhas_multicell(self, texto, larguras_usadas[col])
                else:
                    linhas_necessarias = 1
                if linhas_necessarias > max_linhas:
                    max_linhas = linhas_necessarias

            h = max_linhas * ROW_H
            if self.get_y() + h > self.page_break_trigger:
                self.add_page()
                desenhar_cabecalho()
                # BUGFIX: desenhar_cabecalho() deixa a fonte em Arial Bold 9 (usada no
                # cabeçalho da tabela). Sem este reset, todas as linhas de dados da
                # página seguinte eram desenhadas em negrito/tamanho maior, o que
                # fazia textos como "D8SAFUSCONS" não caberem mais na coluna e serem
                # quebrados no meio (ex.: "D8SAFUSCON" / "S") — este era o defeito
                # relatado, visível a partir da 2ª página do relatório.
                self.set_font("Arial", "", 7)

            x0 = self.get_x()
            y0 = self.get_y()

            for col in colunas_usadas:
                w = larguras_usadas[col]
                texto = textos[col]
                x_atual = self.get_x()

                if col in COLUNAS_WRAP:
                    self.set_xy(x_atual, y0)
                    self.multi_cell(w, ROW_H, texto, border=1, align="L")
                else:
                    self.set_xy(x_atual, y0)
                    alinhamento = "R" if col == "Valor" else "C"
                    # Colunas de código/valor nunca quebram: se não couberem na
                    # largura da coluna, são truncadas com reticências em vez de
                    # sobrepor a célula vizinha.
                    texto_exibido = texto if col == "Valor" else _truncar_para_largura(self, texto, w)
                    self.cell(w, h, texto_exibido, border=1, align=alinhamento)
                self.set_xy(x_atual + w, y0)

            self.set_xy(x0, y0 + h)

        try:
            total_valor = pd.to_numeric(dados["Valor"], errors="coerce").sum()
            total_texto = f"R$ {total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            total_texto = "—"

        self.set_font("Arial", "B", 8)
        largura_ate_valor = sum(larguras_usadas[c] for c in colunas_usadas if c != "Valor")
        self.cell(largura_ate_valor, 8, "TOTAL", border=1, align="C", fill=True)
        self.cell(larguras_usadas.get("Valor", 20), 8, total_texto, border=1, align="R", fill=True)
        self.ln()


class GeradorPDFFaturaFrame(ctk.CTkFrame):
    def __init__(self, master, app=None):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.df: pd.DataFrame | None = None
        self.faturas_repetidas: list = []
        self.selected_faturas: list = []
        self._build_ui()
        if self.app and self.app.arquivo_mapa:
            self.after(200, self._carregar_excel)

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="Relatório Financeiro Detalhado", font=("Segoe UI", 28, "bold"), text_color=HEADER_COLOR
        ).pack(pady=(30, 20))

        ctk.CTkFrame(self, height=2, fg_color="#444444").pack(fill="x", padx=30, pady=(0, 20))

        area = ctk.CTkFrame(self, fg_color="#222222", corner_radius=10)
        area.pack(pady=5, padx=30, fill="both", expand=True)

        self.check_frame = ctk.CTkScrollableFrame(area, height=250, width=300, fg_color="transparent")
        self.check_frame.pack(side="left", padx=(10, 10), pady=10, fill="y")

        ctrl_frame = ctk.CTkFrame(area, fg_color="transparent")
        ctrl_frame.pack(side="left", padx=10, pady=10, fill="y")

        ctk.CTkButton(
            ctrl_frame, text="Limpar Filtros", command=self._limpar_filtros, font=("Segoe UI", 14, "bold"),
            text_color=HEADER_COLOR, fg_color=SIDEBAR_BTN_FG, hover_color=SIDEBAR_BTN_HOVER, corner_radius=6
        ).pack(pady=(20, 10))

        self.checkboxes: list = []

        ctk.CTkLabel(ctrl_frame, text="Plano Interno:", text_color=TEXT_COLOR_GRAY).pack(pady=(10, 0))
        self.plano_combo = ctk.CTkComboBox(ctrl_frame, values=[], state="disabled", width=200)
        self.plano_combo.pack(pady=(5, 20))

        self.gerar_btn = ctk.CTkButton(
            ctrl_frame, text="📄 Gerar PDF", command=self._gerar_pdf, state="disabled", font=("Segoe UI", 16, "bold"),
            text_color=HEADER_COLOR, fg_color=BTN_FG, hover_color=BTN_HOVER, height=45
        )
        self.gerar_btn.pack(pady=10)

        self.status = ctk.CTkLabel(ctrl_frame, text="", text_color=ACCENT, font=("Segoe UI", 12))
        self.status.pack()

    def atualizar_arquivo_mapa(self, caminho: str):
        if self.app:
            self.app.arquivo_mapa = caminho
        self.after(100, self._carregar_excel)

    def atualizar_pasta_destino(self, caminho: str):
        if self.app:
            self.app.pasta_destino = caminho

    def _carregar_excel(self):
        caminho = self.app.arquivo_mapa if self.app else None
        if not caminho: return

        try:
            xl = pd.ExcelFile(caminho)
            aba = "Sheet1" if "Sheet1" in xl.sheet_names else xl.sheet_names[0]
            self.df = pd.read_excel(caminho, sheet_name=aba)

            for col in ("CNPJ", "CPF"):
                if col not in self.df.columns:
                    self.df[col] = ""

            usa_cnpj = self.df["CNPJ"].apply(lambda x: str(x).strip() not in ["", "0", "nan", "None"]).any()
            id_col = "CNPJ" if usa_cnpj else "CPF"

            grupo = self.df.groupby(["Fatura", id_col]).size().reset_index()
            self.faturas_repetidas = [(row["Fatura"], row[id_col]) for _, row in grupo.iterrows()]
        except Exception as e:
            self.status.configure(text=f"❌ Erro ao ler: {e}", text_color="red")
            return

        for widget in self.check_frame.winfo_children(): widget.destroy()
        self.checkboxes.clear()

        ctk.CTkLabel(
            self.check_frame, text="Fatura – CNPJ/CPF", font=("Segoe UI", 14, "bold"), text_color="#60A5FA"
        ).pack(anchor="w", pady=(0, 10))

        for fat, id_val in self.faturas_repetidas:
            try: texto_cb = f"{int(float(str(fat)))} - {id_val}"
            except: texto_cb = f"{fat} - {id_val}"
            cb = ctk.CTkCheckBox(self.check_frame, text=texto_cb, command=self._atualizar_planos, fg_color=BTN_FG)
            cb.pack(anchor="w", pady=2)
            self.checkboxes.append(((fat, id_val), cb))

        self.plano_combo.configure(values=[], state="disabled")
        self.gerar_btn.configure(state="disabled")
        self.status.configure(text=f"✅ Arquivo carregado", text_color=ACCENT)

    def _atualizar_planos(self):
        self.selected_faturas = [fk for fk, cb in self.checkboxes if cb.get()]
        if not self.selected_faturas:
            self.plano_combo.configure(values=[], state="disabled")
            self.gerar_btn.configure(state="disabled")
            return

        usa_cnpj = self.df["CNPJ"].apply(lambda x: str(x).strip() not in ["", "0", "nan", "None"]).any()
        id_col = "CNPJ" if usa_cnpj else "CPF"

        filtro = pd.Series(False, index=self.df.index)
        for fat, id_val in self.selected_faturas:
            filtro |= (self.df["Fatura"] == fat) & (self.df[id_col] == id_val)

        planos = sorted(self.df.loc[filtro, "Plano Interno"].dropna().unique())
        self.plano_combo.configure(values=planos, state="normal")
        if planos: self.plano_combo.set(planos[0])
        self.gerar_btn.configure(state="normal")

    def _limpar_filtros(self):
        for _, cb in self.checkboxes: cb.deselect()
        self._atualizar_planos()

    def _gerar_pdf(self):
        if self.df is None: return
        plano = self.plano_combo.get()
        if not plano: return

        usa_cnpj = self.df["CNPJ"].apply(lambda x: str(x).strip() not in ["", "0", "nan", "None"]).any()
        id_col = "CNPJ" if usa_cnpj else "CPF"

        filtro = pd.Series(False, index=self.df.index)
        for fat, id_val in self.selected_faturas:
            filtro |= (self.df["Fatura"] == fat) & (self.df[id_col] == id_val)

        dados = self.df.loc[filtro & (self.df["Plano Interno"] == plano)].sort_values("Fatura")
        if dados.empty: return

        nome_clinica = str(dados["Nome"].iloc[0])
        pdf = _PDFTabela(orientation="L")
        pdf.titulo = nome_clinica[:100]
        pdf.add_page()
        pdf.tabela(dados, COLUNAS_PDF)

        pasta = (self.app.pasta_destino if self.app else None) or os.getcwd()
        faturas_str = "_".join(str(int(float(str(f)))) for f, _ in self.selected_faturas)
        plano_safe = re.sub(r'[^\w\-]', '_', plano)
        nome_arquivo = f"Fatura_{faturas_str}_{plano_safe}.pdf"
        caminho = os.path.realpath(os.path.join(pasta, nome_arquivo))

        if not caminho.startswith(os.path.realpath(pasta)):
            self.status.configure(text="❌ Caminho de saída inválido.", text_color="red")
            return
        try:
            pdf.output(caminho)
            self.status.configure(text=f"✅ Gerado: {nome_arquivo}", text_color=ACCENT)
        except Exception as e:
            self.status.configure(text=f"❌ Erro ao salvar PDF: {e}", text_color="red")