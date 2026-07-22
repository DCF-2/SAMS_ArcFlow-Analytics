import customtkinter as ctk
from tkinter import ttk
import os
from pathlib import Path
import threading
import numpy as np
import pandas as pd
from scipy.io import wavfile
import joblib

from core.dsp_processor import DSPProcessor
from core.worker_thread import WorkerThread
import utils.config as config

# Componentes da UI
from ui.windows.splash import SplashScreen
from ui.windows.settings_window import SettingsWindow

from ui.panels.explorer_panel import ExplorerPanel
from ui.panels.workspace_panel import WorkspacePanel
from ui.panels.ai_panel import AIPanel

try:
    from moviepy.editor import VideoFileClip
except ImportError:
    try:
        from moviepy import VideoFileClip
    except ImportError:
        pass

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.withdraw() # Hide until splash screen finishes
        
        self.title("SAMS - ArcFlow Analytics V1.0")
        self.geometry("1800x950")
        self.minsize(1400, 800)
        
        ctk.set_appearance_mode(config.GUI_CONFIG['THEME'])
        ctk.set_default_color_theme(config.GUI_CONFIG['COLOR_THEME'])
        
        self.rf_model = None
        self.loaded_trials = {}
        self.current_trial_name = None
        self.current_features_cache = None
        self.processing = False
        self.log_history = []
        
        self.settings_window = None
        
        self._load_ml_model()
        
        # Estrutura Principal
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TPanedwindow", background="#1e1e1e")
        
        self.paned_main = ttk.PanedWindow(self, orient="horizontal")
        self.paned_main.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        # Inicializando os Paineis Modulares
        self.explorer_panel = ExplorerPanel(self.paned_main, self)
        self.workspace_panel = WorkspacePanel(self.paned_main, self)
        self.ai_panel = AIPanel(self.paned_main, self)
        
        self.paned_main.add(self.explorer_panel, weight=0)
        self.paned_main.add(self.workspace_panel, weight=1)
        self.paned_main.add(self.ai_panel, weight=0)
        
        self.log("SAMS ArcFlow Analytics V1.0 Iniciado.")
        
        # Splash Screen
        self.splash = SplashScreen(self)

    def _load_ml_model(self):
        try:
            model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", "rf_model_sams.pkl")
            if os.path.exists(model_path):
                self.rf_model = joblib.load(model_path)
            else:
                self.log(f"AVISO: Modelo {model_path} não encontrado.")
        except Exception as e:
            self.log(f"ERRO ML: {e}")

    def log(self, message):
        print(f"[ LOG ] {message}")
        if self.settings_window and self.settings_window.winfo_exists():
            formatted = self.settings_window.append_log(message)
            self.log_history.append(formatted)
        else:
            self.log_history.append(f"[CACHE] {message}")

    def open_settings(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self)
        else:
            self.settings_window.focus()

    # =========================================================================
    # LÓGICA DE PROCESSAMENTO (MVC Controller)
    # =========================================================================
    def on_file_selected(self, filepath):
        if self.processing: return
        self.current_trial_name = os.path.basename(filepath)
        
        # Persistência de Ensaios: Evitar recálculo se já processou
        if self.current_trial_name in self.loaded_trials:
            self.log(f"Recuperando {self.current_trial_name} do Cache.")
            self._load_from_cache(self.current_trial_name)
            return
            
        self.ai_panel.set_ml_result("Processando...", "gray")
        self.explorer_panel.prog_bar.set(0.1)
        self.explorer_panel.lbl_prog.configure(text="Iniciando Leitura...")
        self.processing = True
        
        threading.Thread(target=self._process_single_file, args=(filepath,), daemon=True).start()

    def on_file_selected_from_cache(self, filename):
        if self.processing: return
        if filename in self.loaded_trials:
            self.current_trial_name = filename
            self.log(f"Trocando aba para cache: {filename}")
            self._load_from_cache(filename)

    def _load_from_cache(self, name):
        data = self.loaded_trials[name]
        f_df = data['features']
        pred = data['pred']
        
        self.current_features_cache = f_df
        cor = "#10B981" if pred == "Spray" else "#3B82F6" if pred == "Globular" else "#EF4444"
        self.ai_panel.set_ml_result(pred, cor)
        self.workspace_panel.update_plots(data, name)
        
        # Limpa barras do explorer
        self.explorer_panel.prog_bar.set(1.0)
        self.explorer_panel.lbl_prog.configure(text="Carregado da memória.")

    def _process_single_file(self, path):
        name = os.path.basename(path)
        self.after(0, lambda: self.log(f"Extraindo features de: {name}"))
        try:
            ext = Path(path).suffix.lower()
            if ext == '.mp4':
                video = VideoFileClip(path)
                audio_filename = Path(path).stem + "_audio.wav"
                audio_path = os.path.join(os.path.dirname(path), audio_filename)
                video.audio.write_audiofile(audio_path, logger=None)
                video.close()
                fs, audio_data = wavfile.read(audio_path)
            else:
                audio_path = path
                fs, audio_data = wavfile.read(audio_path)
            
            self.after(0, lambda: self._update_prog(0.3, "Normalizando Sinal..."))
            if len(audio_data.shape) > 1: audio_data = np.mean(audio_data, axis=1)
            audio_data = audio_data.astype(np.float64)
            audio_data /= (np.max(np.abs(audio_data)) + 1e-9)
            
            self.after(0, lambda: self._update_prog(0.5, "Calculando PSD (Welch)..."))
            t = np.arange(len(audio_data)) / fs
            f, Pxx = DSPProcessor.calcular_psd_welch(audio_data, fs, config.DSP_CONFIG['WELCH_NPERSEG'])
            
            self.after(0, lambda: self._update_prog(0.8, "Aplicando Wavelet Morlet..."))
            freqs = np.linspace(config.DSP_CONFIG['FREQ_MIN'], config.DSP_CONFIG['FREQ_MAX'], config.DSP_CONFIG['NUM_SCALES'])
            coefs, t_cwt = DSPProcessor.cwt_morlet_otimizada(audio_data, fs, freqs)
            
            self.after(0, lambda: self._update_prog(0.9, "Extraindo Features ML..."))
            energia_media = np.sqrt(np.mean(audio_data**2))
            variancia_sinal = np.var(audio_data)
            taxa_cruzamento_zero = np.sum(np.diff(np.sign(audio_data)) != 0)
            indice_pico = np.argmax(Pxx)
            frequencia_pico_hz = f[indice_pico]
            energia_espectral_total = np.trapezoid(y=Pxx, x=f)
            
            features_df = pd.DataFrame([{
                'energia_media': energia_media,
                'variancia_sinal': variancia_sinal,
                'taxa_cruzamento_zero': taxa_cruzamento_zero,
                'frequencia_pico_hz': frequencia_pico_hz,
                'energia_espectral_total': energia_espectral_total
            }])
            
            # Predict
            predicao = "Desconhecido"
            if self.rf_model:
                predicao = self.rf_model.predict(features_df)[0]
            
            # Save to Cache
            self.loaded_trials[name] = {
                'time': {'t': t, 'signal': audio_data},
                'psd': {'f': f, 'Pxx': Pxx, 'fs': fs},
                'wavelet': {'coefs': coefs, 't': t_cwt, 'freqs': freqs},
                'features': features_df,
                'pred': predicao
            }
            
            self.after(0, lambda: self._update_prog(1.0, "Pronto!"))
            self.after(0, lambda: self._update_ui_after_process(name, features_df, predicao))
        except Exception as e:
            self.after(0, lambda: self.log(f"ERRO: {e}"))
            self.after(0, lambda: self.ai_panel.set_ml_result("Erro DSP", "red"))
            self.after(0, lambda: self._update_prog(0, "Falhou."))
            self.processing = False

    def _update_prog(self, val, text):
        self.explorer_panel.prog_bar.set(val)
        self.explorer_panel.lbl_prog.configure(text=f"Processamento: {int(val*100)}% - {text}")

    def _update_ui_after_process(self, name, features_df, predicao):
        self.current_features_cache = features_df
        cor = "#10B981" if predicao == "Spray" else "#3B82F6" if predicao == "Globular" else "#EF4444"
        self.ai_panel.set_ml_result(predicao, cor)
        self.workspace_panel.append_dataset_row(name, predicao, features_df)
        self.workspace_panel.update_plots(self.loaded_trials[name], name)
        self.processing = False
