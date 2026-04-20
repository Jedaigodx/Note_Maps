"""
relatorio_cnpj_pdf.py  — Note Maps v2.0
─────────────────────────────────────────
Gera um PDF individual por prestador + Plano Interno,
pronto para envio manual por e-mail.

Correções v2.1:
  • Fix encoding: fpdf 1.x usa Latin-1; caracteres fora do range
    (ex.: travessão \u2014, acentos especiais) agora são convertidos
    via encode('latin-1', errors='replace') antes de qualquer cell().
  • Barra de pesquisa com filtro em tempo real nos checkboxes.
"""

import os
import re
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk
import pandas as pd
from fpdf import FPDF

# ──────────────────────────────────────────────
#  Cores
# ──────────────────────────────────────────────
BTN_FG            = "#0B8052"
BTN_HOVER         = "#0E9E66"
TEXT_COLOR_GRAY   = "#A0A0A0"
SIDEBAR_BTN_FG    = "#134E8B"
SIDEBAR_BTN_HOVER = "#1D67B5"

_RE_SAFE = re.compile(r"[^\w\-]")


# ──────────────────────────────────────────────
#  Utilitários
# ──────────────────────────────────────────────
def _latin1(texto, maxlen=0):
    """
    Converte qualquer valor para string Latin-1 seguro para fpdf 1.x.
    Caracteres fora do range (travessao u2014, emojis, etc.) viram '?'.
    """
    s = str(texto) if not isinstance(texto, str) else texto
    if maxlen:
        s = s[:maxlen]
    return s.encode("latin-1", errors="replace").decode("latin-1")


def _formatar_id(val):
    """Formata CPF (<=11 digitos) ou CNPJ (14 digitos) com pontuacao."""
    try:
        digits = str(int(float(str(val).strip())))
        if len(digits) <= 11:
            c = digits.zfill(11)
            return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}"
        c = digits.zfill(14)
        return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}"
    except (ValueError, TypeError):
        return str(val)


def _fmt_valor(x):
    try:
        return f"R$ {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return str(x)


# ──────────────────────────────────────────────
#  Classe PDF
# ──────────────────────────────────────────────
class _PDFPrestador(FPDF):
    """PDF de relatorio individual por CNPJ/CPF + Plano Interno."""

    def __init__(self, nome, identificador, plano):
        super().__init__()
        # Todos os atributos ja passam por _latin1 aqui,
        # eliminando o erro de encoding em qualquer metodo posterior.
        self._nome  = _latin1(nome, 80)
        self._id    = _latin1(identificador)
        self._plano = _latin1(plano)
        self._data  = datetime.now().strftime("%d/%m/%Y")

    def header(self):
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 28, "F")
        self.set_font("Arial", "B", 13)
        self.set_text_color(255, 255, 255)
        self.set_xy(8, 5)
        self.cell(0, 8, "COPESP - Relatorio de Faturamento ao Prestador", ln=True)
        self.set_font("Arial", "", 9)
        self.set_xy(8, 14)
        self.cell(0, 6, f"Emissao: {self._data}", ln=True)
        self.set_text_color(0, 0, 0)
        self.ln(5)

    def footer(self):
        self.set_y(-12)
        self.set_font("Arial", "I", 7)
        self.set_text_color(120, 120, 120)
        self.cell(
            0, 8,
            f"Pagina {self.page_no()} - Gerado automaticamente por Note Maps v2.0",
            align="C"
        )
        self.set_text_color(0, 0, 0)

    def bloco_prestador(self):
        self.set_fill_color(240, 245, 255)
        self.set_font("Arial", "B", 10)
        self.cell(0, 7, "Dados do Prestador", border="B", ln=True, fill=True)
        self.ln(2)
        pares = [
            ("Nome/Razao:",     self._nome),
            ("CNPJ/CPF:",       self._id),
            ("Plano Interno:",  self._plano),
        ]
        for label, valor in pares:
            self.set_font("Arial", "", 10)
            self.cell(38, 6, _latin1(label), border=0)
            self.set_font("Arial", "B", 10)
            self.cell(0, 6, _latin1(valor), border=0, ln=True)
        self.ln(4)

    def tabela_faturas(self, linhas):
        cols = [
            ("Fatura",          25),
            ("Guia",            20),
            ("Enc. Titular",    55),
            ("Enc. Dependente", 55),
            ("Valor (R$)",      35),
        ]
        # Cabecalho verde
        self.set_fill_color(11, 128, 82)
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 9)
        for label, w in cols:
            self.cell(w, 8, _latin1(label), border=1, align="C", fill=True)
        self.ln()
        self.set_text_color(0, 0, 0)

        total = 0.0
        self.set_font("Arial", "", 8)
        for i, row in enumerate(linhas):
            fill = (i % 2 == 0)
            self.set_fill_color(245, 248, 255) if fill else self.set_fill_color(255, 255, 255)

            fatura  = _latin1(row.get("Fatura", ""), 20)
            guia    = _latin1(row.get("Guia", ""), 20)
            enc_tit = _latin1(row.get("enc titular", ""), 50)
            enc_dep = _latin1(row.get("enc dependente", ""), 50)

            valor_raw = row.get("Valor", 0)
            try:
                valor_num = float(valor_raw)
            except (TypeError, ValueError):
                valor_num = 0.0
            total += valor_num

            self.cell(25, 7, fatura,              border=1, fill=fill)
            self.cell(20, 7, guia,                border=1, fill=fill)
            self.cell(55, 7, enc_tit,             border=1, fill=fill)
            self.cell(55, 7, enc_dep,             border=1, fill=fill)
            self.cell(35, 7, _fmt_valor(valor_num), border=1, align="R", fill=fill)
            self.ln()

        # Total
        self.set_font("Arial", "B", 9)
        self.set_fill_color(230, 240, 230)
        self.cell(155, 8, "TOTAL", border=1, align="C", fill=True)
        self.cell(35,  8, _fmt_valor(total), border=1, align="R", fill=True)
        self.ln(6)
        return total


