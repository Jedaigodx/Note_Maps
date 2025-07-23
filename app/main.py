import customtkinter as ctk
from conversor import ConversorMapasFrame
from gerador_pdf import GeradorPDFFaturaFrame

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class InicioFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        ctk.CTkLabel(self, text="Sistema Administrativo - COPESP", font=("Arial", 26, "bold")).pack(pady=30)
        ctk.CTkLabel(self, text="Escolha uma das opções ao lado para iniciar.", font=("Arial", 16)).pack(pady=10)
        ctk.CTkLabel(self, text="Desenvolvido por Cb Pacífico", font=("Arial", 12, "italic"), text_color="gray").pack(side="bottom", pady=10)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Note Maps")
        self.geometry("950x650")
        self.resizable(False, False)

        self.sidebar = ctk.CTkFrame(self, width=220, fg_color="#0F172A")
        self.sidebar.pack(side="left", fill="y")

        self.container = ctk.CTkFrame(self, fg_color="#1E293B")
        self.container.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(self.sidebar, text="Menu", font=("Arial", 20, "bold")).pack(pady=20)
        ctk.CTkButton(self.sidebar, text="🏠 Início", command=self.show_inicio).pack(fill="x", pady=5, padx=20)
        ctk.CTkButton(self.sidebar, text="🧾 Conversor de Mapas", command=self.show_conversor).pack(fill="x", pady=5, padx=20)
        ctk.CTkButton(self.sidebar, text="📄 Gerador de PDF", command=self.show_pdf).pack(fill="x", pady=5, padx=20)

        self.frames = {}
        for FrameClass in (InicioFrame, ConversorMapasFrame, GeradorPDFFaturaFrame):
            frame = FrameClass(self.container)
            self.frames[FrameClass] = frame
            frame.pack_forget()

        self.show_inicio()

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
