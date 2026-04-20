import pandas as pd
import customtkinter as ctk
from fpdf import FPDF
from tkinter import filedialog, messagebox
import os

# ──────────────────────────────────────────────
#  Cores
# ──────────────────────────────────────────────
BTN_FG            = "#0B8052"
BTN_HOVER         = "#0E9E66"
TEXT_COLOR_GRAY   = "#A0A0A0"
SIDEBAR_BTN_FG    = "#134E8B"
SIDEBAR_BTN_HOVER = "#1D67B5"

# Colunas que serão exibidas no PDF (ordem de preferência)
COLUNAS_PDF = ["CNPJ", "CPF", "Guia", "Fatura", "Plano Interno",
               "enc titular", "enc dependente", "Valor"]

# Larguras em mm de cada coluna
LARGURAS = {
    "CNPJ": 22, "CPF": 22, "Guia": 12, "Plano Interno": 22,
    "Fatura": 12, "enc titular": 50, "enc dependente": 50, "Valor": 20
}


class _PDFTabela(FPDF):
    """Gerador de PDF com tabela formatada."""

    titulo: str = ""

    def header(self):
        pass  # Cabeçalho gerenciado manualmente em tabela()

    def tabela(self, dados: pd.DataFrame, colunas_disponiveis: list[str]):
        # Decide CNPJ vs CPF
        usa_cnpj = dados["CNPJ"].apply(
            lambda x: str(x).strip() not in ["", "0", "nan", "None"]
        ).any()
        id_col = "CNPJ" if usa_cnpj else "CPF"

        colunas_usadas = [c for c in colunas_disponiveis if c not in ("CNPJ", "CPF")]
        colunas_usadas.insert(0, id_col)
        # Filtra apenas colunas que existem no DataFrame
        colunas_usadas = [c for c in colunas_usadas if c in dados.columns or c in ("CNPJ", "CPF")]

        larguras_usadas = {c: LARGURAS.get(c, 20) for c in colunas_usadas}
        total_width = sum(larguras_usadas.values())

        # Título centralizado (apenas 1ª página)
        if self.page_no() == 1:
            self.set_font("Arial", "B", 12)
            self.set_fill_color(240, 240, 240)
            self.cell(total_width, 10, self.titulo[:80], border=1, align="C", ln=True)
            self.ln(2)

        # Cabeçalho das colunas
        self.set_fill_color(230, 230, 230)
        self.set_font("Arial", "B", 9)
        for col in colunas_usadas:
            self.cell(larguras_usadas[col], 8, col, border=1, align="C", fill=True)
        self.ln()

        # Linhas de dados
        self.set_font("Arial", "", 6)
        for _, row in dados.iterrows():
            for col in colunas_usadas:
                val = row.get(col, "")
                if col == "Valor" and pd.notnull(val):
                    try:
                        texto = f"R$ {float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    except (TypeError, ValueError):
                        texto = str(val)[:40]
                else:
                    texto = str(val)[:40] if pd.notnull(val) else ""
                self.cell(larguras_usadas[col], 8, texto, border=1)
            self.ln()

        # Linha de total
        try:
            total_valor = pd.to_numeric(dados["Valor"], errors="coerce").sum()
            total_texto = f"R$ {total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            total_texto = "—"

        self.set_font("Arial", "B", 8)
        largura_ate_valor = sum(
            larguras_usadas[c] for c in colunas_usadas if c != "Valor"
        )
        self.cell(largura_ate_valor, 8, "Total", border=1, align="C")
        self.cell(larguras_usadas.get("Valor", 20), 8, total_texto, border=1, align="C")
        self.ln()


