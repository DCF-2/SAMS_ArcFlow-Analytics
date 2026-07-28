import customtkinter as ctk
from PIL import Image
from pathlib import Path
import threading

class CTKErrorWindow(ctk.CTkToplevel):
    """
    Janela de Erro customizada para o SAMS.
    Mantém o tema escuro/dark da aplicação ao invés do visual padrão do Windows.
    """
    def __init__(self, master, title="Erro no Sistema", message="Ocorreu um erro desconhecido.", **kwargs):
        super().__init__(master, **kwargs)
        
        self.title(title)
        self.geometry("450x200")
        self.resizable(False, False)
        self.attributes('-topmost', True)
        self.configure(fg_color="#181818")
        
        # Tenta centralizar
        try:
            self.update_idletasks()
            x = master.winfo_x() + (master.winfo_width() // 2) - (450 // 2)
            y = master.winfo_y() + (master.winfo_height() // 2) - (200 // 2)
            self.geometry(f"+{x}+{y}")
        except:
            pass
            
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        
        icons_dir = Path(__file__).parent.parent.parent.parent / 'assets' / 'icons'
        try:
            icon_err = ctk.CTkImage(Image.open(icons_dir / "erro.png"), size=(48, 48))
        except:
            icon_err = None
            
        if icon_err:
            lbl_icon = ctk.CTkLabel(self, text="", image=icon_err)
            lbl_icon.grid(row=0, column=0, padx=20, pady=20, sticky="n")
            
        lbl_msg = ctk.CTkLabel(self, text=message, font=ctk.CTkFont(size=13), text_color="#E5E7EB", justify="left", wraplength=320)
        lbl_msg.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nw")
        
        btn_ok = ctk.CTkButton(self, text="Entendi", width=120, fg_color="#EF4444", hover_color="#DC2626", command=self.destroy)
        btn_ok.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        self.grab_set()

def show_error(master, title, message):
    """
    Exibe a janela de erro na main thread de forma segura.
    """
    def _show():
        CTKErrorWindow(master, title, message)
        
    # Verifica se ja esta na main thread
    if threading.current_thread() is threading.main_thread():
        _show()
    else:
        # Se for outra thread, usa .after para injetar na GUI principal
        try:
            master.after(0, _show)
        except:
            pass
