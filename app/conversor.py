import customtkinter as ctk
import pandas as pd
from tkinter import filedialog
import os
from datetime import datetime

class ConversorMapasFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.arquivo_inex = None
        self.progress = None
        self.status = None
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Conversor de Execução Orçamentária", font=("Arial", 22, "bold")).pack(pady=20)
        ctk.CTkFrame(self, height=2, fg_color="gray").pack(fill="x", padx=30, pady=(0, 20))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="📂 Anexar Mapa", command=self.selecionar_arquivo, width=180, height=45).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="📁 Selecionar Pasta", command=self.selecionar_pasta, width=180, height=45).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="📥 Incluir INEX (Opcional)", command=self.popup_incluir_inex, width=180, height=45).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="📤 Converter", command=self.converter, width=180, height=45).pack(side="left", padx=10)

        self.progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=30, pady=10)
        self.progress.pack_forget()

        self.status = ctk.CTkLabel(self, text="📂 Selecione um mapa para gerar o relatório.", font=("Calibri", 14, "bold"), text_color="#1e7bc5")
        self.status.pack(pady=20)

        self.arquivo_mapa = None
        self.pasta_destino = os.path.join(os.path.expanduser("~"), "Downloads")

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

    def popup_incluir_inex(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Incluir INEX?")
        popup.geometry("350x150")
        popup.grab_set()

        ctk.CTkLabel(popup, text="Deseja incluir o arquivo INEX?", font=("Arial", 14)).pack(pady=20)

        def incluir():
            popup.destroy()
            path = filedialog.askopenfilename(title="Selecione o arquivo INEX", filetypes=[("Excel Files", "*.xlsx *.xls")])
            if path:
                self.arquivo_inex = path
                self.status.configure(text=f"📄 Arquivo INEX selecionado: {os.path.basename(path)}", text_color="#1E3A8A")

        def nao_incluir():
            popup.destroy()

        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="✅ Sim", command=incluir, width=100).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="❌ Não", command=nao_incluir, width=100).pack(side="right", padx=10)

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
        self.progress.pack(fill="x", padx=30, pady=10)
        self.progress.start()
        self.status.configure(text="Processando...", text_color="#1E3A8A")
        self.update()

        try:
            import pandas as pd
            mapa_df = pd.read_excel(self.arquivo_mapa, dtype={"CNPJ": str, "CPF": str, "Fatura": str})
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
                inex_df["ITEM"] = inex_df.get("ITEM", "")
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
