import customtkinter as ctk

class SplashScreen(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        self.overrideredirect(True) # Remove borders
        
        # Center on screen
        window_width = 500
        window_height = 300
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_cordinate = int((screen_width/2) - (window_width/2))
        y_cordinate = int((screen_height/2) - (window_height/2))
        self.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
        
        self.configure(fg_color="#1a1a1a")
        self.attributes('-topmost', True)
        
        from pathlib import Path
        from PIL import Image
        assets_dir = Path(__file__).parent.parent.parent / 'assets'
        logo_path = assets_dir / "SAMS.png"
        
        if logo_path.exists():
            self.img_sams = ctk.CTkImage(light_image=Image.open(logo_path), dark_image=Image.open(logo_path), size=(180, 70))
            self.lbl_title = ctk.CTkLabel(self, text="", image=self.img_sams)
        else:
            self.lbl_title = ctk.CTkLabel(self, text="SAMS", font=ctk.CTkFont(size=64, weight="bold"), text_color="#10B981")
            
        self.lbl_title.pack(expand=True, pady=(60, 0))
        
        self.lbl_sub = ctk.CTkLabel(self, text="Sistema de Monitoramento de Soldagem\nArcFlow Analytics V1.0", font=ctk.CTkFont(size=14))
        self.lbl_sub.pack(pady=(0, 20))
        
        self.prog = ctk.CTkProgressBar(self, width=300, fg_color="#333333", progress_color="#10B981")
        self.prog.pack(pady=20)
        self.prog.set(0)
        
        self.lbl_status = ctk.CTkLabel(self, text="Carregando módulos...", font=ctk.CTkFont(size=11), text_color="gray")
        self.lbl_status.pack(pady=10)
        
        self._simulate_loading(0)
        
    def _simulate_loading(self, step):
        steps = [
            (0.2, "Carregando ambiente UI..."),
            (0.5, "Inicializando Motor DSP..."),
            (0.8, "Carregando Modelos Machine Learning..."),
            (1.0, "Pronto.")
        ]
        
        if step < len(steps):
            val, text = steps[step]
            self.prog.set(val)
            self.lbl_status.configure(text=text)
            self.after(500, self._simulate_loading, step + 1)
        else:
            self.after(200, self._finish)
            
    def _finish(self):
        self.destroy()
        self.parent.deiconify() # Shows the main window