class GeradorPDFFaturaFrame(ctk.CTkFrame):
    def __init__(self, master, app=None):
        super().__init__(master)
        self.app = app
        self.df: pd.DataFrame | None = None
        self.faturas_repetidas: list = []
        self.selected_faturas: list = []
        self._build_ui()

        # CORREÇÃO: se já existe mapa quando o frame é criado, carrega imediatamente
        if self.app and self.app.arquivo_mapa:
            self.after(200, self._carregar_excel)

    # ── UI ──────────────────────────────────
    def _build_ui(self):
        ctk.CTkLabel(
            self, text="Relatório Financeiro Detalhado",
            font=("Segoe UI", 28, "bold")
        ).pack(pady=(30, 20))

        ctk.CTkFrame(self, height=2, fg_color="gray").pack(fill="x", padx=30, pady=(0, 20))

        area = ctk.CTkFrame(self, fg_color="#2b2b2b")
        area.pack(pady=5)

        self.check_frame = ctk.CTkScrollableFrame(area, height=250, width=200)
        self.check_frame.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            area, text="Limpar",
            command=self._limpar_filtros,
            font=("Segoe UI", 16, "bold"),
            text_color=TEXT_COLOR_GRAY,
            fg_color=SIDEBAR_BTN_FG, hover_color=SIDEBAR_BTN_HOVER,
            width=50, height=30, corner_radius=4
        ).pack(side="left", pady=5)

        self.checkboxes: list = []

        ctk.CTkLabel(self, text="Plano Interno:").pack(pady=10)
        self.plano_combo = ctk.CTkComboBox(self, values=[], state="disabled")
        self.plano_combo.pack()

        self.gerar_btn = ctk.CTkButton(
            self, text="📄 Gerar PDF",
            command=self._gerar_pdf,
            state="disabled",
            font=("Segoe UI", 18, "bold"),
            text_color="#ffffff",
            fg_color=BTN_FG, hover_color=BTN_HOVER,
        )
        self.gerar_btn.pack(pady=30)

        self.status = ctk.CTkLabel(self, text="", text_color="green")
        self.status.pack()

    # ── Callbacks do App ──────────────────
    def atualizar_arquivo_mapa(self, caminho: str):
        """
        Chamado pelo App central sempre que um novo mapa é selecionado.
        CORREÇÃO: sempre recarrega — sem memória do arquivo anterior.
        """
        if self.app:
            self.app.arquivo_mapa = caminho
        self.after(100, self._carregar_excel)

    def atualizar_pasta_destino(self, caminho: str):
        if self.app:
            self.app.pasta_destino = caminho

    # ── Carregamento ─────────────────────
    def _carregar_excel(self):
        caminho = self.app.arquivo_mapa if self.app else None
        if not caminho:
            self.status.configure(text="Nenhum arquivo mapa selecionado.", text_color="orange")
            return

        try:
            # Tenta Sheet1; se não existir, pega a primeira aba disponível
            xl = pd.ExcelFile(caminho)
            aba = "Sheet1" if "Sheet1" in xl.sheet_names else xl.sheet_names[0]
            self.df = pd.read_excel(caminho, sheet_name=aba)

            for col in ("CNPJ", "CPF"):
                if col not in self.df.columns:
                    self.df[col] = ""

            usa_cnpj = self.df["CNPJ"].apply(
                lambda x: str(x).strip() not in ["", "0", "nan", "None"]
            ).any()
            id_col = "CNPJ" if usa_cnpj else "CPF"

            grupo = self.df.groupby(["Fatura", id_col]).size().reset_index()
            self.faturas_repetidas = [
                (row["Fatura"], row[id_col]) for _, row in grupo.iterrows()
            ]

        except Exception as e:
            self.status.configure(text=f"❌ Erro ao ler arquivo: {e}", text_color="red")
            return

        # Reconstrói checkboxes (limpa anteriores)
        for widget in self.check_frame.winfo_children():
            widget.destroy()
        self.checkboxes.clear()

        ctk.CTkLabel(
            self.check_frame, text="Fatura – CNPJ/CPF",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", pady=(0, 5))

        for fat, id_val in self.faturas_repetidas:
            try:
                texto_cb = f"{int(float(str(fat)))} - {id_val}"
            except (ValueError, TypeError):
                texto_cb = f"{fat} - {id_val}"

            cb = ctk.CTkCheckBox(
                self.check_frame, text=texto_cb,
                command=self._atualizar_planos
            )
            cb.pack(anchor="w")
            self.checkboxes.append(((fat, id_val), cb))

        self.plano_combo.configure(values=[], state="disabled")
        self.gerar_btn.configure(state="disabled")
        self.status.configure(
            text=f"✅ Arquivo carregado: {os.path.basename(caminho)}", text_color="green"
        )

    # ── Filtros ───────────────────────────
    def _atualizar_planos(self):
        self.selected_faturas = [fk for fk, cb in self.checkboxes if cb.get()]
        if not self.selected_faturas:
            self.plano_combo.configure(values=[], state="disabled")
            self.gerar_btn.configure(state="disabled")
            return

        usa_cnpj = self.df["CNPJ"].apply(
            lambda x: str(x).strip() not in ["", "0", "nan", "None"]
        ).any()
        id_col = "CNPJ" if usa_cnpj else "CPF"

        filtro = pd.Series(False, index=self.df.index)
        for fat, id_val in self.selected_faturas:
            filtro |= (self.df["Fatura"] == fat) & (self.df[id_col] == id_val)

        planos = sorted(self.df.loc[filtro, "Plano Interno"].dropna().unique())
        self.plano_combo.configure(values=planos, state="normal")
        if planos:
            self.plano_combo.set(planos[0])
        self.gerar_btn.configure(state="normal")

    def _limpar_filtros(self):
        for _, cb in self.checkboxes:
            cb.deselect()
        self._atualizar_planos()

    # ── Geração PDF ───────────────────────
    def _gerar_pdf(self):
        if self.df is None:
            self.status.configure(text="❌ Nenhum arquivo carregado.", text_color="red")
            return

        plano = self.plano_combo.get()
        if not plano:
            self.status.configure(text="❌ Selecione um Plano Interno.", text_color="red")
            return

        usa_cnpj = self.df["CNPJ"].apply(
            lambda x: str(x).strip() not in ["", "0", "nan", "None"]
        ).any()
        id_col = "CNPJ" if usa_cnpj else "CPF"

        filtro = pd.Series(False, index=self.df.index)
        for fat, id_val in self.selected_faturas:
            filtro |= (self.df["Fatura"] == fat) & (self.df[id_col] == id_val)

        dados = self.df.loc[filtro & (self.df["Plano Interno"] == plano)].sort_values("Fatura")

        if dados.empty:
            self.status.configure(text="❌ Nenhum dado encontrado com esses filtros.", text_color="red")
            return

        nome_clinica = str(dados["Nome"].iloc[0])

        pdf = _PDFTabela(orientation="L")
        pdf.titulo = nome_clinica[:80]
        pdf.add_page()
        pdf.tabela(dados, COLUNAS_PDF)

        pasta = (self.app.pasta_destino if self.app else None) or os.getcwd()
        faturas_str = "_".join(
            str(int(float(str(f)))) for f, _ in self.selected_faturas
        )
        # Sanitização do nome do arquivo
        import re
        plano_safe = re.sub(r'[^\w\-]', '_', plano)
        nome_arquivo = f"Fatura_{faturas_str}_{plano_safe}.pdf"
        caminho = os.path.realpath(os.path.join(pasta, nome_arquivo))

        # Pentest: garante que o arquivo não escapa da pasta
        if not caminho.startswith(os.path.realpath(pasta)):
            self.status.configure(text="❌ Caminho de saída inválido.", text_color="red")
            return

        try:
            pdf.output(caminho)
            self.status.configure(text=f"✅ PDF gerado: {nome_arquivo}", text_color="green")
        except Exception as e:
            self.status.configure(text=f"❌ Erro ao salvar PDF: {e}", text_color="red")
