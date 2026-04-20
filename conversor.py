import customtkinter as ctk
import pandas as pd
from tkinter import filedialog, messagebox
import os
import re
from datetime import datetime

# ──────────────────────────────────────────────
#  Cores
# ──────────────────────────────────────────────
BTN_FG          = "#0B8052"
BTN_HOVER       = "#0E9E66"
TEXT_COLOR_GRAY = "#A0A0A0"

# Colunas que o mapa deve conter
COLUNAS_OBRIGATORIAS = {"CNPJ", "CPF", "Fatura", "Plano Interno", "Nome", "Valor"}

# Pentest / segurança: caracteres proibidos em nomes de arquivo gerados
_RE_SAFE_FILENAME = re.compile(r'[^\w\-.]')


def _sanitize_filename(name: str) -> str:
    """Remove caracteres perigosos do nome do arquivo de saída."""
    return _RE_SAFE_FILENAME.sub('_', name)


def _formatar_identificador(val) -> str:
    """
    Formata CPF (≤ 11 dígitos) ou CNPJ (14 dígitos) com pontuação.
    Nunca lança exceção — retorna o valor original em caso de falha.
    """
    try:
        # Converte para inteiro para remover zeros flutuantes e depois
        # reconstrói como string com zeros à esquerda.
        digits = str(int(float(str(val).strip())))
        if len(digits) <= 11:
            cpf = digits.zfill(11)
            return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        else:
            cnpj = digits.zfill(14)
            return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    except (ValueError, TypeError):
        return str(val)


def _formatar_valor(x) -> str:
    try:
        return f"R$ {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return str(x)


