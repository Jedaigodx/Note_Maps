import os
import re
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk
import pandas as pd
from fpdf import FPDF

# Cores
BTN_FG            = "#0B8052"
BTN_HOVER         = "#0E9E66"
TEXT_COLOR_GRAY   = "#A0A0A0"
SIDEBAR_BTN_FG    = "#134E8B"
SIDEBAR_BTN_HOVER = "#1D67B5"
HEADER_COLOR      = "#FFFFFF"
ACCENT            = "#0E9E66"

_RE_SAFE = re.compile(r"[^\w\-]")

# Largura util do A4 paisagem = 297 mm, margens 10mm cada = 277mm util
COL_FATURA  = 22
COL_GUIA    = 18
COL_TITULAR = 100
COL_DEP     = 100
COL_VALOR   = 37
TOTAL_COLS  = COL_FATURA + COL_GUIA + COL_TITULAR + COL_DEP + COL_VALOR  # 277

def _latin1(texto, maxlen=0):
    if pd.isna(texto): return "-"
    s = str(texto)
    if s.strip().lower() in ["nan", "none", "null", ""]: return "-"
    if maxlen: s = s[:maxlen]
    return s.encode("latin-1", errors="replace").decode("latin-1")

def _formatar_id(val):
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
    except:
        return str(x)

def _nome_mapa(caminho_mapa):
    if not caminho_mapa: return "Nao informado"
    return _latin1(os.path.splitext(os.path.basename(caminho_mapa))[0])

def _linhas_multicell(pdf, texto, largura, padding=2):
    """Calcula quantas linhas o multi_cell vai realmente desenhar, usando a largura
    real dos caracteres na fonte atual do pdf, em vez de uma estimativa fixa por
    número de caracteres (que pode subestimar a altura necessária da linha)."""
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


