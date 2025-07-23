import customtkinter as ctk
from tkinter import filedialog
from conversor import ConversorMapasFrame
from gerador_pdf import GeradorPDFFaturaFrame

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class InicioFrame(ctk.CTkFrame):
    def __init__(self, master, app=None):
        super().__init__(master)
        self.app = app
        
        # Frame principal para organização
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(main_frame, text="Sistema Administrativo - COPESP", 
                    font=("Arial", 26, "bold")).pack(pady=30)
        
        # Instrução
        ctk.CTkLabel(main_frame, text="Selecione o arquivo do mapa (arquivo Excel) e a pasta onde serão salvos os resultados ", 
                    font=("Arial", 16)).pack(pady=10)
        
        # Frame para os botões (um ao lado do outro)
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=20)
        
        # Botão Anexar Mapa
        ctk.CTkButton(button_frame, text="➕ ANEXAR MAPA",
                     command=self.app.anexar_mapa,
                     fg_color="#04573B",
                     hover_color="#093828",
                     font=("Arial", 14, "bold"),
                     height=50,
                     width=180).pack(side="left", padx=10)
        
        # Botão Selecionar Pasta
        ctk.CTkButton(button_frame, text="➕ SELECIONAR PASTA",
                     command=self.app.selecionar_pasta_destino,
                     fg_color="#04573B",
                     hover_color="#093828",
                     font=("Arial", 14, "bold"),
                     height=50,
                     width=180).pack(side="left", padx=10)
        # Instrução
        ctk.CTkLabel(main_frame, text="Escolha uma das opções ao lado para iniciar.", 
                    font=("Arial", 16)).pack(pady=10)
        
        # Rodapé
        ctk.CTkLabel(main_frame, text="Desenvolvido por Cb Pacífico", 
                    font=("Arial", 12, "italic"), 
                    text_color="gray").pack(side="bottom", pady=10)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Note Maps")
        self.geometry("950x650")
        self.resizable(False, False)

        # Variáveis compartilhadas
        self.arquivo_mapa = None
        self.pasta_destino = None

        # Sidebar com botões gerais e navegação
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color="#0F172A")
        self.sidebar.pack(side="left", fill="y")

        self.container = ctk.CTkFrame(self, fg_color="#1E293B")
        self.container.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(self.sidebar, text="Menu", font=("Arial", 20, "bold")).pack(pady=20)

        # Navegação
        ctk.CTkButton(self.sidebar, text="🏠 Início", 
                     command=self.show_inicio, 
                     fg_color="#062F88",
                     hover_color="#1D47A0",
                     font=("Arial",16, "bold"),
                     height=30).pack(fill="x", pady=(10,20), padx=15)
  
        # Removi os botões de anexar da sidebar pois agora estão no frame inicial

        ctk.CTkButton(self.sidebar, text="🧾 Conversor de Notas", 
                     command=self.show_conversor,
                     fg_color="#288ED3",
                     hover_color="#1D47A0",
                     font=("Arial",14, "bold"),
                     height=30).pack(fill="x", pady=(5,7), padx=15)

        ctk.CTkButton(self.sidebar, text="📄 Gerar Relatório", 
                     command=self.show_pdf,
                     fg_color="#288ED3",
                     hover_color="#1D47A0",
                     font=("Arial",14, "bold"),
                     height=30, 
                     anchor="w").pack(fill="x", pady=(5,10), padx=15)

        # Instanciar frames passando self para compartilhamento
        self.frames = {}
        for FrameClass in (InicioFrame, ConversorMapasFrame, GeradorPDFFaturaFrame):
            frame = FrameClass(self.container, app=self)
            self.frames[FrameClass] = frame
            frame.pack_forget()

        self.show_inicio()

    def anexar_mapa(self):
        path = filedialog.askopenfilename(title="Selecione o arquivo Excel do mapa", filetypes=[("Excel files", "*.xlsx *.xls")])
        if path:
            self.arquivo_mapa = path
            # Atualiza frames que usam o arquivo mapa
            for frame in self.frames.values():
                if hasattr(frame, 'atualizar_arquivo_mapa'):
                    frame.atualizar_arquivo_mapa(path)

    def selecionar_pasta_destino(self):
        path = filedialog.askdirectory(title="Selecione a pasta destino")
        if path:
            self.pasta_destino = path
            # Atualiza frames que usam pasta destino
            for frame in self.frames.values():
                if hasattr(frame, 'atualizar_pasta_destino'):
                    frame.atualizar_pasta_destino(path)

    def show_inicio(self):
        self._switch_frame(InicioFrame)

    def show_conversor(self):
        self._switch_frame(ConversorMapasFrame)

    def show_pdf(self):
        self._switch_frame(GeradorPDFFaturaFrame)

    def _switch_frame(self, frame_class):
        for f in self.frames.values():
            f.pack_forget()
        self.frames[frame_class].pack(fill="both", expand=True)

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()