# ──────────────────────────────────────────────
#  Frame da aba
# ──────────────────────────────────────────────
class RelatorioCNPJFrame(ctk.CTkFrame):
    """Aba 'Relatorio por CNPJ/PI'."""

    def __init__(self, master, app=None):
        super().__init__(master)
        self.app = app
        self.df = None
        self.grupos = []
        self.checkboxes = []
        self._build_ui()
        if self.app and self.app.arquivo_mapa:
            self.after(300, self._carregar)

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="Relatorio por CNPJ / Plano Interno",
            font=("Segoe UI", 28, "bold")
        ).pack(pady=(30, 6))

        ctk.CTkLabel(
            self,
            text=(
                "Selecione os prestadores para os quais deseja gerar um PDF "
                "individual pronto para envio por e-mail."
            ),
            font=("Segoe UI", 14), wraplength=640,
            justify="center", text_color=TEXT_COLOR_GRAY
        ).pack(pady=(0, 8))

        ctk.CTkFrame(self, height=2, fg_color="gray").pack(fill="x", padx=30, pady=(0, 10))

        # ── Barra de pesquisa ──
        busca_frame = ctk.CTkFrame(self, fg_color="transparent")
        busca_frame.pack(fill="x", padx=30, pady=(0, 6))

        ctk.CTkLabel(busca_frame, text="🔍", font=("Segoe UI", 18)).pack(side="left", padx=(0, 6))

        self.entry_busca = ctk.CTkEntry(
            busca_frame,
            placeholder_text="Pesquisar por nome, CNPJ/CPF ou Plano Interno...",
            font=("Segoe UI", 13),
            height=34,
        )
        self.entry_busca.pack(side="left", fill="x", expand=True)
        self.entry_busca.bind("<KeyRelease>", lambda _e: self._filtrar_checkboxes())

        ctk.CTkButton(
            busca_frame, text="x", width=34, height=34,
            fg_color="#3a3a3a", hover_color="#555",
            font=("Segoe UI", 13, "bold"),
            command=self._limpar_busca
        ).pack(side="left", padx=(4, 0))

        # ── Area de selecao ──
        sel_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        sel_frame.pack(pady=4, padx=20, fill="x")

        self.scroll_check = ctk.CTkScrollableFrame(sel_frame, height=240, width=520)
        self.scroll_check.pack(side="left", padx=(10, 5), pady=8)

        side_ctrl = ctk.CTkFrame(sel_frame, fg_color="transparent")
        side_ctrl.pack(side="left", padx=5, pady=8, fill="y")

        ctk.CTkButton(
            side_ctrl, text="Selecionar tudo",
            command=self._selecionar_visiveis,
            fg_color=SIDEBAR_BTN_FG, hover_color=SIDEBAR_BTN_HOVER,
            font=("Segoe UI", 13), width=155, height=32, corner_radius=6
        ).pack(pady=3)

        ctk.CTkButton(
            side_ctrl, text="Limpar selecao",
            command=self._limpar_selecao,
            fg_color=SIDEBAR_BTN_FG, hover_color=SIDEBAR_BTN_HOVER,
            font=("Segoe UI", 13), width=155, height=32, corner_radius=6
        ).pack(pady=3)

        self.lbl_contagem = ctk.CTkLabel(
            side_ctrl, text="",
            font=("Segoe UI", 11), text_color=TEXT_COLOR_GRAY,
            wraplength=155, justify="center"
        )
        self.lbl_contagem.pack(pady=(10, 0))

        # ── Botao gerar ──
        self.btn_gerar = ctk.CTkButton(
            self, text="Gerar PDF(s)",
            command=self._gerar_pdfs,
            state="disabled",
            fg_color=BTN_FG, hover_color=BTN_HOVER,
            font=("Segoe UI", 18, "bold"),
            width=220, height=55, corner_radius=12
        )
        self.btn_gerar.pack(pady=14)

        self.progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=30)
        self.progress.pack_forget()

        self.status = ctk.CTkLabel(
            self, text="Aguardando arquivo mapa...",
            font=("Calibri", 14, "bold"), text_color="#1e7bc5"
        )
        self.status.pack(pady=10)

    # ── Callbacks do App ──────────────────
    def atualizar_arquivo_mapa(self, caminho):
        if self.app:
            self.app.arquivo_mapa = caminho
        self.after(150, self._carregar)

    def atualizar_pasta_destino(self, caminho):
        if self.app:
            self.app.pasta_destino = caminho

    # ── Carregamento ─────────────────────
    def _carregar(self):
        caminho = self.app.arquivo_mapa if self.app else None
        if not caminho:
            return
        try:
            xl  = pd.ExcelFile(caminho)
            aba = "Sheet1" if "Sheet1" in xl.sheet_names else xl.sheet_names[0]
            df  = pd.read_excel(
                caminho, sheet_name=aba,
                dtype={"CNPJ": str, "CPF": str, "Fatura": str}
            )
        except Exception as e:
            self.status.configure(text=f"Erro ao ler mapa: {e}", text_color="red")
            return

        obrigatorias = {"CNPJ", "CPF", "Fatura", "Plano Interno", "Nome", "Valor"}
        faltando = obrigatorias - set(df.columns)
        if faltando:
            self.status.configure(
                text=f"Colunas faltando: {', '.join(sorted(faltando))}",
                text_color="red"
            )
            return

        df["CNPJ"] = df["CNPJ"].replace(["", " ", "0", "0.0", "nan", "None", None], pd.NA)
        df["_ID"]  = df["CNPJ"].fillna(df["CPF"])
        self.df    = df

        grupos = []
        for (id_val, plano), grupo in df.groupby(["_ID", "Plano Interno"], dropna=False):
            nome   = str(grupo["Nome"].iloc[0])
            id_fmt = _formatar_id(id_val)
            grupos.append((nome, id_fmt, str(plano), grupo.copy(), id_val))
        self.grupos = grupos

        self._reconstruir_checkboxes()
        self.btn_gerar.configure(state="normal")
        self.status.configure(
            text=f"{len(self.grupos)} grupo(s) carregado(s): {os.path.basename(caminho)}",
            text_color="green"
        )

    def _reconstruir_checkboxes(self):
        marcados = {
            (item[0], item[1], item[2])
            for item, cb in self.checkboxes if cb.get()
        }
        for w in self.scroll_check.winfo_children():
            w.destroy()
        self.checkboxes.clear()

        ctk.CTkLabel(
            self.scroll_check,
            text="Prestador - Plano Interno",
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w", pady=(0, 6))

        for item in self.grupos:
            nome, id_fmt, plano, _, _ = item
            texto = f"{nome[:38]}  |  {id_fmt}  |  PI: {plano}"
            cb = ctk.CTkCheckBox(self.scroll_check, text=texto)
            cb.pack(anchor="w", pady=1)
            if (nome, id_fmt, plano) in marcados:
                cb.select()
            self.checkboxes.append((item, cb))

        self._atualizar_contagem()

    # ── Pesquisa ─────────────────────────
    def _filtrar_checkboxes(self):
        termo = self.entry_busca.get().strip().lower()
        for item, cb in self.checkboxes:
            nome, id_fmt, plano, _, _ = item
            visivel = (
                not termo
                or termo in nome.lower()
                or termo in id_fmt.lower()
                or termo in plano.lower()
            )
            if visivel:
                cb.pack(anchor="w", pady=1)
            else:
                cb.pack_forget()
        self._atualizar_contagem()

    def _limpar_busca(self):
        self.entry_busca.delete(0, "end")
        self._filtrar_checkboxes()

    def _atualizar_contagem(self):
        visiveis = sum(1 for _, cb in self.checkboxes if cb.winfo_ismapped())
        total    = len(self.checkboxes)
        self.lbl_contagem.configure(text=f"{visiveis} de {total} prestadores")

    # ── Selecao ───────────────────────────
    def _selecionar_visiveis(self):
        for _, cb in self.checkboxes:
            if cb.winfo_ismapped():
                cb.select()

    def _limpar_selecao(self):
        for _, cb in self.checkboxes:
            cb.deselect()

    # ── Geracao de PDFs ───────────────────
    def _gerar_pdfs(self):
        selecionados = [(item, cb) for item, cb in self.checkboxes if cb.get()]
        if not selecionados:
            messagebox.showwarning("Selecao vazia", "Selecione ao menos um prestador.")
            return

        pasta = (self.app.pasta_destino if self.app else None) or os.getcwd()
        ok, msg = _validar_pasta(pasta)
        if not ok:
            messagebox.showerror("Pasta invalida", msg)
            return

        self.btn_gerar.configure(state="disabled")
        self.progress.pack(fill="x", padx=30, pady=4)
        self.progress.start()
        self.status.configure(text="Gerando PDF(s)...", text_color="#1E3A8A")
        self.update()

        gerados, erros = [], []
        pasta_real = os.path.realpath(pasta)

        for (nome, id_fmt, plano, grupo, _), _ in selecionados:
            try:
                pdf = _PDFPrestador(nome, id_fmt, plano)
                pdf.add_page()
                pdf.bloco_prestador()
                pdf.tabela_faturas(grupo.to_dict("records"))

                id_safe    = _RE_SAFE.sub("_", id_fmt)
                plano_safe = _RE_SAFE.sub("_", plano)
                ts         = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_arq   = f"RelPrestador_{id_safe}_{plano_safe}_{ts}.pdf"

                caminho = os.path.realpath(os.path.join(pasta_real, nome_arq))
                if not caminho.startswith(pasta_real):
                    erros.append(f"{nome}: caminho fora da pasta permitida.")
                    continue

                pdf.output(caminho)
                gerados.append(nome_arq)

            except Exception as e:
                erros.append(f"{nome} / {plano}: {e}")

        self.progress.stop()
        self.progress.pack_forget()
        self.btn_gerar.configure(state="normal")

        resumo = f"{len(gerados)} PDF(s) gerado(s)."
        if erros:
            resumo += f"  {len(erros)} erro(s)."
            messagebox.showwarning("Erros na geracao", "\n".join(erros))
        self.status.configure(
            text=resumo,
            text_color="green" if not erros else "orange"
        )


# ──────────────────────────────────────────────
#  Validacao de pasta
# ──────────────────────────────────────────────
def _validar_pasta(path):
    if not path:
        return False, "Nenhuma pasta selecionada."
    path_real = os.path.realpath(path)
    if not os.path.isdir(path_real):
        return False, "Pasta nao encontrada."
    if not os.access(path_real, os.W_OK):
        return False, "Sem permissao de escrita na pasta."
    return True, ""
