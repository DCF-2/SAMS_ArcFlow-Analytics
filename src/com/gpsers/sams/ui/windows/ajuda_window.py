import customtkinter as ctk
from pathlib import Path
from PIL import Image

class AjudaWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("SAMS - Ajuda e Documentação")
        self.geometry("900x700")
        
        # Centralizar
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (900 // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (700 // 2)
        self.geometry(f"+{x}+{y}")
        self.attributes("-topmost", True)
        self.configure(fg_color="#121212")
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_manual = self.tabview.add("Manual do Usuário")
        self.tab_graficos = self.tabview.add("Documentação Gráfica")
        
        self._setup_manual_tab()
        self._setup_graficos_tab()

    def _setup_manual_tab(self):
        lbl_title = ctk.CTkLabel(self.tab_manual, text="Manual do Usuário SAMS", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_title.pack(pady=(20, 10))
        
        txt_help = ctk.CTkTextbox(self.tab_manual, wrap="word", fg_color="transparent")
        txt_help.pack(padx=20, pady=10, expand=True, fill="both")
        
        txt_help.tag_config("h1", foreground="#10B981", spacing1=10, spacing3=5)
        txt_help.tag_config("h2", foreground="#58A6FF", spacing1=15, spacing3=5)
        txt_help.tag_config("bold", foreground="#FFFFFF")
        txt_help.tag_config("normal", foreground="#E6EDF3", spacing3=2)
        txt_help.tag_config("bullet", foreground="#F59E0B")
        
        txt_help.insert("end", "📌 EXPLORER DE ENSAIOS (Painel Esquerdo)\n", "h1")
        txt_help.insert("end", "Aqui ficam listados todos os ensaios carregados da base de dados local.\n", "normal")
        txt_help.insert("end", " • ", "bullet"); txt_help.insert("end", "Ao clicar em um ensaio, o SAMS carrega os dados brutos de tensão e corrente (.txt).\n", "normal")
        txt_help.insert("end", " • ", "bullet"); txt_help.insert("end", "O ensaio ficará em ", "normal"); txt_help.insert("end", "cache", "bold"); txt_help.insert("end", " para navegação rápida.\n", "normal")
        
        txt_help.insert("end", "\n📊 WORKSPACE DE ANÁLISE (Painel Central)\n", "h1")
        txt_help.insert("end", "É o coração do sistema, dividido em várias abas técnicas no Dashboard Visual:\n", "normal")
        txt_help.insert("end", " 1. ", "bullet"); txt_help.insert("end", "Sinais Brutos: ", "bold"); txt_help.insert("end", "Exibe o oscilograma de Corrente (A) e Tensão (V).\n", "normal")
        txt_help.insert("end", " 2. ", "bullet"); txt_help.insert("end", "Curva Cíclica (DTC): ", "bold"); txt_help.insert("end", "Dispersão Dinâmica correlacionando Tensão x Corrente.\n", "normal")
        txt_help.insert("end", " 3. ", "bullet"); txt_help.insert("end", "Espectrograma (FFT): ", "bold"); txt_help.insert("end", "Decomposição do som da solda em frequências.\n", "normal")
        txt_help.insert("end", " 4. ", "bullet"); txt_help.insert("end", "Tabela de Extração (Features): ", "bold"); txt_help.insert("end", "Mostra os resultados matemáticos processados do Ensaio.\n", "normal")
        
        txt_help.insert("end", "\n🧠 SAMS IA - DIAGNÓSTICO E CHAT (Painel Direito)\n", "h1")
        txt_help.insert("end", "Motor de Inteligência Artificial integrado e Totalmente Offline.\n", "normal")
        txt_help.insert("end", " • ", "bullet"); txt_help.insert("end", "Diagnóstico Técnico: ", "bold"); txt_help.insert("end", "Machine Learning que roda em milissegundos para classificar o tipo de transferência.\n", "normal")
        txt_help.insert("end", " • ", "bullet"); txt_help.insert("end", "Chatbot Especialista: ", "bold"); txt_help.insert("end", "Assistente treinado em Engenharia de Soldagem. Responde suas dúvidas!\n", "normal")
        
        txt_help.insert("end", "\n⚙️ CONFIGURAÇÕES E ALERTAS\n", "h1")
        txt_help.insert("end", " • ", "bullet"); txt_help.insert("end", "Notificações: ", "bold"); txt_help.insert("end", "Avisos Toast no canto inferior quando cálculos de vídeo estão prontos.\n\n", "normal")
        
        txt_help.configure(state="disabled")

    def _setup_graficos_tab(self):
        self.tab_graficos.grid_rowconfigure(0, weight=1)
        self.tab_graficos.grid_columnconfigure(0, weight=1)
        
        scroll = ctk.CTkScrollableFrame(self.tab_graficos, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew")
        
        lbl_title = ctk.CTkLabel(scroll, text="Documentação Técnica dos Gráficos (Base: Ensaio Spray)", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_title.pack(pady=10)
        
        res_dir = Path(__file__).parent.parent.parent.parent.parent.parent.parent / "PGD-INTM-AUDIOS" / "Ensaio 28.05.26 - Spray" / "Resultados" / "Relatorio_Ensaio_1_20260601_090132"
        
        # 1. TEMPO
        ctk.CTkLabel(scroll, text="1. Sinal Acústico no Tempo", font=ctk.CTkFont(size=16, weight="bold"), text_color="#3B82F6").pack(pady=(20, 5), anchor="w")
        ctk.CTkLabel(scroll, text="Apresenta a oscilação bruta (amplitude) ao longo dos segundos.\nNo modo Spray (abaixo), vemos uma banda contínua sem picos extremos (estabilidade alta).\nModos como Curto-Circuito mostrariam 'espinhos' gigantes devido ao estrangulamento da gota.", justify="left").pack(anchor="w", padx=10)
        
        img1_path = res_dir / "1_TEMPO.png"
        if img1_path.exists():
            img1 = ctk.CTkImage(light_image=Image.open(img1_path), dark_image=Image.open(img1_path), size=(500, 300))
            ctk.CTkLabel(scroll, text="", image=img1).pack(pady=10)
            
        # 2. PSD
        ctk.CTkLabel(scroll, text="2. Densidade Espectral de Potência (PSD Welch)", font=ctk.CTkFont(size=16, weight="bold"), text_color="#3B82F6").pack(pady=(20, 5), anchor="w")
        ctk.CTkLabel(scroll, text="Exibe como a energia do som se distribui em Frequências (Hz).\nNo eixo X temos a Frequência, e no Y a Potência (dB). O 'Pico Dominante' revela a frequência de \ntransferência (quantas gotas/pulsos por segundo ocorrem).", justify="left").pack(anchor="w", padx=10)
        
        img2_path = res_dir / "2_PSD.png"
        if img2_path.exists():
            img2 = ctk.CTkImage(light_image=Image.open(img2_path), dark_image=Image.open(img2_path), size=(500, 300))
            ctk.CTkLabel(scroll, text="", image=img2).pack(pady=10)
            
        # 3. WAVELET
        ctk.CTkLabel(scroll, text="3. Espectrograma Wavelet (Morlet)", font=ctk.CTkFont(size=16, weight="bold"), text_color="#3B82F6").pack(pady=(20, 5), anchor="w")
        ctk.CTkLabel(scroll, text="Une o Tempo e a Frequência numa imagem 2D. Cores quentes (Amarelo/Vermelho) \nmostram onde ocorreu um evento de altíssima energia (dB).\nPerfeito para rastrear instabilidades pontuais no arco que a FFT (Welch) ofuscaria.", justify="left").pack(anchor="w", padx=10)
        
        img3_path = res_dir / "3_WAVELET.png"
        if img3_path.exists():
            img3 = ctk.CTkImage(light_image=Image.open(img3_path), dark_image=Image.open(img3_path), size=(500, 300))
            ctk.CTkLabel(scroll, text="", image=img3).pack(pady=10)
            
        # 4. TABELA
        ctk.CTkLabel(scroll, text="4. Tabela de Extração (Features)", font=ctk.CTkFont(size=16, weight="bold"), text_color="#3B82F6").pack(pady=(20, 5), anchor="w")
        tabela_desc = (
            "A tabela resume toda a matemática do áudio para o Modelo Preditivo Random Forest.\n"
            "• Energia Média: Raiz quadrada média (RMS) de toda a onda.\n"
            "• Variância: Mede a dispersão. Variância alta = arco instável ou Curto-Circuito caótico.\n"
            "• Cruzamento Zero: Quantas vezes a onda de som 'cortou' o eixo 0. Reflete a frequência de engasgos.\n"
            "• Freq. Pico Hz: Exatamente o ponto mais alto do gráfico PSD (Item 2).\n"
            "• Energia Espectral: A área total (integral) do gráfico PSD."
        )
        ctk.CTkLabel(scroll, text=tabela_desc, justify="left").pack(anchor="w", padx=10, pady=(0, 20))
