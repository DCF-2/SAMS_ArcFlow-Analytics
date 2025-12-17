"""
welding_monitor_app.py
======================
Aplicação Principal de Monitoramento de Soldagem
Interface Gráfica com CustomTkinter + Matplotlib

Autor: Sistema de Monitoramento de Soldagem
Versão: 2.0
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import os
import traceback
from moviepy.editor import VideoFileClip
from pathlib import Path

# Importa módulos do projeto
from dsp_processor import DSPProcessor
from worker_thread import WorkerThread


class WeldingMonitorApp(ctk.CTk):
    """
    Aplicação Principal de Monitoramento de Soldagem
    
    Arquitetura:
    - GUI: CustomTkinter (tema dark moderno)
    - Plots: Matplotlib integrado via FigureCanvasTkAgg
    - Threading: WorkerThread para manter UI responsiva
    - DSP: Algoritmos otimizados para Raspberry Pi
    """
    
    def __init__(self):
        super().__init__()
        
        # ===== Configuração da Janela =====
        self.title("Sistema de Monitoramento de Soldagem - Análise Espectral v2.0")
        self.geometry("1400x900")
        
        # Configuração do tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # ===== Variáveis de Estado =====
        self.audio_data = None
        self.sample_rate = None
        self.video_path = None
        self.audio_path = None
        self.processing = False
        
        # ===== Criar Interface =====
        self._create_widgets()
        
        print("✓ Aplicação inicializada com sucesso!")
        
    def _create_widgets(self):
        """Constrói toda a interface gráfica"""
        
        # ===== PAINEL SUPERIOR: Controles =====
        self.control_frame = ctk.CTkFrame(self, height=100)
        self.control_frame.pack(side="top", fill="x", padx=10, pady=10)
        
        # Botão carregar vídeo
        self.btn_load = ctk.CTkButton(
            self.control_frame,
            text="📁 Carregar Vídeo MP4",
            command=self.load_video,
            width=200,
            height=40,
            font=("Arial", 14, "bold")
        )
        self.btn_load.pack(side="left", padx=10, pady=20)
        
        # Label de status
        self.status_label = ctk.CTkLabel(
            self.control_frame,
            text="Aguardando arquivo...",
            font=("Arial", 12)
        )
        self.status_label.pack(side="left", padx=20)
        
        # Barra de progresso
        self.progress = ctk.CTkProgressBar(self.control_frame, width=300)
        self.progress.pack(side="left", padx=10)
        self.progress.set(0)
        
        # ===== PAINEL DE ABAS: Visualizações =====
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        
        # Criar abas
        self.tab_time = self.tabview.add("🔊 Sinal no Tempo")
        self.tab_fft = self.tabview.add("📊 FFT/PSD (Welch)")
        self.tab_wavelet = self.tabview.add("🌊 Wavelet (Morlet)")
        
        # Inicializar plots
        self._setup_plot_tabs()
        
    def _setup_plot_tabs(self):
        """Configura os canvas de matplotlib em cada aba"""
        
        # ===== ABA 1: Sinal no Tempo =====
        self.fig_time = Figure(figsize=(12, 6), dpi=100, facecolor='#2b2b2b')
        self.ax_time = self.fig_time.add_subplot(111)
        self.ax_time.set_facecolor('#1e1e1e')
        self.ax_time.set_xlabel('Tempo (s)', color='white')
        self.ax_time.set_ylabel('Amplitude', color='white')
        self.ax_time.set_title('Sinal de Áudio no Domínio do Tempo', color='white')
        self.ax_time.tick_params(colors='white')
        self.ax_time.grid(True, alpha=0.3)
        self.canvas_time = FigureCanvasTkAgg(self.fig_time, master=self.tab_time)
        self.canvas_time.get_tk_widget().pack(fill="both", expand=True)
        
        # ===== ABA 2: FFT/PSD =====
        self.fig_fft = Figure(figsize=(12, 6), dpi=100, facecolor='#2b2b2b')
        self.ax_fft = self.fig_fft.add_subplot(111)
        self.ax_fft.set_facecolor('#1e1e1e')
        self.ax_fft.set_xlabel('Frequência (Hz)', color='white')
        self.ax_fft.set_ylabel('PSD (dB/Hz)', color='white')
        self.ax_fft.set_title('Densidade Espectral de Potência - Método de Welch', color='white')
        self.ax_fft.tick_params(colors='white')
        self.ax_fft.grid(True, alpha=0.3)
        self.canvas_fft = FigureCanvasTkAgg(self.fig_fft, master=self.tab_fft)
        self.canvas_fft.get_tk_widget().pack(fill="both", expand=True)
        
        # ===== ABA 3: Wavelet =====
        self.fig_wavelet = Figure(figsize=(12, 6), dpi=100, facecolor='#2b2b2b')
        self.ax_wavelet = self.fig_wavelet.add_subplot(111)
        self.ax_wavelet.set_facecolor('#1e1e1e')
        self.ax_wavelet.set_xlabel('Tempo (s)', color='white')
        self.ax_wavelet.set_ylabel('Frequência (Hz)', color='white')
        self.ax_wavelet.set_title('Espectrograma Wavelet - Morlet CWT', color='white')
        self.ax_wavelet.tick_params(colors='white')
        self.canvas_wavelet = FigureCanvasTkAgg(self.fig_wavelet, master=self.tab_wavelet)
        self.canvas_wavelet.get_tk_widget().pack(fill="both", expand=True)
        
    # =========================================================================
    # MÉTODOS DE CONTROLE E CARREGAMENTO
    # =========================================================================
    
    def load_video(self):
        """Carrega vídeo MP4 e inicia o pipeline de processamento"""
        if self.processing:
            messagebox.showwarning("Aviso", "Aguarde o processamento atual terminar!")
            return
            
        filepath = filedialog.askopenfilename(
            title="Selecione o vídeo de soldagem",
            filetypes=[("Vídeos MP4", "*.mp4"), ("Todos os arquivos", "*.*")]
        )
        
        if not filepath:
            return
        
        self.video_path = filepath
        self.processing = True
        self.btn_load.configure(state="disabled")
        self.status_label.configure(text="Extraindo áudio do vídeo...")
        self.progress.set(0.2)
        
        # Inicia thread de processamento
        worker = WorkerThread(
            self._on_extraction_complete,
            self._extract_audio,
            filepath
        )
        worker.start()
    
    # =========================================================================
    # PIPELINE DE PROCESSAMENTO (Executa em WorkerThread)
    # =========================================================================
    
    def _extract_audio(self, video_path):
        """
        Extrai áudio do vídeo MP4 usando MoviePy
        
        Returns:
            dict: {audio_path, sample_rate, audio_data}
        """
        print(f"[INFO] Iniciando extração de áudio: {video_path}")
        video = VideoFileClip(video_path)
        
        # Define caminho do áudio
        audio_filename = Path(video_path).stem + "_audio.wav"
        audio_path = os.path.join(os.path.dirname(video_path), audio_filename)
        
        # Extrai e salva áudio
        print(f"[INFO] Salvando áudio em: {audio_path}")
        video.audio.write_audiofile(audio_path, verbose=False, logger=None)
        video.close()
        
        # Carrega áudio como numpy array
        sample_rate, audio_data = wavfile.read(audio_path)
        
        # Converte estéreo -> mono (se necessário)
        if len(audio_data.shape) > 1:
            print(f"[INFO] Convertendo estéreo -> mono")
            audio_data = np.mean(audio_data, axis=1)
        
        # Normaliza para [-1, 1]
        audio_data = audio_data.astype(np.float64)
        audio_data = audio_data / np.max(np.abs(audio_data))
        
        print(f"[INFO] Áudio carregado: {len(audio_data)/sample_rate:.2f}s @ {sample_rate}Hz")
        
        return {
            'audio_path': audio_path,
            'sample_rate': sample_rate,
            'audio_data': audio_data
        }
    
    def _run_all_analysis(self, audio_data, sample_rate):
        """
        Executa todas as análises DSP
        
        Returns:
            dict: {time, psd, wavelet} com resultados
        """
        results = {}
        
        # 1. Sinal no tempo
        print("[INFO] Preparando visualização temporal...")
        t = np.arange(len(audio_data)) / sample_rate
        results['time'] = {'t': t, 'signal': audio_data}
        
        # 2. PSD Welch
        print("[INFO] Calculando PSD (Welch)...")
        f, Pxx = DSPProcessor.calcular_psd_welch(audio_data, sample_rate)
        results['psd'] = {'f': f, 'Pxx': Pxx}
        
        # 3. Wavelet CWT
        print("[INFO] Calculando CWT (Morlet) - isso pode demorar...")
        freqs = np.logspace(np.log10(50), np.log10(5000), 100)
        coefs, t_cwt = DSPProcessor.cwt_morlet_otimizada(audio_data, sample_rate, freqs)
        results['wavelet'] = {'coefs': coefs, 't': t_cwt, 'freqs': freqs}
        
        print("[INFO] Análises concluídas!")
        return results
    
    # =========================================================================
    # CALLBACKS (Thread-Safe com after())
    # =========================================================================
    
    def _on_extraction_complete(self, result, error):
        """Callback após extração do áudio"""
        if error:
            self.after(0, self._show_error, "Erro na Extração", error)
            return
        
        # Armazena dados
        self.audio_path = result['audio_path']
        self.sample_rate = result['sample_rate']
        self.audio_data = result['audio_data']
        
        # Atualiza UI
        self.status_label.configure(text="⏳ Processando análises DSP...")
        self.progress.set(0.5)
        
        # Inicia análises DSP em nova thread
        worker = WorkerThread(
            self._on_analysis_complete,
            self._run_all_analysis,
            self.audio_data,
            self.sample_rate
        )
        worker.start()
    
    def _on_analysis_complete(self, results, error):
        """Callback após análises DSP"""
        if error:
            self.after(0, self._show_error, "Erro no Processamento", error)
            return
        
        # Agenda atualização dos plots na thread principal
        self.after(0, self._update_all_plots, results)
    
    def _show_error(self, title, message):
        """Mostra erro e reseta estado (thread-safe)"""
        messagebox.showerror(title, f"{message}")
        self.status_label.configure(text=f"❌ {title}")
        self.progress.set(0)
        self.btn_load.configure(state="normal")
        self.processing = False
    
    def _update_all_plots(self, results):
        """Atualiza todos os plots (deve ser chamado na thread principal)"""
        try:
            print("[INFO] Atualizando visualizações...")
            
            self._plot_time_domain(results['time'])
            self.progress.set(0.7)
            
            self._plot_psd(results['psd'])
            self.progress.set(0.85)
            
            self._plot_wavelet(results['wavelet'])
            self.progress.set(1.0)
            
            # Status final
            duracao = len(self.audio_data) / self.sample_rate
            self.status_label.configure(
                text=f"✅ Análise completa! Duração: {duracao:.2f}s @ {self.sample_rate}Hz"
            )
            print("[INFO] Processo concluído com sucesso!")
            
        except Exception as e:
            error_msg = f"Erro ao plotar: {str(e)}\n{traceback.format_exc()}"
            print(f"[ERRO] {error_msg}")
            messagebox.showerror("Erro", error_msg)
        
        finally:
            self.btn_load.configure(state="normal")
            self.processing = False
    
    # =========================================================================
    # MÉTODOS DE PLOTAGEM
    # =========================================================================
    
    def _plot_time_domain(self, data):
        """Plota sinal no domínio do tempo"""
        self.ax_time.clear()
        self.ax_time.plot(data['t'], data['signal'], color='#00d9ff', linewidth=0.5)
        self.ax_time.set_xlabel('Tempo (s)', color='white', fontsize=11)
        self.ax_time.set_ylabel('Amplitude Normalizada', color='white', fontsize=11)
        self.ax_time.set_title('Sinal de Áudio no Domínio do Tempo', 
                                color='white', fontsize=13, fontweight='bold')
        self.ax_time.tick_params(colors='white')
        self.ax_time.grid(True, alpha=0.3, color='gray', linestyle='--')
        self.ax_time.set_facecolor('#1e1e1e')
        self.fig_time.tight_layout()
        self.canvas_time.draw()
    
    def _plot_psd(self, data):
        """Plota densidade espectral de potência"""
        self.ax_fft.clear()
        Pxx_db = 10 * np.log10(data['Pxx'] + 1e-12)
        self.ax_fft.plot(data['f'], Pxx_db, color='#00ff88', linewidth=1.5)
        self.ax_fft.set_xlabel('Frequência (Hz)', color='white', fontsize=11)
        self.ax_fft.set_ylabel('PSD (dB/Hz)', color='white', fontsize=11)
        self.ax_fft.set_title('Densidade Espectral de Potência - Método de Welch (Hanning)', 
                              color='white', fontsize=13, fontweight='bold')
        self.ax_fft.set_xlim([0, self.sample_rate/2])
        self.ax_fft.tick_params(colors='white')
        self.ax_fft.grid(True, alpha=0.3, color='gray', linestyle='--')
        self.ax_fft.set_facecolor('#1e1e1e')
        self.fig_fft.tight_layout()
        self.canvas_fft.draw()
    
    def _plot_wavelet(self, data):
        """Plota espectrograma wavelet"""
        self.ax_wavelet.clear()
        
        # Calcula magnitude em dB
        magnitude = np.abs(data['coefs'])
        magnitude_db = 20 * np.log10(magnitude + 1e-12)
        
        # Plota espectrograma
        im = self.ax_wavelet.pcolormesh(
            data['t'], data['freqs'], magnitude_db,
            shading='auto', cmap='jet', 
            vmin=np.percentile(magnitude_db, 5),
            vmax=np.percentile(magnitude_db, 95)
        )
        
        self.ax_wavelet.set_xlabel('Tempo (s)', color='white', fontsize=11)
        self.ax_wavelet.set_ylabel('Frequência (Hz)', color='white', fontsize=11)
        self.ax_wavelet.set_title('Espectrograma Wavelet - Transformada de Morlet (Otimizada)', 
                                  color='white', fontsize=13, fontweight='bold')
        self.ax_wavelet.set_yscale('log')
        self.ax_wavelet.tick_params(colors='white')
        self.ax_wavelet.set_facecolor('#1e1e1e')
        
        # Adiciona colorbar
        cbar = self.fig_wavelet.colorbar(im, ax=self.ax_wavelet)
        cbar.set_label('Magnitude (dB)', color='white', fontsize=10)
        cbar.ax.yaxis.set_tick_params(color='white')
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
        
        self.fig_wavelet.tight_layout()
        self.canvas_wavelet.draw()