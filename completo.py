import customtkinter as ctk
import pandas as pd
from tkinter import filedialog
from fpdf import FPDF
import os
from datetime import datetime

# Configurações iniciais
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema Administrativo - COPESP")
        self.geometry("950x650")
        self.resizable(False, False)

        # Layout principal
        self.sidebar = ctk.CTkFrame(self, width=200, fg_color="#0F172A")
        self.sidebar.pack(side="left", fill="y")

        self.container = ctk.CTkFrame(self, fg_color="#1E293B")
        self.container.pack(side="right", expand=True, fill="both")

        # Botões do menu lateral
        ctk.CTkLabel(self.sidebar, text="Menu", font=("Arial", 20, "bold")).pack(pady=20)
        ctk.CTkButton(self.sidebar, text="🏠 Início", command=self.show_inicio).pack(fill="x", pady=5, padx=10)
        ctk.CTkButton(self.sidebar, text="🧾 Conversor de Mapas", command=self.show_conversor).pack(fill="x", pady=5, padx=10)
        ctk.CTkButton(self.sidebar, text="📄 Gerador de PDF", command=self.show_pdf_generator).pack(fill="x", pady=5, padx=10)

        # Frames para cada página
        self.frames = {}
        for FrameClass in (InicioFrame, ConversorMapasFrame, GeradorPDFFaturaFrame):
            frame = FrameClass(self.container, self)
            self.frames[FrameClass] = frame
            frame.pack_forget()

        self.show_inicio()

    def show_inicio(self):
        self._switch_frame(InicioFrame)

    def show_conversor(self):
        self._switch_frame(ConversorMapasFrame)

    def show_pdf_generator(self):
        self._switch_frame(GeradorPDFFaturaFrame)

    def _switch_frame(self, frame_class):
        for f in self.frames.values():
            f.pack_forget()
        self.frames[frame_class].pack(fill="both", expand=True)


# Página de boas-vindas
class InicioFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        ctk.CTkLabel(self, text="Sistema Administrativo", font=("Arial", 26, "bold")).pack(pady=30)
        ctk.CTkLabel(self, text="Escolha uma das opções ao lado para iniciar.", font=("Arial", 16)).pack(pady=10)
        ctk.CTkLabel(self, text="Desenvolvido por Cb Pacífico", font=("Arial", 12, "italic"), text_color="gray").pack(side="bottom", pady=10)


