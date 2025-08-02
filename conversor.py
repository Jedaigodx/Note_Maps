import customtkinter as ctk
import pandas as pd
from tkinter import filedialog
import os
from datetime import datetime

#colors
BTN_FG = "#0B8052"
BTN_HOVER = "#0E9E66"
TEXT_COLOR_GRAY = "#A0A0A0"

class ConversorMapasFrame(ctk.CTkFrame):
    def __init__(self, master, app=None):
        super().__init__(master)
        self.app = app
        self.arquivo_inex = None
        self.pasta_destino = None

        self._build_ui()

        if self.app:
            if self.app.arquivo_mapa:
                self.atualizar_arquivo_mapa(self.app.arquivo_mapa)
            if self.app.pasta_destino:
                self.atualizar_pasta_destino(self.app.pasta_destino)

    def _build_ui(self):
        ctk.CTkLabel(self, text="Conversor de Execução Orçamentária", font=("Segoe UI", 28, "bold")).pack(pady=(30,20))
        ctk.CTkFrame(self, height=2, fg_color="gray").pack(fill="x", padx=30, pady=(0, 40))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)

        subtitulo = ctk.CTkLabel(
            self,
            text="Selecione o arquivo INEX opcional (.xlsx) para complementar os dados do relatório. Caso não possua, continue apenas com o mapa principal na opção Gerar extrato.",
            font=("Segoe UI", 14),
            wraplength=600,
            justify="center",
            text_color=TEXT_COLOR_GRAY
        )
        subtitulo.pack(pady=(30, 10), padx=20)
        
        self.btn_anexar_inex = ctk.CTkButton(
            btn_frame,
            text="📎 Anexar INEX ",
            command=self.anexar_inex,
            fg_color=BTN_FG,
            hover_color=BTN_HOVER,
            font=("Segoe UI", 18, "bold"),
            width=180,
            height=60,
            corner_radius=12
        )
        self.btn_anexar_inex.pack(side="left", padx=12, pady=4)

        self.btn_converter = ctk.CTkButton(
            btn_frame, 
            text="📤 Gerar extrato",  
            command=self.converter,            
            fg_color=BTN_FG,
            hover_color=BTN_HOVER,
            font=("Segoe UI", 18, "bold"),
            width=180,
            height=60,
            corner_radius=12
        )
        self.btn_converter.pack(side="left", padx=10)

        self.progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=30, pady=10)
        self.progress.pack_forget()

        self.status = ctk.CTkLabel(self, text="📂 Selecione um mapa para gerar o relatório.", font=("Calibri", 14, "bold"), text_color="#1e7bc5")
        self.status.pack(pady=20)

        self.arquivo_mapa = None

    def atualizar_arquivo_mapa(self, path):
        self.arquivo_mapa = path
        self.status.configure(text=f"📄 Arquivo selecionado: {os.path.basename(path)}", text_color="#1E3A8A")

    def atualizar_pasta_destino(self, path):
        self.pasta_destino = path

    def anexar_inex(self):
        path = filedialog.askopenfilename(title="Selecione o arquivo INEX", filetypes=[("Excel Files", "*.xlsx *.xls")])
        if path:
            self.arquivo_inex = path
            self.status.configure(text=f"📄 INEX anexado: {os.path.basename(path)}", text_color="#1E3A8A")

    def formatar_identificador(self, val):
        try:
            val_str = str(int(val)).zfill(14)
            stripped = str(int(val))
            if len(stripped) <= 11:
                cpf = val_str[-11:]
                return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
            else:
                cnpj = val_str
                return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
        except:
            return val

    def converter(self):
        if not self.arquivo_mapa:
            self.status.configure(text="❌ Por favor, selecione o arquivo mapa.", text_color="red")
            return
        if not self.pasta_destino:
            self.status.configure(text="❌ Por favor, selecione a pasta destino para salvar o arquivo.", text_color="red")
            return

        self.btn_converter.configure(state="disabled")
        self.progress.pack(fill="x", padx=30, pady=10)
        self.progress.start()
        self.status.configure(text="Processando...", text_color="#1E3A8A")
        self.update()

        try:
            mapa_df = pd.read_excel(self.arquivo_mapa, dtype={"CNPJ": str, "CPF": str, "Fatura": str})
            # Verificar colunas obrigatórias
            obrigatorias = ['CNPJ', 'CPF', 'Fatura', 'Plano Interno', 'Nome', 'Valor']
            faltando = [col for col in obrigatorias if col not in mapa_df.columns]
            if faltando:
                raise ValueError(f"Colunas faltando: {', '.join(faltando)}")

            mapa_df["CNPJ"] = mapa_df["CNPJ"].replace([None, "nan", "0", "0.0", "", " "], pd.NA)
            mapa_df["Identificador"] = mapa_df["CNPJ"].fillna(mapa_df["CPF"])

            resultado = mapa_df.groupby(['Identificador', 'Plano Interno']).agg({
                'Nome': 'first',
                'Fatura': lambda x: ', '.join(
                    map(lambda v: str(v).split(".")[0] if str(v).replace(".", "").isdigit() else str(v), x.unique())
                ),
                'Valor': 'sum'
            }).reset_index()

            resultado = resultado[['Nome', 'Identificador', 'Plano Interno', 'Fatura', 'Valor']]
            resultado.rename(columns={'Identificador': 'CNPJ/CPF'}, inplace=True)

            resultado['CNPJ/CPF'] = resultado['CNPJ/CPF'].apply(self.formatar_identificador)
            resultado['Valor'] = resultado['Valor'].apply(
                lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )

            if self.arquivo_inex:
                inex_df = pd.read_excel(self.arquivo_inex, dtype={"CNPJ": str})
                inex_df["CNPJ"] = inex_df["CNPJ"].astype(str).str.zfill(14)
                if "ITEM" not in inex_df.columns:
                    inex_df["ITEM"] = ""
                if "INEX" not in inex_df.columns:
                    inex_df["INEX"] = ""

                resultado["CNPJ_Base"] = resultado["CNPJ/CPF"].str.replace(r'\D', '', regex=True).str.zfill(14)

                merge_df = resultado.merge(inex_df[['CNPJ', 'ITEM', 'INEX']], how='left', left_on="CNPJ_Base", right_on="CNPJ")
                merge_df.drop(columns=["CNPJ_Base", "CNPJ"], inplace=True)

                colunas = list(merge_df.columns)
                colunas_reordenadas = ['ITEM', 'INEX'] + [col for col in colunas if col not in ['ITEM', 'INEX']]
                resultado = merge_df[colunas_reordenadas]

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"relatorio_por_cnpj_{timestamp}.xlsx"
            caminho_completo = os.path.join(self.pasta_destino, nome_arquivo)

            resultado.to_excel(caminho_completo, index=False)
            self.status.configure(text=f"✅ Arquivo salvo: {nome_arquivo}", text_color="green")

        except Exception as e:
            self.status.configure(text=f"❌ Erro: {str(e)}", text_color="red")
        finally:
            self.progress.stop()
            self.progress.pack_forget()
            self.btn_converter.configure(state="normal")