class _PDFPrestador(FPDF):
    def __init__(self, nome, identificador, plano, mapa_nome, total_valor):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.set_margins(10, 10, 10)
        self.set_auto_page_break(auto=True, margin=14)

        self._nome       = _latin1(nome)
        self._id         = _latin1(identificador)
        self._plano      = _latin1(plano)
        self._mapa       = _latin1(mapa_nome)
        self._total      = _fmt_valor(total_valor)
        self._data       = datetime.now().strftime("%d/%m/%Y %H:%M")

    def header(self):
        # Cabeçalho limpo sem retângulo azul, de acordo com o pedido
        self.set_font("Arial", "B", 12)
        self.set_text_color(0, 0, 0)
        self.set_xy(10, 10)
        self.cell(200, 7, "FuSEx / Goiânia - Relatório de discriminação dos serviços", ln=True)
        self.ln(4)

    def footer(self):
        self.set_y(-10)
        self.set_font("Arial", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, f"Emissao: {self._data}   |   Pagina {self.page_no()}", align="R")
        self.set_text_color(0, 0, 0)

    def bloco_prestador(self):
        self.set_fill_color(240, 240, 240)
        self.rect(10, self.get_y(), TOTAL_COLS, 28, "F")
        y0 = self.get_y() + 2

        self.set_xy(12, y0)
        self.set_font("Arial", "B", 9)
        self.set_text_color(50, 50, 50)
        self.cell(40, 5, "DADOS DO PRESTADOR", ln=True)

        dados_esq = [
            ("Nome / Razao Social:", self._nome),
            ("CNPJ / CPF:",          self._id),
            ("Plano Interno (PI):",   self._plano),
        ]
        for label, valor in dados_esq:
            self.set_xy(12, self.get_y())
            self.set_font("Arial", "", 8)
            self.set_text_color(80, 80, 80)
            self.cell(35, 5, _latin1(label), border=0)
            self.set_font("Arial", "B", 8)
            self.set_text_color(0, 0, 0)
            x_val = self.get_x()
            self.set_xy(x_val, self.get_y())
            self.cell(135, 5, _latin1(valor)[:90], border=0, ln=True)

        self.set_xy(200, y0)
        self.set_font("Arial", "B", 9)
        self.set_text_color(50, 50, 50)
        self.cell(0, 5, "RESUMO", ln=True)

        resumo = [
            ("Mapa de origem:", self._mapa),
            ("Total do relatorio:", self._total),
        ]
        for label, valor in resumo:
            self.set_xy(200, self.get_y())
            self.set_font("Arial", "", 8)
            self.set_text_color(80, 80, 80)
            self.cell(38, 5, _latin1(label), border=0)
            self.set_font("Arial", "B", 8)
            self.set_text_color(0, 0, 0)
            self.cell(0, 5, _latin1(valor), border=0, ln=True)

        self.ln(6)

    def tabela_faturas(self, linhas):
        cols = [
            ("Fatura",         COL_FATURA,  "C"),
            ("Guia",           COL_GUIA,    "C"),
            ("Enc. Titular",   COL_TITULAR, "L"),
            ("Enc. Dependente",COL_DEP,     "L"),
            ("Valor (R$)",     COL_VALOR,   "L"),
        ]
        ROW_H = 6
        HEADER_H = 8

        def _cabecalho_tabela():
            self.set_fill_color(220, 220, 220)
            self.set_text_color(0, 0, 0)
            self.set_font("Arial", "B", 8)
            for label, w, aln in cols:
                self.cell(w, HEADER_H, _latin1(label), border=1, align="C", fill=True)
            self.ln()

        _cabecalho_tabela()
        total = 0.0
        self.set_font("Arial", "", 7)

        for i, row in enumerate(linhas):
            fill = (i % 2 == 0)
            if fill: self.set_fill_color(245, 245, 245)
            else: self.set_fill_color(255, 255, 255)

            fatura  = _latin1(row.get("Fatura", ""))
            guia    = _latin1(row.get("Guia", ""))
            tit     = _latin1(row.get("enc titular", ""))
            dep     = _latin1(row.get("enc dependente", ""))

            valor_raw = row.get("Valor", 0)
            try: valor_num = float(valor_raw)
            except: valor_num = 0.0
            total += valor_num

            linhas_tit = _linhas_multicell(self, tit, COL_TITULAR)
            linhas_dep = _linhas_multicell(self, dep, COL_DEP)
            h = max(linhas_tit, linhas_dep) * ROW_H

            if self.get_y() + h > self.page_break_trigger:
                self.add_page()
                _cabecalho_tabela()
                # BUGFIX: _cabecalho_tabela() deixa a fonte em Arial Bold 8 (usada no
                # cabeçalho). Sem este reset, as linhas de dados da página seguinte
                # eram desenhadas em negrito, ficando maiores que o esperado e
                # podendo estourar a altura calculada da linha / quebrar texto de
                # forma inesperada — mesmo defeito relatado no Relatório Detalhado.
                self.set_font("Arial", "", 7)

            x0 = self.get_x()
            y0 = self.get_y()

            self.set_xy(x0, y0)
            self.cell(COL_FATURA, h, fatura, border=1, align="C", fill=fill)
            self.cell(COL_GUIA,   h, guia, border=1, align="C", fill=fill)

            x_tit = self.get_x()
            self.set_xy(x_tit, y0)
            self.set_fill_color(245, 245, 245) if fill else self.set_fill_color(255, 255, 255)
            self.multi_cell(COL_TITULAR, ROW_H, tit, border=1, align="L", fill=fill)

            x_dep = x_tit + COL_TITULAR
            self.set_xy(x_dep, y0)
            self.multi_cell(COL_DEP, ROW_H, dep, border=1, align="L", fill=fill)

            self.set_xy(x_dep + COL_DEP, y0)
            self.cell(COL_VALOR, h, _fmt_valor(valor_num), border=1, align="L", fill=fill)
            self.set_xy(x0, y0 + h)

        self.set_font("Arial", "B", 8)
        self.set_fill_color(200, 200, 200)
        largura_ate_valor = COL_FATURA + COL_GUIA + COL_TITULAR + COL_DEP
        self.cell(largura_ate_valor, 8, "TOTAL GERAL", border=1, align="C", fill=True)
        self.cell(COL_VALOR, 8, _fmt_valor(total), border=1, align="L", fill=True)
        self.ln(8)
        return total


