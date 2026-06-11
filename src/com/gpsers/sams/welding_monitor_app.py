"""
welding_monitor_app.py
======================
Aplicação Principal de Monitoramento de Soldagem (SAMS)
Versão: 4.0 (Enterprise Dashboard com Integração de Agente IA Gemini)
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter
import os
import io
import threading
import datetime
from pathlib import Path

# Ajuste de compatibilidade MoviePy
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    try:
        from moviepy import VideoFileClip
    except ImportError:
        print("[SISTEMA] Aviso: Biblioteca MoviePy não encontrada.")

# Integração com a API do Gemini
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("[SISTEMA] Aviso: Biblioteca google-genai não instalada. Instale com 'pip install google-genai'")

from dsp_processor import DSPProcessor
from worker_thread import WorkerThread
import config

class GeminiAgentWindow(ctk.CTkToplevel):
    """
    Janela dedicada ao Agente de IA que se comunica com o Gemini
    para analisar visualmente os gráficos gerados.
    """
    def __init__(self, parent, app_instance):
        super().__init__(parent)
        self.app = app_instance
        self.title("SAMS - Agente de Análise IA")
        self.geometry("600x700")
        self.minsize(500, 600)
        
        # Garante que a janela fica visível por cima da principal
        self.attributes("-topmost", True)
        
        # Configuração do Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Cabeçalho do Agente
        self.lbl_title = ctk.CTkLabel(
            self, text="🤖 Engenheiro Analista IA (MIG/MAG)",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.lbl_title.pack(padx=20, pady=15)
        
        # Área de exibição do relatório/chat
        self.txt_analysis = ctk.CTkTextbox(
            self, font=("Consolas", 12), text_color="#ffffff", fg_color="#1a1a1a"
        )
        self.txt_analysis.pack(padx=20, pady=10, fill="both", expand=True)
        self.txt_analysis.insert("0.0", "Aguardando comando... Clique em 'Executar Diagnóstico' para enviar os dados atuais ao Gemini.")
        self.txt_analysis.configure(state="disabled")
        
        # Botão de Ação
        self.btn_run = ctk.CTkButton(
            self, text="⚡ EXECUTAR DIAGNÓSTICO DIGITAL",
            height=45, font=ctk.CTkFont(weight="bold"),
            fg_color="#7289da", hover_color="#5b73c7",
            command=self.start_ai_analysis
        )
        self.btn_run.pack(padx=20, pady=15, fill="x")

    def start_ai_analysis(self):
        """Dispara a análise da IA numa thread secundária para não travar a interface"""
        if not self.app.plots_ready:
            messagebox.showwarning("Aviso", "Por favor, processe um ensaio antes de solicitar a análise do Agente!")
            return
            
        self.btn_run.configure(state="disabled", text="🤖 AGENTE ESTÁ A PENSAR...")
        self.txt_analysis.configure(state="normal")
        self.txt_analysis.delete("0.0", "end")
        self.txt_analysis.insert("0.0", "🤖 [Agente SAMS]: Capturando gráficos em tempo de execução e empacotando buffers de imagem...\nConectando com o servidor Gemini...")
        self.txt_analysis.configure(state="disabled")
        
        threading.Thread(target=self._call_gemini_api, daemon=True).start()

    def _call_gemini_api(self):
        try:
            # Captura o nome do ensaio atual para identificação
            nome_ensaio = self.app.current_trial_name if self.app.current_trial_name else "Ensaio Desconhecido"
            trial_data = self.app.loaded_trials.get(self.app.current_trial_name)
            
            if not trial_data:
                raise ValueError("Dados do ensaio não encontrados na memória.")

            self._update_ui_text("🤖 [Agente SAMS]: Extraindo fatia de alta resolução (Zoom de 0.5s) nas zonas ativas para evitar aliasing visual...\nConectando com o servidor Gemini...")

            # =================================================================
            # 1. O SEGREDO: PREPARAR O "ZOOM" EXCLUSIVO PARA A IA
            # =================================================================
            fs = trial_data['psd']['fs']
            signal = trial_data['time']['signal']
            t = trial_data['time']['t']
            
            # Encontrar o índice de maior energia (garantir que pegamos no meio da soldadura)
            max_idx = np.argmax(np.abs(signal))
            
            # Criar uma janela de 0.5 segundos em torno desse pico
            window_samples = int(fs * 0.5)
            # Recuamos 10% da janela para trás do pico para garantir que apanhamos contexto
            start_idx = max(0, max_idx - int(window_samples * 0.1)) 
            end_idx = min(len(signal), start_idx + window_samples)
            
            t_slice = t[start_idx:end_idx]
            signal_slice = signal[start_idx:end_idx]
            
            # Fatiar a Wavelet para o mesmo período de tempo
            t_cwt = trial_data['wavelet']['t']
            coefs = trial_data['wavelet']['coefs']
            freqs = trial_data['wavelet']['freqs']
            
            start_w = np.searchsorted(t_cwt, t_slice[0])
            end_w = np.searchsorted(t_cwt, t_slice[-1])
            t_cwt_slice = t_cwt[start_w:end_w]
            coefs_slice = coefs[:, start_w:end_w]

            # Gerar as imagens exclusivas da IA (em memória)
            img_time = self._generate_ai_time_plot(t_slice, signal_slice)
            img_wavelet = self._generate_ai_wavelet_plot(t_cwt_slice, freqs, coefs_slice)
            
            # O PSD não sofre de aliasing temporal, enviamos o que está na tela
            img_psd = self._fig_to_jpeg_bytes(self.app.fig_fft)

            # =================================================================
            # 2. O NOVO PROMPT DE TREINO (AFINADO PARA GLOBULAR E NOME DO ARQUIVO)
            # =================================================================
            prompt = f"""
            És o Agente SAMS (Sistema de Análise de Modos de Soldadura), um especialista avançado em Processamento Digital de Sinal (DSP) e diagnóstico acústico de processos de soldadura (MIG/MAG). A tua missão é analisar conjuntos de três gráficos acústicos e classificar, com precisão absoluta, qual o modo de transferência metálica utilizado: Curto-Circuito, Globular ou Spray.

            **Regra de Ouro (Atenção Máxima)**
            Os gráficos de Tempo e Wavelet que recebeste têm um ZOOM de 0.5 segundos focado estritamente na zona de soldadura ativa para que possas ver os micro-padrões com clareza sem esmagamento visual. A tua métrica principal e fator de desempate será sempre o **Espectrograma Wavelet**.

            **Matriz de Classificação Visual (Zoom 0.5s)**
            Estás a analisar o ensaio: **{nome_ensaio}**. Aplica a seguinte matriz de diagnóstico:

            * **1. MODO CURTO-CIRCUITO (Geometria Vertical / Código de Barras)**
                * **Tempo:** Dezenas de picos agudos e finos, muito repetitivos e rítmicos.
                * **PSD:** Energia concentrada nas baixas frequências (formando uma "montanha" à esquerda do gráfico).
                * **Wavelet (Decisivo):** Presença de um **"código de barras" denso**. Verás múltiplas linhas/pilares verticais perfeitos em tons quentes (vermelho/laranja) muito próximos uns dos outros.

            * **2. MODO GLOBULAR (Geometria Caótica / Impactos Esporádicos e Isolados)**
                * **Tempo:** Caótico e irregular. Num espaço de 0.5s, verás impactos muito esporádicos, com espaços vazios ou sinais fracos entre eles. Falta-lhe a densidade rítmica do Curto-Circuito e a massa contínua do Spray.
                * **PSD:** Espectro ruidoso, instável e flutuante, sem a perfeição de um platô horizontal.
                * **Wavelet (Decisivo):** Presença de **poucas manchas grossas e isoladas ou borrões espaçados**. A energia quebra-se completamente: não forma o código de barras rítmico (Curto-Circuito) nem cria uma linha contínua (Spray). São "explosões" de energia avulsas e desorganizadas no tempo.

            * **3. MODO SPRAY / AEROSSOL (Geometria Horizontal / Fluxo Contínuo)**
                * **Tempo:** Um bloco espesso, denso e altamente contínuo. Não há impactos isolados visíveis, apenas um ruído constante ("chiado").
                * **PSD:** Forma um "platô" horizontal. A energia mantém-se distribuída e nivelada de forma muito estável ao longo das frequências médias.
                * **Wavelet (Decisivo):** Presença clara de **faixas ou bandas horizontais contínuas**. O gráfico mostra um "esfregaço" horizontal ininterrupto, sem pilares verticais e sem borrões vazios.

            **Formato de Saída Exigido**
            A tua resposta deve ser estruturada exatamente desta forma (sem texto introdutório ou de conclusão adicionais):
            **Arquivo Analisado:** {nome_ensaio}
            1. **Análise do Tempo:** (1 a 2 frases focadas na densidade, ritmo ou esporadicidade no zoom).
            2. **Análise do PSD:** (1 a 2 frases focadas na concentração ou distribuição da energia).
            3. **Análise da Wavelet:** (1 a 2 frases focadas estritamente na geometria: código de barras, manchas isoladas ou faixas horizontais).
            4. **Veredicto Final:** [Apenas o nome do modo em maiúsculas, ex: MODO DE TRANSFERÊNCIA: GLOBULAR]
            """
            
            # Inicializa o cliente e faz a chamada API
            client = genai.Client(api_key=config.GEMINI_CONFIG['API_KEY'])
            part_time = types.Part.from_bytes(data=img_time, mime_type="image/jpeg")
            part_psd = types.Part.from_bytes(data=img_psd, mime_type="image/jpeg")
            part_wavelet = types.Part.from_bytes(data=img_wavelet, mime_type="image/jpeg")
            
            response = client.models.generate_content(
                model=config.GEMINI_CONFIG['MODEL_NAME'],
                contents=[prompt, part_time, part_psd, part_wavelet],
                config=types.GenerateContentConfig(
                    temperature=0.0 # Temperatura ZERO para classificação puramente lógica
                )
            )
            
            self._update_ui_text(response.text)
            
        except Exception as e:
            self._update_ui_text(f"❌ Erro ao comunicar com o Agente Gemini:\n{str(e)}")
        finally:
            self.app.after(0, lambda: self.btn_run.configure(state="normal", text="⚡ EXECUTAR DIAGNÓSTICO DIGITAL"))

    # =========================================================================
    # FUNÇÕES GERADORAS DE GRÁFICOS FANTASMAS (SÓ PARA A IA)
    # =========================================================================
    def _generate_ai_time_plot(self, t, signal):
        """Gera um gráfico do Tempo focado sem renderizar na interface"""
        from matplotlib.figure import Figure
        fig = Figure(figsize=(8, 5), dpi=100, facecolor='#1e1e1e')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#1e1e1e')
        ax.plot(t, signal, color='cyan', linewidth=1)
        ax.set_title("ZOOM IA - Domínio do Tempo (0.5s)", color='white')
        
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format='jpeg', facecolor=fig.get_facecolor())
        buf.seek(0)
        return buf.read()

    def _generate_ai_wavelet_plot(self, t, freqs, coefs):
        """Gera um gráfico Wavelet focado sem renderizar na interface"""
        from matplotlib.figure import Figure
        fig = Figure(figsize=(8, 5), dpi=100, facecolor='#1e1e1e')
        ax = fig.add_subplot(111)
        
        magnitude = np.abs(coefs)
        max_val = np.max(magnitude) if np.max(magnitude) > 0 else 1e-12
        magnitude_db = 20 * np.log10((magnitude / max_val) + 1e-12)
        extent = [freqs[0], freqs[-1], t[0], t[-1]]
        
        ax.imshow(magnitude_db.T, aspect='auto', origin='lower', cmap='jet', extent=extent, vmin=-50, vmax=0)
        ax.set_title("ZOOM IA - Espectrograma Wavelet (0.5s)", color='white')
        
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format='jpeg', facecolor=fig.get_facecolor())
        buf.seek(0)
        return buf.read()
      
    def _fig_to_jpeg_bytes(self, fig):
        """Converte uma figura Matplotlib em bytes JPEG diretamente na memória do Python"""
        buf = io.BytesIO()
        fig.savefig(buf, format='jpeg', dpi=120, facecolor=fig.get_facecolor())
        buf.seek(0)
        return buf.read()

    def _update_ui_text(self, text):
        """Garante a inserção segura do texto a partir de outra Thread"""
        self.app.after(0, self._safe_write_text, text)

    def _safe_write_text(self, text):
        self.txt_analysis.configure(state="normal")
        self.txt_analysis.delete("0.0", "end")
        self.txt_analysis.insert("0.0", text)
        self.txt_analysis.configure(state="disabled")


class WeldingMonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # ===== Configuração da Janela Principal =====
        self.title("SAMS - ArcFlow Analytics v4.0")
        self.geometry("1600x900")
        self.minsize(1200, 800)
        
        # Tema
        ctk.set_appearance_mode(config.GUI_CONFIG['THEME'])
        ctk.set_default_color_theme(config.GUI_CONFIG['COLOR_THEME'])
        
        # Banco de Dados de Ensaios Carregados em Memória (Suporte Multi-Ficheiros)
        self.loaded_trials = {}
        self.current_trial_name = None
        
        self.processing = False
        self.plots_ready = False
        self.cbar_wavelet = None # Guarda a referência global para evitar o BUG visual!
        
        # Layout Grid Principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._create_sidebar()
        self._create_main_area()
        
        self.log("Sistema ArcFlow Analytics v4.0 Ativo.")
        self.log("Pronto para importação individual ou em lote.")
        
    def _create_sidebar(self):
        """Cria a barra lateral de controlos, lote e logs"""
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1) # Empurra logs para baixo
        
        # 1. Cabeçalho
        self.lbl_logo = ctk.CTkLabel(
            self.sidebar, text="ArcFlow\nAnalytics", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.lbl_logo.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.lbl_version = ctk.CTkLabel(self.sidebar, text="v4.0 AI Powered", text_color="gray")
        self.lbl_version.grid(row=1, column=0, padx=20, pady=(0, 15))
        
        # 2. Controlos de Entrada de Ficheiros
        self.btn_load_batch = ctk.CTkButton(
            self.sidebar, text="📂 IMPORTAR ARQUIVOS", command=self.load_batch_files,
            height=40, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2c3e50", hover_color="#34495e"
        )
        self.btn_load_batch.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        
        # Menu Suspenso (ComboBox) para selecionar qual ensaio visualizar
        self.lbl_combo = ctk.CTkLabel(self.sidebar, text="Selecionar Ensaio Ativo:", font=("Arial", 11, "bold"), text_color="gray")
        self.lbl_combo.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.combo_trials = ctk.CTkComboBox(
            self.sidebar, values=["Nenhum Carregado"], command=self._on_trial_selected, state="disabled"
        )
        self.combo_trials.grid(row=4, column=0, padx=20, pady=5, sticky="ew")
        
        # 3. Controlos Avançados (Agente IA e Exportar)
        self.btn_agent = ctk.CTkButton(
            self.sidebar, text="🤖 CONSULTAR AGENTE IA", command=self.open_ai_agent,
            height=45, font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#7289da", hover_color="#5b73c7"
        )
        self.btn_agent.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_export = ctk.CTkButton(
            self.sidebar, text="💾 EXPORTAR RELATÓRIO", command=self.export_report,
            height=40, font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2da44e", hover_color="#2c974b", state="disabled"
        )
        self.btn_export.grid(row=6, column=0, padx=20, pady=5, sticky="ew")
        
        # 4. Console de Logs
        self.log_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.log_frame.grid(row=7, column=0, padx=20, pady=10, sticky="nsew")
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.log_frame, text="LOG DO SISTEMA:", anchor="w", font=("Consolas", 12, "bold")).grid(row=0, column=0, sticky="w")
        
        self.console = ctk.CTkTextbox(
            self.log_frame, font=("Consolas", 11), text_color="#00ff00", fg_color="#101010", activate_scrollbars=True
        )
        self.console.grid(row=1, column=0, sticky="nsew", pady=5)
        self.console.configure(state="disabled")
        
        # 5. Barra de Progresso
        self.progress_bar = ctk.CTkProgressBar(self.sidebar)
        self.progress_bar.grid(row=8, column=0, padx=20, pady=(10, 20), sticky="ew")
        self.progress_bar.set(0)

    def _create_main_area(self):
        """Área central com as abas e toolbar de gráficos"""
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(fill="both", expand=True)
        
        self.tab_time = self.tabview.add("🔊 SINAL NO TEMPO")
        self.tab_fft = self.tabview.add("📊 FFT / PSD")
        self.tab_wavelet = self.tabview.add("🌊 SPECTROID WAVELET")
        
        self._setup_plot_tabs()

    def _setup_plot_tabs(self):
        def create_plot_area(parent_tab):
            frame = ctk.CTkFrame(parent_tab, fg_color="transparent")
            frame.pack(fill="both", expand=True)
            
            fig = Figure(figsize=(10, 6), dpi=config.GUI_CONFIG['PLOT_DPI'], facecolor=config.GUI_CONFIG['PLOT_FACECOLOR'])
            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
            
            toolbar = NavigationToolbar2Tk(canvas, frame, pack_toolbar=False)
            toolbar.config(background=config.GUI_CONFIG['PLOT_FACECOLOR'])
            toolbar._message_label.config(background=config.GUI_CONFIG['PLOT_FACECOLOR'], foreground='white')
            for button in toolbar.winfo_children():
                button.config(background=config.GUI_CONFIG['PLOT_FACECOLOR'])
            toolbar.update()
            toolbar.pack(side="bottom", fill="x")
            
            return fig, canvas

        self.fig_time, self.canvas_time = create_plot_area(self.tab_time)
        self.ax_time = self.fig_time.add_subplot(111)
        
        self.fig_fft, self.canvas_fft = create_plot_area(self.tab_fft)
        self.ax_fft = self.fig_fft.add_subplot(111)
        
        self.fig_wavelet, self.canvas_wavelet = create_plot_area(self.tab_wavelet)
        self.ax_wavelet = self.fig_wavelet.add_subplot(111)

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {message}\n"
        self.console.configure(state="normal")
        self.console.insert("end", full_msg)
        self.console.see("end")
        self.console.configure(state="disabled")

    # =========================================================================
    # LÓGICA CORE: IMPORTAÇÃO E PROCESSAMENTO EM LOTE
    # =========================================================================
    
    def load_batch_files(self):
        """Seleciona múltiplos arquivos e processa um a um de forma transparente"""
        if self.processing:
            messagebox.showwarning("Aviso", "O sistema está processando dados no momento!")
            return
            
        filepaths = filedialog.askopenfilenames(
            title="Selecione um ou múltiplos arquivos de soldagem",
            filetypes=[("Vídeos e Áudios", "*.mp4 *.wav"), ("Todos os Arquivos", "*.*")]
        )
        
        if not filepaths: return
        
        self.log(f"Lote recebido: {len(filepaths)} arquivo(s) para análise.")
        self.processing = True
        self.btn_load_batch.configure(state="disabled")
        
        # Dispara o processamento em cadeia na Thread secundária
        threading.Thread(target=self._process_queue, args=(filepaths,), daemon=True).start()

    def _process_queue(self, queue):
        """Consome a lista de arquivos sequencialmente sem travar a GUI"""
        for index, path in enumerate(queue):
            name = os.path.basename(path)
            # CORREÇÃO: Usar self.after em vez de self.app.after
            self.after(0, lambda n=name, i=index, t=len(queue): self.log(f"🔄 Processando [{i+1}/{t}]: {n}"))
            
            try:
                # 1. Extração segura
                ext = Path(path).suffix.lower()
                if ext == '.mp4':
                    video = VideoFileClip(path)
                    audio_filename = Path(path).stem + "_audio.wav"
                    audio_path = os.path.join(os.path.dirname(path), audio_filename)
                    video.audio.write_audiofile(audio_path, logger=None)
                    video.close()
                    sample_rate, audio_data = wavfile.read(audio_path)
                else:
                    audio_path = path
                    sample_rate, audio_data = wavfile.read(audio_path)
                
                if len(audio_data.shape) > 1:
                    audio_data = np.mean(audio_data, axis=1)
                
                audio_data = audio_data.astype(np.float64)
                audio_data /= (np.max(np.abs(audio_data)) + 1e-9)
                
                # 2. Execução dos Algoritmos de DSP
                t = np.arange(len(audio_data)) / sample_rate
                f, Pxx = DSPProcessor.calcular_psd_welch(audio_data, sample_rate, config.DSP_CONFIG['WELCH_NPERSEG'])
                
                freqs = np.linspace(config.DSP_CONFIG['FREQ_MIN'], config.DSP_CONFIG['FREQ_MAX'], config.DSP_CONFIG['NUM_SCALES'])
                coefs, t_cwt = DSPProcessor.cwt_morlet_otimizada(audio_data, sample_rate, freqs)
                
                # 3. Cache de dados estruturados em memória
                self.loaded_trials[name] = {
                    'audio_path': audio_path,
                    'time': {'t': t, 'signal': audio_data},
                    'psd': {'f': f, 'Pxx': Pxx, 'fs': sample_rate},
                    'wavelet': {'coefs': coefs, 't': t_cwt, 'freqs': freqs}
                }
                
                # Atualiza progresso da barra
                self.after(0, lambda p=(index+1)/len(queue): self.progress_bar.set(p))
                
            except Exception as e:
                self.after(0, lambda n=name, err=str(e): self.log(f"❌ Falha no arquivo {n}: {err}"))
        
        # Conclusão do lote e atualização da UI principal
        self.after(0, self._on_batch_complete)

    def _on_batch_complete(self):
        self.processing = False
        self.btn_load_batch.configure(state="normal")
        
        if self.loaded_trials:
            # Popula o menu de opções com os nomes dos arquivos analisados
            trial_names = list(self.loaded_trials.keys())
            self.combo_trials.configure(values=trial_names, state="normal")
            # Define o último elemento como ativo automaticamente
            self.combo_trials.set(trial_names[-1])
            self._on_trial_selected(trial_names[-1])
            self.log("✅ Processamento em lote concluído com sucesso!")
        else:
            self.progress_bar.set(0)

    def _on_trial_selected(self, selection):
        """Chamado quando o usuário escolhe outro ensaio no menu suspenso"""
        if selection not in self.loaded_trials: return
        
        self.current_trial_name = selection
        trial_data = self.loaded_trials[selection]
        
        self.log(f"Exibindo dados na tela: {selection}")
        self._update_plots(trial_data)

    # =========================================================================
    # RENDERIZAÇÃO GRÁFICA SEM MEMORY LEAKS (FIX PARA O BUG DA WAVELET)
    # =========================================================================
    
    def _update_plots(self, results):
        try:
            # 1. Domínio do Tempo
            self.ax_time.clear()
            self.ax_time.plot(results['time']['t'], results['time']['signal'], color=config.GUI_CONFIG['COLOR_TIME_SIGNAL'], linewidth=0.5)
            self._dark_style(self.ax_time, f'Domínio do Tempo - {self.current_trial_name}', 'Tempo (s)', 'Amplitude')
            self.fig_time.tight_layout()
            self.canvas_time.draw()
            
            # 2. Espectro PSD
            self.ax_fft.clear()
            Pxx_db = 10 * np.log10(results['psd']['Pxx'] + 1e-12)
            self.ax_fft.fill_between(results['psd']['f'], Pxx_db, -200, color=config.GUI_CONFIG['COLOR_PSD'], alpha=0.2)
            self.ax_fft.plot(results['psd']['f'], Pxx_db, color=config.GUI_CONFIG['COLOR_PSD'], linewidth=1)
            self.ax_fft.set_xlim([0, results['psd']['fs']/2])
            self.ax_fft.set_ylim([np.max(Pxx_db)-80, np.max(Pxx_db)+5])
            self._dark_style(self.ax_fft, 'Espectro de Potência (Welch)', 'Frequência (Hz)', 'dB/Hz')
            self.fig_fft.tight_layout()
            self.canvas_fft.draw()
            
           # ==========================================
            # 3. Wavelet Otimizada 
            # ==========================================
            self.fig_wavelet.clear()
            
            # Recriamos o eixo fresco e com o tamanho correto
            self.ax_wavelet = self.fig_wavelet.add_subplot(111)
            
            magnitude = np.abs(results['wavelet']['coefs'])
            max_val = np.max(magnitude) if np.max(magnitude) > 0 else 1e-12
            magnitude_db = 20 * np.log10((magnitude / max_val) + 1e-12)
            extent = [results['wavelet']['freqs'][0], results['wavelet']['freqs'][-1], results['wavelet']['t'][0], results['wavelet']['t'][-1]]
            
            im = self.ax_wavelet.imshow(
                magnitude_db.T, aspect='auto', origin='lower', cmap=config.GUI_CONFIG['COLORMAP_WAVELET'],
                extent=extent, vmin=-50, vmax=0, interpolation='nearest'
            )
            
            self._dark_style(self.ax_wavelet, f'Spectrograma Wavelet (Morlet) - {self.current_trial_name}', 'Frequência (Hz)', 'Tempo (s)')
            self.ax_wavelet.xaxis.set_major_formatter(ScalarFormatter())
                
            # Como a figura foi limpa, podemos criar a colorbar livremente sem sobreposições
            cbar = self.fig_wavelet.colorbar(im, ax=self.ax_wavelet)
            cbar.set_label('dB', color='white', rotation=0, labelpad=-10, y=1.05)
            cbar.ax.yaxis.set_tick_params(color='white')
            plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
            
            self.fig_wavelet.tight_layout()
            self.canvas_wavelet.draw()
            
            self.plots_ready = True
            self.btn_export.configure(state="normal")
            
        except Exception as e:
            self.log(f"❌ Falha crítica de Plotagem: {e}")

    def _dark_style(self, ax, title, xlabel, ylabel):
        ax.set_facecolor('#1e1e1e')
        ax.tick_params(colors='white', labelsize=9)
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.title.set_color('white')
        ax.title.set_weight('bold')
        for spine in ax.spines.values(): spine.set_edgecolor('#555555')
        ax.grid(True, alpha=0.2, color='white', linestyle='--')
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

    # =========================================================================
    # SUB-JANELAS E FUNÇÕES AUXILIARES
    # =========================================================================

    def open_ai_agent(self):
        """Instancia e abre o Agente inteligente numa janela dedicada"""
        agent_win = GeminiAgentWindow(self, self)
        agent_win.focus()

    def export_report(self):
        if not self.plots_ready: return
        target_dir = filedialog.askdirectory(title="Selecione a Pasta para Salvar o Relatório")
        if not target_dir: return

        try:
            nome_base = Path(self.current_trial_name).stem
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            folder_name = f"Relatorio_{nome_base}_{timestamp}"
            save_path = os.path.join(target_dir, folder_name)
            os.makedirs(save_path, exist_ok=True)
            
            self.fig_time.savefig(os.path.join(save_path, "1_TEMPO.png"), dpi=150, facecolor='#2b2b2b')
            self.fig_fft.savefig(os.path.join(save_path, "2_PSD.png"), dpi=150, facecolor='#2b2b2b')
            self.fig_wavelet.savefig(os.path.join(save_path, "3_WAVELET.png"), dpi=150, facecolor='#2b2b2b')
            
            self.log(f"✅ Exportação concluída em: {folder_name}")
            messagebox.showinfo("Sucesso", f"Relatório salvo em:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))


if __name__ == "__main__":
    app = WeldingMonitorApp()
    app.mainloop()