# Script 1 - Conversor de Mapas
class ConversorMapasFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.arquivo_mapa = ""
        self.arquivo_inex = None
        self.pasta_destino = os.path.join(os.path.expanduser("~"), "Downloads")

        ctk.CTkLabel(self, text="Conversor de Mapas - COPESP", font=("Arial", 20, "bold")).pack(pady=20)
        self.progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=30, pady=10)
        self.progress.pack_forget()

        ctk.CTkButton(self, text="📂 Anexar Mapa", command=self.selecionar_arquivo).pack(pady=5)
        ctk.CTkButton(self, text="📁 Pasta Destino", command=self.selecionar_pasta).pack(pady=5)
        ctk.CTkButton(self, text="➕ Incluir INEX (opcional)", command=self.selecionar_inex).pack(pady=5)
        ctk.CTkButton(self, text="📤 Converter", command=self.converter).pack(pady=15)

        self.status = ctk.CTkLabel(self, text="", font=("Arial", 13))
        self.status.pack(pady=10)

    def selecionar_arquivo(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls")])
        if file_path:
            self.arquivo_mapa = file_path
            self.status.configure(text=f"Mapa: {os.path.basename(file_path)}")

    def selecionar_pasta(self):
        folder = filedialog.askdirectory()
        if folder:
            self.pasta_destino = folder
            self.status.configure(text=f"Pasta: {folder}")

    def selecionar_inex(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls")])
        if file_path:
            self.arquivo_inex = file_path
            self.status.configure(text=f"INEX: {os.path.basename(file_path)}")

    def formatar_identificador(self, val):
        try:
            val_str = str(int(val)).zfill(14)
            if len(val_str.strip()) <= 11:
                return f"{val_str[:3]}.{val_str[3:6]}.{val_str[6:9]}-{val_str[9:]}"
            else:
                return f"{val_str[:2]}.{val_str[2:5]}.{val_str[5:8]}/{val_str[8:12]}-{val_str[12:]}"
        except:
            return val

    def converter(self):
        try:
            self.progress.pack()
            self.progress.start()
            mapa_df = pd.read_excel(self.arquivo_mapa, dtype={"CNPJ": str, "CPF": str, "Fatura": str})
            mapa_df["CNPJ"] = mapa_df["CNPJ"].replace([None, "nan", "0", "", " "], pd.NA)
            mapa_df["Identificador"] = mapa_df["CNPJ"].fillna(mapa_df["CPF"])

            resultado = mapa_df.groupby(['Identificador', 'Plano Interno']).agg({
                'Nome': 'first',
                'Fatura': lambda x: ', '.join(map(str, x.unique())),
                'Valor': 'sum'
            }).reset_index()

            resultado.rename(columns={"Identificador": "CNPJ/CPF"}, inplace=True)
            resultado["CNPJ/CPF"] = resultado["CNPJ/CPF"].apply(self.formatar_identificador)
            resultado["Valor"] = resultado["Valor"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

            if self.arquivo_inex:
                inex_df = pd.read_excel(self.arquivo_inex, dtype={"CNPJ": str})
                resultado["CNPJ_Base"] = resultado["CNPJ/CPF"].str.replace(r"\D", "", regex=True).str.zfill(14)
                merge_df = resultado.merge(inex_df[['CNPJ', 'ITEM', 'INEX']], how="left", left_on="CNPJ_Base", right_on="CNPJ")
                resultado = merge_df.drop(columns=["CNPJ", "CNPJ_Base"])

            nome = f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            caminho = os.path.join(self.pasta_destino, nome)
            resultado.to_excel(caminho, index=False)
            self.status.configure(text=f"✅ Arquivo salvo: {nome}")
        except Exception as e:
            self.status.configure(text=f"❌ Erro: {str(e)}")
        finally:
            self.progress.stop()
            self.progress.pack_forget()


# Script 2 - Gerador de PDF por Fatura
class GeradorPDFFaturaFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.df = pd.read_excel("GuiasOCSPSA_437467S-2024.xlsx")
        self.faturas = sorted(self.df['Fatura'].dropna().unique())

        ctk.CTkLabel(self, text="Gerador de PDF por Fatura", font=("Arial", 20, "bold")).pack(pady=20)
        ctk.CTkLabel(self, text="Selecione as faturas:", font=("Arial", 14)).pack()

        self.check_frame = ctk.CTkScrollableFrame(self, height=180)
        self.check_frame.pack(pady=5)
        self.checkboxes = []

        for fat in self.faturas:
            cb = ctk.CTkCheckBox(self.check_frame, text=str(int(fat)), command=self.update_planos)
            cb.pack(anchor="w")
            self.checkboxes.append((fat, cb))

        ctk.CTkLabel(self, text="Plano Interno:", font=("Arial", 14)).pack(pady=10)
        self.plano_combo = ctk.CTkComboBox(self, values=[], state="disabled")
        self.plano_combo.pack()

        self.gerar_btn = ctk.CTkButton(self, text="Gerar PDF", command=self.gerar_pdf, state="disabled")
        self.gerar_btn.pack(pady=20)

    def update_planos(self):
        selecionadas = [f for f, cb in self.checkboxes if cb.get()]
        if not selecionadas:
            self.plano_combo.configure(values=[], state="disabled")
            self.gerar_btn.configure(state="disabled")
            return
        planos = self.df[self.df["Fatura"].isin(selecionadas)]["Plano Interno"].dropna().unique()
        self.plano_combo.configure(values=list(planos), state="normal")
        self.gerar_btn.configure(state="normal")

    def gerar_pdf(self):
        faturas_sel = [f for f, cb in self.checkboxes if cb.get()]
        plano = self.plano_combo.get()
        if not plano:
            return

        dados = self.df[(self.df["Fatura"].isin(faturas_sel)) & (self.df["Plano Interno"] == plano)]
        nome_clinica = str(dados['Nome'].iloc[0])
        colunas = ['CNPJ', 'CPF', 'Guia', 'Plano Interno', 'enc titular', 'enc dependente', 'Valor']

        class PDF(FPDF):
            def tabela(self, dados, colunas):
                self.set_font("Arial", "B", 10)
                self.cell(0, 10, nome_clinica, ln=True, align="C", border=1)
                self.ln()
                self.set_font("Arial", "B", 8)
                for col in colunas:
                    self.cell(28, 7, col, border=1)
                self.ln()
                self.set_font("Arial", "", 7)
                for _, row in dados.iterrows():
                    for col in colunas:
                        val = row[col]
                        if col == "Valor":
                            val = f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        self.cell(28, 7, str(val)[:20], border=1)
                    self.ln()
                self.set_font("Arial", "B", 8)
                total = dados["Valor"].sum()
                self.cell(28*6, 7, "Total", border=1)
                self.cell(28, 7, f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), border=1)

        pdf = PDF()
        pdf.add_page()
        pdf.tabela(dados, colunas)
        nome_arq = f"Fatura_{'_'.join(map(str, map(int, faturas_sel)))}_{plano}.pdf"
        pdf.output(nome_arq)
        ctk.CTkLabel(self, text=f"✅ PDF gerado: {nome_arq}", text_color="green").pack()

# Executar
if __name__ == "__main__":
    app = App()
    app.mainloop()
