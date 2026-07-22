import customtkinter as ctk
import datetime

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
        
        # Main Tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_modelos = self.tabview.add("Modelos de IA")
        self.tab_logs = self.tabview.add("Logs do Sistema")
        self.tab_ajuda = self.tabview.add("Ajuda")
        self.tab_sobre = self.tabview.add("Sobre o SAMS")
        
        self._setup_modelos_tab()
        self._setup_logs_tab()
        self._setup_ajuda_tab()
        self._setup_sobre_tab()

    def _setup_modelos_tab(self):
        lbl = ctk.CTkLabel(self.tab_modelos, text="Gerenciamento de Modelos LLM Offline", font=ctk.CTkFont(size=16, weight="bold"))
        lbl.pack(pady=(10, 20))
        
        frame = ctk.CTkFrame(self.tab_modelos, fg_color="transparent")
        frame.pack(pady=10)
        
        ctk.CTkLabel(frame, text="Selecione o Cérebro da IA:").grid(row=0, column=0, padx=10, pady=10)
        
        # Vamos pegar o modelo atual que está na AIPanel
        current_model = getattr(self.parent.ai_panel, 'current_model_name', "Llama-3.2-3B-Instruct-Q4_0.gguf")
        
        self.combo_model = ctk.CTkComboBox(
            frame, values=["Llama-3.2-3B-Instruct-Q4_0.gguf", "Phi-3-mini-4k-instruct.Q4_0.gguf"],
            width=250, command=self._on_model_change
        )
        self.combo_model.set(current_model)
        self.combo_model.grid(row=0, column=1, padx=10, pady=10)
        
        ctk.CTkLabel(self.tab_modelos, text="Nota: A primeira vez que um modelo for selecionado,\no SAMS fará o download (~2GB a 3GB) automaticamente na memória.", text_color="gray").pack(pady=20)

    def _on_model_change(self, choice):
        # Chama a atualização do painel de IA do app principal
        self.parent.ai_panel._init_local_llm(choice)

    def _setup_logs_tab(self):
        self.tab_logs.grid_rowconfigure(0, weight=1)
        self.tab_logs.grid_columnconfigure(0, weight=1)
        
        self.console = ctk.CTkTextbox(self.tab_logs, font=("Consolas", 11), text_color="#00ff00", fg_color="#1a1a1a")
        self.console.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.console.configure(state="disabled")
        
        if hasattr(self.parent, 'log_history'):
            self.console.configure(state="normal")
            for msg in self.parent.log_history:
                self.console.insert("end", msg + "\n")
            self.console.see("end")
            self.console.configure(state="disabled")

    def _setup_ajuda_tab(self):
        lbl_title = ctk.CTkLabel(self.tab_ajuda, text="Manual do Usuário SAMS", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_title.pack(pady=(20, 10))
        
        txt_help = ctk.CTkTextbox(self.tab_ajuda, wrap="word", fg_color="transparent")
        txt_help.pack(padx=20, pady=10, expand=True, fill="both")
        
        # Estilização tipo Markdown via Tags (Sem font pois CTk proíbe)
        txt_help.tag_config("h1", foreground="#10B981", spacing1=10, spacing3=5)
        txt_help.tag_config("h2", foreground="#58A6FF", spacing1=15, spacing3=5)
        txt_help.tag_config("bold", foreground="#FFFFFF")
        txt_help.tag_config("normal", foreground="#E6EDF3", spacing3=2)
        txt_help.tag_config("bullet", foreground="#F59E0B")
        
        # --- EXPLORER ---
        txt_help.insert("end", "📌 EXPLORER DE ENSAIOS (Painel Esquerdo)\n", "h1")
        txt_help.insert("end", "Aqui ficam listados todos os ensaios carregados da base de dados local.\n", "normal")
        txt_help.insert("end", " • ", "bullet"); txt_help.insert("end", "Ao clicar em um ensaio, o SAMS carrega os dados brutos de tensão e corrente (.txt).\n", "normal")
        txt_help.insert("end", " • ", "bullet"); txt_help.insert("end", "O ensaio ficará em ", "normal"); txt_help.insert("end", "cache", "bold"); txt_help.insert("end", " para navegação rápida.\n", "normal")
        
        # --- WORKSPACE ---
        txt_help.insert("end", "\n📊 WORKSPACE DE ANÁLISE (Painel Central)\n", "h1")
        txt_help.insert("end", "É o coração do sistema, dividido em várias abas técnicas:\n", "normal")
        txt_help.insert("end", " 1. ", "bullet"); txt_help.insert("end", "Sinais Brutos: ", "bold"); txt_help.insert("end", "Exibe o oscilograma de Corrente (A) e Tensão (V).\n", "normal")
        txt_help.insert("end", " 2. ", "bullet"); txt_help.insert("end", "Curva Cíclica (DTC): ", "bold"); txt_help.insert("end", "Dispersão Dinâmica correlacionando Tensão x Corrente.\n", "normal")
        txt_help.insert("end", " 3. ", "bullet"); txt_help.insert("end", "Espectrograma (FFT): ", "bold"); txt_help.insert("end", "Decomposição do som da solda em frequências.\n", "normal")
        txt_help.insert("end", " 4. ", "bullet"); txt_help.insert("end", "Histograma: ", "bold"); txt_help.insert("end", "Distribuição estatística das grandezas (ex: picos anormais).\n", "normal")
        
        # --- SAMS IA ---
        txt_help.insert("end", "\n🧠 SAMS IA - DIAGNÓSTICO E CHAT (Painel Direito)\n", "h1")
        txt_help.insert("end", "Motor de Inteligência Artificial integrado e Totalmente Offline.\n", "normal")
        txt_help.insert("end", " • ", "bullet"); txt_help.insert("end", "Diagnóstico Técnico: ", "bold"); txt_help.insert("end", "Machine Learning que roda em milissegundos para classificar o tipo de transferência de metal (Curto-Circuito, Spray, etc).\n", "normal")
        txt_help.insert("end", " • ", "bullet"); txt_help.insert("end", "Chatbot Especialista: ", "bold"); txt_help.insert("end", "Assistente treinado em Engenharia de Soldagem. Ele consegue ler os cálculos do Workspace e responder suas dúvidas técnicas!\n", "normal")
        txt_help.insert("end", " • ", "bullet"); txt_help.insert("end", "Uso do Chat: ", "bold"); txt_help.insert("end", "Pressione 'Shift+Enter' para pular linha ou 'Enter' para enviar sua dúvida.\n", "normal")
        
        # --- CONFIGURAÇÕES ---
        txt_help.insert("end", "\n⚙️ CONFIGURAÇÕES (Esta Janela)\n", "h1")
        txt_help.insert("end", " • ", "bullet"); txt_help.insert("end", "Modelos de IA: ", "bold"); txt_help.insert("end", "Baixe e troque o cérebro do SAMS (ex: Llama-3).\n", "normal")
        txt_help.insert("end", " • ", "bullet"); txt_help.insert("end", "Logs: ", "bold"); txt_help.insert("end", "Terminal completo registrando todo o funcionamento por trás dos panos.\n\n", "normal")
        
        txt_help.configure(state="disabled")

    def _setup_sobre_tab(self):
        lbl_title = ctk.CTkLabel(self.tab_sobre, text="SAMS ArcFlow Analytics V1.0", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_title.pack(pady=(20, 10))
        
        txt_info = ctk.CTkTextbox(self.tab_sobre, width=540, height=250, font=("Segoe UI", 12), wrap="word", fg_color="transparent")
        txt_info.pack(padx=20, pady=5, expand=True, fill="both")
        
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
        
        # Adicionar Logos
        frame_logos = ctk.CTkFrame(self.tab_sobre, fg_color="transparent", height=80)
        frame_logos.pack(padx=20, pady=(5, 10), fill="x")
        
        from pathlib import Path
        from PIL import Image
        
        assets_dir = Path(__file__).parent.parent.parent / 'assets' / 'imagens'
        
        logos_files = ["IFPElogo.png", "gpsers.jpg", "UFPElogo.png", "Soldamat.png", "cnpq.png"]
        
        target_height = 55
        for filename in logos_files:
            path = assets_dir / filename
            if path.exists():
                pil_img = Image.open(path)
                orig_w, orig_h = pil_img.size
                calc_w = int(orig_w * (target_height / orig_h))
                
                img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(calc_w, target_height))
                lbl = ctk.CTkLabel(frame_logos, text="", image=img)
                lbl.pack(side="left", expand=True, padx=5)

    def append_log(self, message):
        t = datetime.datetime.now().strftime("%H:%M:%S")
        formatted = f"[{t}] {message}"
        self.console.configure(state="normal")
        self.console.insert("end", formatted + "\n")
        self.console.see("end")
        self.console.configure(state="disabled")
        return formatted