class ConversorMapasFrame(ctk.CTkFrame):
    def __init__(self, master, app=None):
        super().__init__(master)
        self.app = app
        self.arquivo_mapa: str | None = None
        self.arquivo_inex: str | None = None
        self.pasta_destino: str | None = None
        self._build_ui()

        # Sincroniza estado inicial com o app (caso já exista mapa/pasta)
        if self.app:
            if self.app.arquivo_mapa:
                self.atualizar_arquivo_mapa(self.app.arquivo_mapa)
            if self.app.pasta_destino:
                self.atualizar_pasta_destino(self.app.pasta_destino)

    # ── UI ──────────────────────────────────
    def _build_ui(self):
        ctk.CTkLabel(
            self, text="Conversor de Execução Orçamentária",
            font=("Segoe UI", 28, "bold")
        ).pack(pady=(30, 20))

        ctk.CTkFrame(self, height=2, fg_color="gray").pack(fill="x", padx=30, pady=(0, 20))

        ctk.CTkLabel(
            self,
            text=(
                "Selecione o arquivo INEX opcional (.xlsx) para complementar os dados do relatório. "
                "Caso não possua, continue apenas com o mapa principal na opção Gerar extrato."
            ),
            font=("Segoe UI", 14),
            wraplength=600,
            justify="center",
            text_color=TEXT_COLOR_GRAY
        ).pack(pady=(10, 20), padx=20)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)

        self.btn_anexar_inex = ctk.CTkButton(
            btn_frame, text="📎 Anexar INEX",
            command=self._anexar_inex,
            fg_color=BTN_FG, hover_color=BTN_HOVER,
            font=("Segoe UI", 18, "bold"),
            width=180, height=60, corner_radius=12
        )
        self.btn_anexar_inex.pack(side="left", padx=12, pady=4)

        self.btn_converter = ctk.CTkButton(
            btn_frame, text="📤 Gerar extrato",
            command=self._converter,
            fg_color=BTN_FG, hover_color=BTN_HOVER,
            font=("Segoe UI", 18, "bold"),
            width=180, height=60, corner_radius=12
        )
        self.btn_converter.pack(side="left", padx=10)

        self.progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=30, pady=10)
        self.progress.pack_forget()

        self.status = ctk.CTkLabel(
            self,
            text="📂 Selecione um mapa para gerar o relatório.",
            font=("Calibri", 14, "bold"),
            text_color="#1e7bc5"
        )
        self.status.pack(pady=20)

    # ── Callbacks do app ──────────────────
    def atualizar_arquivo_mapa(self, path: str):
        """Chamado pelo App quando o mapa global é trocado."""
        self.arquivo_mapa = path
        self.status.configure(
            text=f"📄 Arquivo selecionado: {os.path.basename(path)}",
            text_color="#1E3A8A"
        )

    def atualizar_pasta_destino(self, path: str):
        self.pasta_destino = path

    # ── Ações internas ────────────────────
    def _anexar_inex(self):
        path = filedialog.askopenfilename(
            title="Selecione o arquivo INEX",
            filetypes=[("Excel Files", "*.xlsx *.xls")]
        )
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()
        if ext not in {".xlsx", ".xls"}:
            messagebox.showerror("Arquivo inválido", "Selecione um arquivo .xlsx ou .xls.")
            return
        self.arquivo_inex = path
        self.status.configure(
            text=f"📄 INEX anexado: {os.path.basename(path)}",
            text_color="#1E3A8A"
        )

    def _converter(self):
        if not self.arquivo_mapa:
            self.status.configure(text="❌ Por favor, selecione o arquivo mapa.", text_color="red")
            return
        if not self.pasta_destino:
            self.status.configure(text="❌ Por favor, selecione a pasta destino.", text_color="red")
            return

        self.btn_converter.configure(state="disabled")
        self.progress.pack(fill="x", padx=30, pady=10)
        self.progress.start()
        self.status.configure(text="⏳ Processando...", text_color="#1E3A8A")
        self.update()

        try:
            resultado = self._processar()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = _sanitize_filename(f"relatorio_por_cnpj_{timestamp}.xlsx")
            # Pentest: valida que o destino final ainda está dentro da pasta esperada
            caminho_completo = os.path.realpath(
                os.path.join(self.pasta_destino, nome_arquivo)
            )
            pasta_real = os.path.realpath(self.pasta_destino)
            if not caminho_completo.startswith(pasta_real):
                raise PermissionError("Destino de arquivo fora da pasta permitida.")

            resultado.to_excel(caminho_completo, index=False)
            self.status.configure(
                text=f"✅ Arquivo salvo: {nome_arquivo}", text_color="green"
            )

        except PermissionError as e:
            self.status.configure(text=f"❌ Segurança: {e}", text_color="red")
        except ValueError as e:
            self.status.configure(text=f"❌ Dados inválidos: {e}", text_color="red")
        except Exception as e:
            self.status.configure(text=f"❌ Erro inesperado: {e}", text_color="red")
        finally:
            self.progress.stop()
            self.progress.pack_forget()
            self.btn_converter.configure(state="normal")

    def _processar(self) -> pd.DataFrame:
        """
        Lê o mapa, agrupa por Identificador + Plano Interno e retorna
        o DataFrame final (com INEX mesclado se houver).
        """
        mapa_df = pd.read_excel(
            self.arquivo_mapa,
            dtype={"CNPJ": str, "CPF": str, "Fatura": str}
        )

        # Valida colunas obrigatórias
        faltando = COLUNAS_OBRIGATORIAS - set(mapa_df.columns)
        if faltando:
            raise ValueError(f"Colunas faltando no mapa: {', '.join(sorted(faltando))}")

        # Normaliza CNPJ/CPF
        mapa_df["CNPJ"] = mapa_df["CNPJ"].replace(
            ["", " ", "0", "0.0", "nan", "None", None], pd.NA
        )
        mapa_df["Identificador"] = mapa_df["CNPJ"].fillna(mapa_df["CPF"])

        # Agrupa por Identificador + Plano Interno
        resultado = (
            mapa_df
            .groupby(["Identificador", "Plano Interno"], dropna=False)
            .agg(
                Nome    = ("Nome", "first"),
                Fatura  = ("Fatura", lambda x: ", ".join(
                    str(v).split(".")[0] if str(v).replace(".", "").isdigit() else str(v)
                    for v in x.unique()
                )),
                Valor   = ("Valor", "sum"),
            )
            .reset_index()
            .rename(columns={"Identificador": "CNPJ/CPF"})
        )

        resultado = resultado[["Nome", "CNPJ/CPF", "Plano Interno", "Fatura", "Valor"]]
        resultado["CNPJ/CPF"] = resultado["CNPJ/CPF"].apply(_formatar_identificador)
        resultado["Valor"]    = resultado["Valor"].apply(_formatar_valor)

        # Mescla com INEX se fornecido
        if self.arquivo_inex:
            resultado = self._mesclar_inex(resultado)

        return resultado

    def _mesclar_inex(self, resultado: pd.DataFrame) -> pd.DataFrame:
        inex_df = pd.read_excel(self.arquivo_inex, dtype={"CNPJ": str})
        inex_df["CNPJ"] = inex_df["CNPJ"].astype(str).str.strip().str.zfill(14)

        if "ITEM" not in inex_df.columns:
            inex_df["ITEM"] = ""
        if "INEX" not in inex_df.columns:
            inex_df["INEX"] = ""

        resultado["CNPJ_Base"] = (
            resultado["CNPJ/CPF"]
            .str.replace(r"\D", "", regex=True)
            .str.zfill(14)
        )
        merge_df = resultado.merge(
            inex_df[["CNPJ", "ITEM", "INEX"]],
            how="left",
            left_on="CNPJ_Base",
            right_on="CNPJ"
        )
        merge_df.drop(columns=["CNPJ_Base", "CNPJ"], inplace=True, errors="ignore")

        # Reordena colocando ITEM e INEX no início
        cols = list(merge_df.columns)
        extras = [c for c in ["ITEM", "INEX"] if c in cols]
        demais = [c for c in cols if c not in extras]
        return merge_df[extras + demais]
