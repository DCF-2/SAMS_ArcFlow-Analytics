import customtkinter as ctk
import datetime
from pathlib import Path
import shutil
import tkinter.messagebox as messagebox
from PIL import Image

class AccordionItem(ctk.CTkFrame):
    def __init__(self, master, title, icon_path=None, **kwargs):
        super().__init__(master, fg_color="#1E1E1E", corner_radius=8, **kwargs)
        self.expanded = False
        
        icon = None
        if icon_path and Path(icon_path).exists():
            img = Image.open(icon_path)
            icon = ctk.CTkImage(light_image=img, dark_image=img, size=(20, 20))
        
        self.btn = ctk.CTkButton(self, text=title, anchor="w", image=icon, fg_color="transparent", hover_color="#2b2b2b", text_color="white", font=ctk.CTkFont(size=14, weight="bold"), command=self.toggle)
        self.btn.pack(fill="x", padx=5, pady=5)
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        # Nao fazemos pack do content_frame ainda
        
    def toggle(self):
        if self.expanded:
            self.content_frame.pack_forget()
            self.expanded = False
        else:
            self.content_frame.pack(fill="x", padx=10, pady=(0, 10))
            self.expanded = True

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        self.title("SAMS - Configurações Gerais")
        self.geometry("700x550")
        
        # Centralizar
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (700 // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (550 // 2)
        self.geometry(f"+{x}+{y}")
        self.attributes("-topmost", True)
        self.configure(fg_color="#121212")
        
        lbl_title = ctk.CTkLabel(self, text="Configurações e Serviços", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_title.pack(pady=(20, 10), padx=20, anchor="w")
        
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=15, pady=(10, 5))
        
        self._build_accordion_modelos()
        self._build_accordion_fala()
        self._build_accordion_notificacoes()
        self._build_accordion_armazenamento()
        self._build_accordion_logs()
        self._build_accordion_sobre()
        
        self._build_logos_footer()

    def _build_accordion_modelos(self):
        icons_dir = Path(__file__).parent.parent.parent / 'assets' / 'icons'
        acc = AccordionItem(self.scroll, title="Modelos de IA e Gerenciamento", icon_path=icons_dir / "inteligencia-artificial-configuracoes.png")
        acc.pack(fill="x", pady=5)
        
        ctk.CTkLabel(acc.content_frame, text="Selecione o Cérebro da IA para Inferência:", text_color="#A0A0A0").pack(anchor="w", pady=(5, 5))
        
        self.combo_model = ctk.CTkOptionMenu(
            acc.content_frame, values=["Llama-3.2-3B-Instruct-Q4_0.gguf", "Phi-3-mini-4k-instruct.Q4_0.gguf"],
            variable=self.parent.shared_model_var,
            width=250, command=self._on_model_change,
            fg_color="#2b2b2b", button_color="#333333"
        )
        self.combo_model.pack(anchor="w", pady=(0, 10))
        
        ctk.CTkLabel(acc.content_frame, text="Ao trocar, se o modelo não existir na máquina, o SAMS fará o \ndownload automaticamente da base de dados LLaMA.", text_color="#666666", justify="left").pack(anchor="w")

    def _build_accordion_fala(self):
        icons_dir = Path(__file__).parent.parent.parent / 'assets' / 'icons'
        acc = AccordionItem(self.scroll, title="Configurações de Fala (Sintetizador)", icon_path=icons_dir / "falando.png")
        acc.pack(fill="x", pady=5)
        
        from utils.voice_engine import voice
        
        self.switch_voice = ctk.CTkSwitch(
            acc.content_frame, text="Sintetizador de Voz (Ativado)", 
            command=self._on_voice_toggle, progress_color="#10B981"
        )
        self.switch_voice.pack(anchor="w", pady=10)
        if voice.enabled: self.switch_voice.select()
        else:
            self.switch_voice.deselect()
            self.switch_voice.configure(text="Sintetizador de Voz (Desativado)")
            
    def _build_accordion_notificacoes(self):
        icons_dir = Path(__file__).parent.parent.parent / 'assets' / 'icons'
        acc = AccordionItem(self.scroll, title="Notificações e Alertas", icon_path=icons_dir / "notificação.png")
        acc.pack(fill="x", pady=5)
        
        # O estado atual ficara no main window
        if not hasattr(self.parent, 'notifications_enabled'):
            self.parent.notifications_enabled = True
            
        self.switch_notif = ctk.CTkSwitch(
            acc.content_frame, text="Avisos Visuais de Gráficos e Processamento", 
            command=self._on_notif_toggle, progress_color="#10B981"
        )
        self.switch_notif.pack(anchor="w", pady=10)
        if self.parent.notifications_enabled: self.switch_notif.select()
        else: self.switch_notif.deselect()

    def _build_accordion_armazenamento(self):
        icons_dir = Path(__file__).parent.parent.parent / 'assets' / 'icons'
        acc = AccordionItem(self.scroll, title="Gerenciar Armazenamento", icon_path=icons_dir / "cache-do-navegador.png")
        acc.pack(fill="x", pady=5)
        
        ctk.CTkLabel(acc.content_frame, text="Gerenciamento de cache da aplicação e reset de dados.", text_color="#A0A0A0").pack(anchor="w", pady=(5, 10))
        
        self.lbl_storage_size = ctk.CTkLabel(acc.content_frame, text="Calculando uso de disco...", text_color="#10B981", font=ctk.CTkFont(weight="bold"))
        self.lbl_storage_size.pack(anchor="w", pady=(0, 10))
        self._update_storage_sizes()
        
        btn_limpar_cache = ctk.CTkButton(
            acc.content_frame, text="Limpar Cache (Rápido)",
            image=ctk.CTkImage(Image.open(icons_dir / "apagar-os-dados.png"), size=(20, 20)),
            command=self._on_limpar_cache, fg_color="#F59E0B", hover_color="#D97706", text_color="white", font=ctk.CTkFont(weight="bold")
        )
        btn_limpar_cache.pack(anchor="w", pady=5)
        ctk.CTkLabel(acc.content_frame, text="Apaga matrizes matemáticas temporárias para liberar disco.\nOs ensaios exigirão reprocessamento na próxima leitura.", text_color="#666666", justify="left").pack(anchor="w", pady=(0, 10))
        
        btn_apagar_dados = ctk.CTkButton(
            acc.content_frame, text="Apagar Dados (Hard Reset)",
            image=ctk.CTkImage(Image.open(icons_dir / "excluir.png"), size=(20, 20)),
            command=self._on_apagar_dados, fg_color="#EF4444", hover_color="#DC2626", text_color="white", font=ctk.CTkFont(weight="bold")
        )
        btn_apagar_dados.pack(anchor="w", pady=5)
        ctk.CTkLabel(acc.content_frame, text="Apaga ABSOLUTAMENTE TODOS OS HISTÓRICOS.\nZera o SAMS, apaga o dataset, cache e reinicia do zero.", text_color="#666666", justify="left").pack(anchor="w", pady=(0, 10))

    def _update_storage_sizes(self):
        data_dir = Path(__file__).parent.parent.parent / "data"
        cache_dir = data_dir / "cache"
        session_file = data_dir / "session.json"
        
        cache_size = 0
        session_size = 0
        
        if cache_dir.exists():
            for f in cache_dir.glob("*"):
                if f.is_file(): cache_size += f.stat().st_size
                
        if session_file.exists():
            session_size = session_file.stat().st_size
            
        def format_size(size_bytes):
            if size_bytes == 0: return "0 B"
            sizes = ["B", "KB", "MB", "GB", "TB"]
            i = 0
            while size_bytes >= 1024 and i < len(sizes)-1:
                size_bytes /= 1024.0
                i += 1
            return f"{size_bytes:.2f} {sizes[i]}"
            
        text = f"Espaço Utilizado:\n • Cache Matemático: {format_size(cache_size)}\n • Sessão (Metadados): {format_size(session_size)}"
        self.lbl_storage_size.configure(text=text)

    def _on_limpar_cache(self):
        resposta = messagebox.askyesno("Limpar Cache", "Deseja realmente apagar o cache matemático dos ensaios processados? Isso liberará espaço, mas novos cliques exigirão carregamento longo.")
        if resposta:
            cache_dir = Path(__file__).parent.parent.parent / "data" / "cache"
            if cache_dir.exists():
                try:
                    for f in cache_dir.glob("*.pkl"):
                        f.unlink()
                    for f in cache_dir.glob("*_meta.json"):
                        f.unlink()
                    self._update_storage_sizes()
                    messagebox.showinfo("Sucesso", "Cache limpo com sucesso!")
                except Exception as e:
                    messagebox.showerror("Erro", f"Falha ao limpar: {e}")
            else:
                messagebox.showinfo("Limpo", "O cache já está limpo.")

    def _on_apagar_dados(self):
        resposta = messagebox.askyesno("HARD RESET", "CUIDADO: Isso apagará TODOS os dados de processamento da IA, zerando a tabela de datasets e o histórico.\n\nTem certeza absoluta?")
        if resposta:
            # 1. Limpa Cache Fisico
            data_dir = Path(__file__).parent.parent.parent / "data"
            cache_dir = data_dir / "cache"
            session_file = data_dir / "session.json"
            
            if cache_dir.exists():
                try: shutil.rmtree(cache_dir)
                except: pass
                
            if session_file.exists():
                try: session_file.unlink()
                except: pass
                
            self._update_storage_sizes()
            
            # 2. Zera Memória RAM
            if hasattr(self.parent, 'loaded_trials'):
                self.parent.loaded_trials.clear()
                
            # 3. Zera Tabela no Dashboard
            if hasattr(self.parent, 'dashboard_window') and self.parent.dashboard_window and self.parent.dashboard_window.winfo_exists():
                try:
                    for item in self.parent.dashboard_window.tree.get_children():
                        self.parent.dashboard_window.tree.delete(item)
                except: pass
                
            # 4. Zera ícones na árvore principal
            if hasattr(self.parent, 'explorer_panel') and self.parent.explorer_panel:
                try:
                    for item_id in self.parent.explorer_panel.tree.get_children():
                        self.parent.explorer_panel.tree.item(item_id, image="")
                except: pass
                
            messagebox.showinfo("Sucesso", "Todos os dados foram aniquilados e a aplicação foi reiniciada do zero.")

    def _build_accordion_logs(self):
        icons_dir = Path(__file__).parent.parent.parent / 'assets' / 'icons'
        acc = AccordionItem(self.scroll, title="Logs do Sistema", icon_path=icons_dir / "arquivo-de-log.png")
        acc.pack(fill="x", pady=5)
        
        self.console = ctk.CTkTextbox(acc.content_frame, height=150, font=("Consolas", 11), fg_color="#1a1a1a")
        self.console.pack(fill="x", pady=5)
        
        # Configuracao de Cores no Terminal
        self.console.tag_config("tag_error", foreground="#EF4444")
        self.console.tag_config("tag_warning", foreground="#F59E0B")
        self.console.tag_config("tag_success", foreground="#10B981")
        self.console.tag_config("tag_info", foreground="#E5E7EB")
        self.console.tag_config("tag_debug", foreground="#9CA3AF")
        self.console.tag_config("tag_external", foreground="#60A5FA") # Azul para libs de fora
        
        self.console.configure(state="disabled")
        
        if hasattr(self.parent, 'log_history'):
            self.console.configure(state="normal")
            for level, msg in self.parent.log_history:
                self.append_log(level, msg, auto_update=False)
            self.console.see("end")
            self.console.configure(state="disabled")

    def _build_accordion_sobre(self):
        icons_dir = Path(__file__).parent.parent.parent / 'assets' / 'icons'
        acc = AccordionItem(self.scroll, title="Sobre o SAMS", icon_path=icons_dir / "informacoes.png")
        acc.pack(fill="x", pady=5)
        
        txt_info = ctk.CTkTextbox(acc.content_frame, height=200, font=("Segoe UI", 12), wrap="word", fg_color="transparent")
        txt_info.pack(fill="x", pady=5)
        
        content = (
            "Desenvolvedores e Participantes:\n"
            "Davi Campelo de Freitas¹\n"
            "Meuse Nogueira De Oliveira Junior²\n"
            "Tiago Felipe de Abreu Santos³\n\n"
            "¹ Discente de graduação em Análise e Desenvolvimento de Sistemas - IFPE.\n"
            "² Professor Doutor em Ciência da Computação - IFPE. Orientador do projeto.\n"
            "³ Professor Doutor em Engenharia Mecânica - UFPE. Coorientador do projeto.\n\n"
            "Agradecimentos Oficiais:\n"
            "Agradecemos ao Conselho Nacional de Desenvolvimento Científico e Tecnológico (CNPq) pela cessão de bolsa e apoio financeiro.\n\n"
            "Expressamos sinceros agradecimentos ao Grupo de Pesquisa e Sistemas Embutidos e Rede de Sensores (GPSERS) e ao Laboratório D.E.X.T.E.R. do IFPE, bem como ao Grupo de Pesquisa SOLDAMAT e ao Instituto Nacional de Tecnologia em União e Revestimento de Materiais (INTM) na UFPE, em particular à Drª Ivanilda Ramos de Melo, pelas indispensáveis infraestruturas laboratoriais concedidas."
        )
        txt_info.insert("0.0", content)
        txt_info.configure(state="disabled")

    def _build_logos_footer(self):
        # Adicionar Logos Fixos no fundo da Janela
        frame_logos = ctk.CTkFrame(self, fg_color="transparent", height=80)
        frame_logos.pack(padx=20, pady=10, fill="x", side="bottom")
        
        frame_logos.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        
        assets_dir = Path(__file__).parent.parent.parent / 'assets' / 'img'
        logos_files = ["IFPElogo.png", "gpsers.jpg", "UFPElogo.png", "Soldamat.png", "cnpq.png"]
        
        target_height = 45
        for i, filename in enumerate(logos_files):
            path = assets_dir / filename
            if path.exists():
                pil_img = Image.open(path)
                orig_w, orig_h = pil_img.size
                calc_w = int(orig_w * (target_height / orig_h))
                
                img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(calc_w, target_height))
                lbl = ctk.CTkLabel(frame_logos, text="", image=img)
                lbl.grid(row=0, column=i)

    def _on_model_change(self, choice):
        self.parent.ai_panel._on_model_change(choice)

    def _on_voice_toggle(self):
        from utils.voice_engine import voice
        if self.switch_voice.get():
            voice.enabled = True
            self.switch_voice.configure(text="Sintetizador de Voz (Ativado)")
        else:
            voice.enabled = False
            voice.stop()
            self.switch_voice.configure(text="Sintetizador de Voz (Desativado)")
            
    def _on_notif_toggle(self):
        self.parent.notifications_enabled = bool(self.switch_notif.get())

    def append_log(self, level, message, auto_update=True):
        import datetime
        t = datetime.datetime.now().strftime("%H:%M:%S")
        formatted = f"[{t}] {message}"
        
        tag = "tag_info"
        if level == "ERROR": tag = "tag_error"
        elif level == "WARNING": tag = "tag_warning"
        elif level == "SUCCESS": tag = "tag_success"
        elif level == "DEBUG": tag = "tag_debug"
        elif level == "EXTERNAL": tag = "tag_external"
        
        try:
            self.console.configure(state="normal")
            self.console.insert("end", formatted + "\n", tag)
            if auto_update:
                self.console.see("end")
            self.console.configure(state="disabled")
        except: pass
        return formatted
