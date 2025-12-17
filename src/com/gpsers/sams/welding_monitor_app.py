"""
welding_monitor_app.py
======================
Aplicação Principal de Monitoramento de Soldagem
Versão: 3.0 (Professional Dashboard UI)
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
import datetime
import traceback
from pathlib import Path

# Ajuste de compatibilidade MoviePy
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    try:
        from moviepy import VideoFileClip
    except ImportError:
        print("[SISTEMA] Aviso: Biblioteca MoviePy não encontrada.")

from dsp_processor import DSPProcessor
from worker_thread import WorkerThread

class WeldingMonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # ===== Configuração da Janela Principal =====
        self.title("SAMS - ArcFlow Analytics v3.0")
        self.geometry("1600x900")
        self.minsize(1200, 800)
        
        # Tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Variáveis de Estado
        self.audio_data = None
        self.sample_rate = None
        self.video_path = None
        self.audio_path = None
        self.processing = False
        self.plots_ready = False
        
        # Layout Grid Principal (2 Colunas: Sidebar | Main)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._create_sidebar()
        self._create_main_area()
        
        self.log("Sistema ArcFlow Analytics inicializado.")
        self.log("Aguardando entrada de dados...")
        
    def _create_sidebar(self):
        """Cria a barra lateral de controles e logs"""
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1) # Empurra o log para baixo
        
        # 1. Cabeçalho
        self.lbl_logo = ctk.CTkLabel(
            self.sidebar, text="ArcFlow\nAnalytics", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.lbl_logo.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.lbl_version = ctk.CTkLabel(self.sidebar, text="v3.0 Professional", text_color="gray")
        self.lbl_version.grid(row=1, column=0, padx=20, pady=(0, 20))
        
        # 2. Controles Principais
        self.btn_load = ctk.CTkButton(
            self.sidebar, text="📁 CARREGAR VÍDEO", command=self.load_video,
            height=50, font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1f6aa5", hover_color="#144870"
        )
        self.btn_load.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_export = ctk.CTkButton(
            self.sidebar, text="💾 EXPORTAR RELATÓRIO", command=self.export_report,
            height=50, font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2da44e", hover_color="#2c974b", # Verde GitHub
            state="disabled"
        )
        self.btn_export.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        # 3. Separador
        self.separator = ctk.CTkFrame(self.sidebar, height=2, fg_color="gray30")
        self.separator.grid(row=4, column=0, padx=20, pady=20, sticky="ew")
        
        # 4. Console de Logs (O "Print" na Interface)
        self.log_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.log_frame.grid(row=5, column=0, padx=20, pady=10, sticky="nsew")
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.log_frame, text="LOG DE SISTEMA:", anchor="w", font=("Consolas", 12, "bold")).grid(row=0, column=0, sticky="w")
        
        self.console = ctk.CTkTextbox(
            self.log_frame, font=("Consolas", 11), 
            text_color="#00ff00", fg_color="#101010", # Visual Terminal Hacker
            activate_scrollbars=True
        )
        self.console.grid(row=1, column=0, sticky="nsew", pady=5)
        self.console.configure(state="disabled")
        
        # 5. Barra de Progresso (Rodapé)
        self.progress_bar = ctk.CTkProgressBar(self.sidebar)
        self.progress_bar.grid(row=6, column=0, padx=20, pady=(10, 20), sticky="ew")
        self.progress_bar.set(0)

    def _create_main_area(self):
        """Cria a área principal com as abas e gráficos"""
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Abas
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(fill="both", expand=True)
        
        self.tab_time = self.tabview.add("🔊 SINAL NO TEMPO")
        self.tab_fft = self.tabview.add("📊 FFT / PSD")
        self.tab_wavelet = self.tabview.add("🌊 SPECTROID WAVELET")
        
        # Inicializa os plots
        self._setup_plot_tabs()

    def log(self, message):
        """Adiciona mensagem ao console da interface"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {message}\n"
        
        self.console.configure(state="normal")
        self.console.insert("end", full_msg)
        self.console.see("end") # Auto-scroll
        self.console.configure(state="disabled")
        print(full_msg.strip()) # Também imprime no terminal do Python por segurança

    def _setup_plot_tabs(self):
        """Configura os gráficos com Toolbar Integrada"""
        
        def create_plot_area(parent_tab):
            # Frame container
            frame = ctk.CTkFrame(parent_tab, fg_color="transparent")
            frame.pack(fill="both", expand=True)
            
            # Figura Matplotlib Dark Mode
            fig = Figure(figsize=(10, 6), dpi=100, facecolor='#2b2b2b')
            
            # Canvas
            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
            
            # Toolbar customizada
            toolbar = NavigationToolbar2Tk(canvas, frame, pack_toolbar=False)
            toolbar.config(background='#2b2b2b')
            toolbar._message_label.config(background='#2b2b2b', foreground='white')
            for button in toolbar.winfo_children():
                button.config(background='#2b2b2b')
            toolbar.update()
            toolbar.pack(side="bottom", fill="x")
            
            return fig, canvas, toolbar

        self.fig_time, self.canvas_time, self.tb_time = create_plot_area(self.tab_time)
        self.ax_time = self.fig_time.add_subplot(111)
        
        self.fig_fft, self.canvas_fft, self.tb_fft = create_plot_area(self.tab_fft)
        self.ax_fft = self.fig_fft.add_subplot(111)
        
        self.fig_wavelet, self.canvas_wavelet, self.tb_wavelet = create_plot_area(self.tab_wavelet)
        self.ax_wavelet = self.fig_wavelet.add_subplot(111)

    # =========================================================================
    # LÓGICA DE NEGÓCIO (Carregar e Exportar)
    # =========================================================================
    
    def load_video(self):
        if self.processing:
            messagebox.showwarning("Ocupado", "Aguarde o processamento atual terminar!")
            return
            
        filepath = filedialog.askopenfilename(
            title="Selecione o vídeo de soldagem",
            filetypes=[("Vídeos MP4", "*.mp4"), ("Todos os Arquivos", "*.*")]
        )
        
        if not filepath: return
        
        self.video_path = filepath
        self.processing = True
        self.plots_ready = False
        
        # UI Updates
        self.btn_load.configure(state="disabled")
        self.btn_export.configure(state="disabled")
        self.progress_bar.set(0.1)
        self.log(f"Carregando: {os.path.basename(filepath)}")
        self.log("Iniciando extração de áudio...")
        
        worker = WorkerThread(self._on_extraction_complete, self._extract_audio, filepath)
        worker.start()

    def export_report(self):
        """Exporta relatório perguntando onde salvar"""
        if not self.plots_ready: return

        # Pergunta ONDE salvar (NOVO RECURSO)
        target_dir = filedialog.askdirectory(title="Selecione a Pasta para Salvar o Relatório")
        
        if not target_dir:
            self.log("Exportação cancelada pelo usuário.")
            return

        try:
            nome_base = Path(self.audio_path).stem.replace("_audio", "")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            folder_name = f"Relatorio_{nome_base}_{timestamp}"
            save_path = os.path.join(target_dir, folder_name)
            
            os.makedirs(save_path, exist_ok=True)
            self.log(f"Criando pasta: {folder_name}")
            
            # Salva Imagens
            self.fig_time.savefig(os.path.join(save_path, "1_TEMPO.png"), dpi=150, facecolor='#2b2b2b')
            self.fig_fft.savefig(os.path.join(save_path, "2_PSD.png"), dpi=150, facecolor='#2b2b2b')
            self.fig_wavelet.savefig(os.path.join(save_path, "3_WAVELET.png"), dpi=150, facecolor='#2b2b2b')
            
            self.log("✅ Exportação concluída com sucesso!")
            messagebox.showinfo("Sucesso", f"Relatório salvo em:\n{save_path}")
            
        except Exception as e:
            self.log(f"❌ Erro ao exportar: {e}")
            messagebox.showerror("Erro", str(e))

    # =========================================================================
    # WORKERS E CALLBACKS
    # =========================================================================
    
    def _extract_audio(self, video_path):
        # Lógica de extração segura
        video = VideoFileClip(video_path)
        audio_filename = Path(video_path).stem + "_audio.wav"
        audio_path = os.path.join(os.path.dirname(video_path), audio_filename)
        
        video.audio.write_audiofile(audio_path, verbose=False, logger=None)
        video.close()
        
        sample_rate, audio_data = wavfile.read(audio_path)
        if len(audio_data.shape) > 1: 
            audio_data = np.mean(audio_data, axis=1) # Mono
            
        audio_data = audio_data.astype(np.float64)
        audio_data = audio_data / (np.max(np.abs(audio_data)) + 1e-9) # Normaliza
        
        return {'audio_path': audio_path, 'sample_rate': sample_rate, 'audio_data': audio_data}
    
    def _run_dsp(self, audio_data, sample_rate):
        results = {}
        # 1. Tempo
        results['time'] = {'t': np.arange(len(audio_data))/sample_rate, 'signal': audio_data}
        
        # 2. PSD
        f, Pxx = DSPProcessor.calcular_psd_welch(audio_data, sample_rate)
        results['psd'] = {'f': f, 'Pxx': Pxx}
        
        # 3. Wavelet
        freqs = np.linspace(100, sample_rate/2, 150)
        coefs, t_cwt = DSPProcessor.cwt_morlet_otimizada(audio_data, sample_rate, freqs)
        results['wavelet'] = {'coefs': coefs, 't': t_cwt, 'freqs': freqs}
        
        return results

    def _on_extraction_complete(self, result, error):
        if error:
            self.log(f"❌ Erro na extração: {error}")
            self._reset_ui()
            return
            
        self.audio_path = result['audio_path']
        self.sample_rate = result['sample_rate']
        self.audio_data = result['audio_data']
        
        self.log("Áudio extraído com sucesso.")
        self.log(f"Amostras: {len(self.audio_data)} | Taxa: {self.sample_rate}Hz")
        self.log("Iniciando cálculos DSP (FFT + Wavelet)...")
        self.progress_bar.set(0.4)
        
        worker = WorkerThread(self._on_dsp_complete, self._run_dsp, self.audio_data, self.sample_rate)
        worker.start()
        
    def _on_dsp_complete(self, results, error):
        if error:
            self.log(f"❌ Erro DSP: {error}")
            self._reset_ui()
            return
            
        self.log("Cálculos matemáticos concluídos.")
        self.log("Renderizando gráficos...")
        self.after(0, self._update_plots, results)

    def _update_plots(self, results):
        try:
            self._plot_time(results['time'])
            self.progress_bar.set(0.7)
            
            self._plot_psd(results['psd'])
            self.progress_bar.set(0.85)
            
            self._plot_wavelet(results['wavelet'])
            self.progress_bar.set(1.0)
            
            self.log("✅ ANÁLISE COMPLETA!")
            self.plots_ready = True
            self.btn_export.configure(state="normal")
            
        except Exception as e:
            self.log(f"❌ Erro Plotagem: {e}")
        finally:
            self.btn_load.configure(state="normal")
            self.processing = False

    def _reset_ui(self):
        self.processing = False
        self.btn_load.configure(state="normal")
        self.progress_bar.set(0)

    # =========================================================================
    # PLOTAGEM (ESTILO DARK + OCTAVE)
    # =========================================================================
    
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

    def _plot_time(self, data):
        self.ax_time.clear()
        self.ax_time.plot(data['t'], data['signal'], color='#00ffff', linewidth=0.5)
        self._dark_style(self.ax_time, 'Domínio do Tempo', 'Tempo (s)', 'Amplitude')
        self.fig_time.tight_layout()
        self.canvas_time.draw()
        self.log("Gráfico Tempo: Renderizado.")

    def _plot_psd(self, data):
        self.ax_fft.clear()
        Pxx_db = 10 * np.log10(data['Pxx'] + 1e-12)
        self.ax_fft.fill_between(data['f'], Pxx_db, -200, color='#00ff00', alpha=0.2)
        self.ax_fft.plot(data['f'], Pxx_db, color='#00ff00', linewidth=1)
        self.ax_fft.set_xlim([0, self.sample_rate/2])
        self.ax_fft.set_ylim([np.max(Pxx_db)-80, np.max(Pxx_db)+5])
        self._dark_style(self.ax_fft, 'Espectro de Potência (Welch)', 'Frequência (Hz)', 'dB/Hz')
        self.fig_fft.tight_layout()
        self.canvas_fft.draw()
        self.log("Gráfico PSD: Renderizado.")

    def _plot_wavelet(self, data):
        self.ax_wavelet.clear()
        
        # Matemática
        magnitude = np.abs(data['coefs'])
        max_val = np.max(magnitude) if np.max(magnitude) > 0 else 1e-12
        magnitude_db = 20 * np.log10((magnitude / max_val) + 1e-12)
        
        extent = [data['freqs'][0], data['freqs'][-1], data['t'][0], data['t'][-1]]
        
        # Renderização Pixel Perfect (Octave Style)
        im = self.ax_wavelet.imshow(
            magnitude_db.T, aspect='auto', origin='lower', cmap='jet',
            extent=extent, vmin=-50, vmax=0, interpolation='nearest'
        )
        
        self._dark_style(self.ax_wavelet, 'Spectrograma Wavelet (Morlet)', 'Frequência (Hz)', 'Tempo (s)')
        
        # Formatação
        self.ax_wavelet.xaxis.set_major_formatter(ScalarFormatter())
        self.ax_wavelet.ticklabel_format(style='plain', axis='x')

        if hasattr(self, 'cbar_wavelet'): self.cbar_wavelet.remove()
        
        cbar = self.fig_wavelet.colorbar(im, ax=self.ax_wavelet)
        cbar.set_label('dB', color='white', rotation=0, labelpad=-10, y=1.05)
        cbar.ax.yaxis.set_tick_params(color='white')
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
        
        self.fig_wavelet.tight_layout()
        self.canvas_wavelet.draw()
        self.log("Gráfico Wavelet: Renderizado.")