class RelatorioCNPJFrame(ctk.CTkFrame):
    def __init__(self, master, app=None):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.df = None
        self.grupos = []
        self.checkboxes = []
        self._build_ui()
        if self.app and self.app.arquivo_mapa:
            self.after(300, self._carregar)

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="Relatório por CNPJ / Plano Interno", font=("Segoe UI", 24, "bold"), text_color=HEADER_COLOR
        ).pack(pady=(28, 4))

        ctk.CTkLabel(
            self, text="Selecione os prestadores para gerar um PDF individual pronto para envio por e-mail.",
            font=("Segoe UI", 13), wraplength=640, justify="center", text_color=TEXT_COLOR_GRAY
        ).pack(pady=(0, 6))

        ctk.CTkFrame(self, height=1, fg_color="#444444").pack(fill="x", padx=30, pady=(0, 10))

        busca_frame = ctk.CTkFrame(self, fg_color="transparent")
        busca_frame.pack(fill="x", padx=30, pady=(0, 6))

        ctk.CTkLabel(busca_frame, text="Pesquisar", font=("Segoe UI", 12), text_color=TEXT_COLOR_GRAY).pack(side="left", padx=(0, 8))

        self.entry_busca = ctk.CTkEntry(
            busca_frame, placeholder_text="Nome, CNPJ/CPF ou Plano Interno...", font=("Segoe UI", 13), height=32,
        )
        self.entry_busca.pack(side="left", fill="x", expand=True)
        self.entry_busca.bind("<KeyRelease>", lambda _e: self._filtrar_checkboxes())

        ctk.CTkButton(
            busca_frame, text="Limpar", width=64, height=32, fg_color=SIDEBAR_BTN_FG, hover_color=SIDEBAR_BTN_HOVER,
            font=("Segoe UI", 12), command=self._limpar_busca
        ).pack(side="left", padx=(6, 0))

        area = ctk.CTkFrame(self, fg_color="#222222", corner_radius=10)
        area.pack(pady=4, padx=20, fill="both", expand=True)

        self.scroll_check = ctk.CTkScrollableFrame(area, fg_color="transparent")
        self.scroll_check.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=8)

        ctrl = ctk.CTkFrame(area, fg_color="transparent", width=170)
        ctrl.pack(side="right", padx=12, pady=12, fill="y")
        ctrl.pack_propagate(False)

        for texto, cmd in [("Selecionar todos", self._selecionar_visiveis), ("Limpar seleção", self._limpar_selecao)]:
            ctk.CTkButton(
                ctrl, text=texto, command=cmd, fg_color=SIDEBAR_BTN_FG, hover_color=SIDEBAR_BTN_HOVER,
                font=("Segoe UI", 12), height=32, corner_radius=6
            ).pack(fill="x", pady=3)

        ctk.CTkFrame(ctrl, height=1, fg_color="#444444").pack(fill="x", pady=8)

        self.lbl_contagem = ctk.CTkLabel(
            ctrl, text="0 prestadores", font=("Segoe UI", 11), text_color=TEXT_COLOR_GRAY, wraplength=160, justify="center"
        )
        self.lbl_contagem.pack()

        self.btn_gerar = ctk.CTkButton(
            self, text="Gerar PDF(s)", command=self._gerar_pdfs, state="disabled", fg_color=BTN_FG, hover_color=BTN_HOVER,
            font=("Segoe UI", 15, "bold"), width=200, height=46, corner_radius=8
        )
        self.btn_gerar.pack(pady=12)

        self.progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=30)
        self.progress.pack_forget()

        self.status = ctk.CTkLabel(self, text="Aguardando arquivo mapa...", font=("Segoe UI", 12), text_color="#60A5FA")
        self.status.pack(pady=8)

    def atualizar_arquivo_mapa(self, caminho):
        if self.app: self.app.arquivo_mapa = caminho
        self.after(150, self._carregar)

    def atualizar_pasta_destino(self, caminho):
        if self.app: self.app.pasta_destino = caminho

    def _carregar(self):
        caminho = self.app.arquivo_mapa if self.app else None
        if not caminho: return
        try:
            xl  = pd.ExcelFile(caminho)
            aba = "Sheet1" if "Sheet1" in xl.sheet_names else xl.sheet_names[0]
            df  = pd.read_excel(caminho, sheet_name=aba, dtype={"CNPJ": str, "CPF": str, "Fatura": str})
        except Exception as e:
            self.status.configure(text=f"Erro ao ler mapa: {e}", text_color="red")
            return

        obrigatorias = {"CNPJ", "CPF", "Fatura", "Plano Interno", "Nome", "Valor"}
        faltando = obrigatorias - set(df.columns)
        if faltando:
            self.status.configure(text=f"Colunas faltando: {', '.join(sorted(faltando))}", text_color="red")
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
        self.status.configure(text=f"{len(self.grupos)} grupo(s) carregado(s)", text_color=ACCENT)

    def _reconstruir_checkboxes(self):
        marcados = {(item[0], item[1], item[2]) for item, cb in self.checkboxes if cb.get()}
        for w in self.scroll_check.winfo_children(): w.destroy()
        self.checkboxes.clear()

        ctk.CTkLabel(
            self.scroll_check, text="Prestador  —  Plano Interno", font=("Segoe UI", 12, "bold"), text_color="#60A5FA"
        ).pack(anchor="w", pady=(0, 6))

        for item in self.grupos:
            nome, id_fmt, plano, _, _ = item
            texto = f"{nome[:40]}   {id_fmt}   PI: {plano}"
            cb = ctk.CTkCheckBox(self.scroll_check, text=texto, font=("Segoe UI", 12), fg_color=BTN_FG, hover_color=BTN_HOVER)
            cb.pack(anchor="w", pady=2)
            if (nome, id_fmt, plano) in marcados: cb.select()
            self.checkboxes.append((item, cb))
        self._atualizar_contagem()

    def _filtrar_checkboxes(self):
        termo = self.entry_busca.get().strip().lower()
        for item, cb in self.checkboxes:
            nome, id_fmt, plano, _, _ = item
            visivel = (not termo or termo in nome.lower() or termo in id_fmt.lower() or termo in plano.lower())
            if visivel: cb.pack(anchor="w", pady=2)
            else: cb.pack_forget()
        self._atualizar_contagem()

    def _limpar_busca(self):
        self.entry_busca.delete(0, "end")
        self._filtrar_checkboxes()

    def _atualizar_contagem(self):
        visiveis = sum(1 for _, cb in self.checkboxes if cb.winfo_ismapped())
        total    = len(self.checkboxes)
        self.lbl_contagem.configure(text=f"{visiveis} de {total}\nprestadores")

    def _selecionar_visiveis(self):
        for _, cb in self.checkboxes:
            if cb.winfo_ismapped(): cb.select()

    def _limpar_selecao(self):
        for _, cb in self.checkboxes: cb.deselect()

    def _gerar_pdfs(self):
        selecionados = [(item, cb) for item, cb in self.checkboxes if cb.get()]
        if not selecionados:
            messagebox.showwarning("Seleção vazia", "Selecione ao menos um prestador.")
            return

        pasta = (self.app.pasta_destino if self.app else None) or os.getcwd()
        ok, msg = _validar_pasta(pasta)
        if not ok:
            messagebox.showerror("Pasta inválida", msg)
            return

        self.btn_gerar.configure(state="disabled")
        self.progress.pack(fill="x", padx=30, pady=4)
        self.progress.start()
        self.status.configure(text="Gerando PDF(s)...", text_color="#60A5FA")
        self.update()

        gerados, erros = [], []
        pasta_real  = os.path.realpath(pasta)
        mapa_nome   = _nome_mapa(self.app.arquivo_mapa if self.app else None)

        for (nome, id_fmt, plano, grupo, _), _ in selecionados:
            try:
                total_val = pd.to_numeric(grupo["Valor"], errors="coerce").sum()
                pdf = _PDFPrestador(nome, id_fmt, plano, mapa_nome, total_val)
                pdf.add_page()
                pdf.bloco_prestador()
                pdf.tabela_faturas(grupo.to_dict("records"))

                nome_safe = _RE_SAFE.sub("_", nome)[:40]
                id_safe = _RE_SAFE.sub("_", id_fmt)
                plano_safe = _RE_SAFE.sub("_", plano)
                ts = datetime.now().strftime("%H%M%S")
                
                nome_arq = f"{nome_safe}_{id_safe}_PI-{plano_safe}_{ts}.pdf"
                
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
            messagebox.showwarning("Erros", "\n".join(erros))
        self.status.configure(text=resumo, text_color=ACCENT if not erros else "orange")

def _validar_pasta(path):
    if not path: return False, "Nenhuma pasta selecionada."
    path_real = os.path.realpath(path)
    if not os.path.isdir(path_real): return False, "Pasta não encontrada."
    if not os.access(path_real, os.W_OK): return False, "Sem permissão de escrita na pasta."
    return True, ""