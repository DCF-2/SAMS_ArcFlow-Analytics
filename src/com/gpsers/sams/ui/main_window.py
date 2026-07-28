import customtkinter as ctk
from tkinter import ttk, filedialog
import os
import json
import threading
from pathlib import Path
from PIL import Image, ImageTk
import joblib
import pandas as pd
import numpy as np
from scipy.io import wavfile
import concurrent.futures
from ui.components.error_window import show_error
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    from moviepy import VideoFileClip
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
        self.processing = False
        self.current_features_cache = None
        self.current_trial_name = None
        self.loaded_trials = {} # RAM cache { 'name': dict_results }
        self.dataset_history = {} # Metadados leves para tabela
        
        self.log_history = []
        
        self.shared_model_var = ctk.StringVar(value="Llama-3.2-3B-Instruct-Q4_0.gguf")
        
        self.settings_window = None
        
        self._load_ml_model()
        
        # Menu Bar (VSCode Style)
        self.menubar = ctk.CTkFrame(self, height=30, corner_radius=0, fg_color="#181818")
        self.menubar.grid(row=0, column=0, sticky="ew")
        self.menubar.grid_propagate(False)
        
        btn_file = ctk.CTkButton(self.menubar, text="Arquivo", width=50, height=20, fg_color="transparent", hover_color="#2b2b2b", command=self._menu_file)
        btn_file.pack(side="left", padx=5, pady=5)
        
        btn_view = ctk.CTkButton(self.menubar, text="Visualizar", width=50, height=20, fg_color="transparent", hover_color="#2b2b2b", command=self._menu_view)
        btn_view.pack(side="left", padx=5, pady=5)
        
        btn_help = ctk.CTkButton(self.menubar, text="Ajuda", width=50, height=20, fg_color="transparent", hover_color="#2b2b2b", command=self._menu_help)
        btn_help.pack(side="left", padx=5, pady=5)
        
        # Estrutura Principal
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TPanedwindow", background="#1e1e1e")
        
        self.paned_main = ttk.PanedWindow(self, orient="horizontal")
        self.paned_main.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        
        # Inicializando os Paineis Modulares
        self.explorer_panel = ExplorerPanel(self.paned_main, self)
        self.workspace_panel = WorkspacePanel(self.paned_main, self)
        self.ai_panel = AIPanel(self.paned_main, self)
        
        self.paned_main.add(self.explorer_panel, weight=0)
        self.paned_main.add(self.workspace_panel, weight=1)
        self.paned_main.add(self.ai_panel, weight=0)
        
        self.load_session()
        
        # Splash Screen
        self.splash = SplashScreen(self)
        
        # Dispara Auto-Load Assíncrono
        threading.Thread(target=self._auto_load_cache, daemon=True).start()

    def _load_ml_model(self):
        try:
            model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", "rf_model_sams.pkl")
            if os.path.exists(model_path):
                self.rf_model = joblib.load(model_path)
            else:
                self.log(f"AVISO: Modelo {model_path} não encontrado.")
        except Exception as e:
            self.log(f"ERRO ML: {e}")

    def log(self, message, level="INFO"):
        if not hasattr(self, 'logger'): return
        if level == "INFO": self.logger.info(message)
        elif level == "WARNING": self.logger.warning(message)
        elif level == "ERROR": self.logger.error(message)
        elif level == "SUCCESS": self.logger.info(message, extra={'gui_level': 'SUCCESS'})
        elif level == "DEBUG": self.logger.debug(message)

    def open_settings(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self)
        else:
            self.settings_window.focus()

    def _auto_load_cache(self):
        import time
        import json
        time.sleep(2) # Pequeno atraso para as telas renderizarem
        
        self.log("Auto-Load: Verificando cache persistente...")
        cache_dir = Path(__file__).parent.parent / "data" / "cache"
        if not cache_dir.exists(): return
        
        count = 0
        for pkl_file in cache_dir.glob("*.pkl"):
            try:
                name = pkl_file.stem
                meta_file = cache_dir / f"{name}_meta.json"
                if meta_file.exists():
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    # Converter dict de features de volta pra pandas DataFrame se possivel (nao essencial para a tabela pura)
                    import pandas as pd
                    df = pd.DataFrame([meta.get('features', {})]) if meta.get('features') else None
                    self.dataset_history[name] = {
                        'pred': meta.get('pred', 'N/A'),
                        'features': df
                    }
                    count += 1
                else:
                    # Se nao tem JSON, pula para evitar o pico fatal de RAM do OpenBLAS
                    pass
            except: pass
            
        if count > 0:
            self.log(f"Auto-Load: {count} ensaios identificados (Leitura Rápida)!")
            if hasattr(self, 'explorer_panel') and self.explorer_panel:
                self.after(0, self.explorer_panel.refresh_cache_icons)

    def _menu_file(self):
        self.explorer_panel.load_directory()
        
    def _menu_view(self):
        # Abre o Dashboard Analitico
        from ui.windows.dashboard_window import DashboardWindow
        if not hasattr(self, 'dashboard_window') or self.dashboard_window is None or not self.dashboard_window.winfo_exists():
            self.dashboard_window = DashboardWindow(self)
        else:
            self.dashboard_window.focus()
            
    def _menu_help(self):
        from ui.windows.ajuda_window import AjudaWindow
        if not hasattr(self, 'ajuda_window') or self.ajuda_window is None or not self.ajuda_window.winfo_exists():
            self.ajuda_window = AjudaWindow(self)
        else:
            self.ajuda_window.focus()
            
    def show_toast(self, message):
        if not getattr(self, 'notifications_enabled', True): return
        toast = ctk.CTkToplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(fg_color="#1E1E1E")
        
        lbl = ctk.CTkLabel(toast, text=f"🔔 {message}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#10B981")
        lbl.pack(padx=20, pady=10)
        
        self.update_idletasks()
        w = toast.winfo_width()
        h = toast.winfo_height()
        x = self.winfo_rootx() + self.winfo_width() - w - 20
        y = self.winfo_rooty() + self.winfo_height() - h - 20
        toast.geometry(f"+{x}+{y}")
        
        self.after(3000, toast.destroy)
    # =========================================================================
    # SESSÃO E MEMÓRIA
    # =========================================================================
    def save_session(self, folder):
        data_dir = Path(__file__).parent.parent / 'data'
        data_dir.mkdir(exist_ok=True)
        session_file = data_dir / 'session.json'
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                import json
                json.dump({'last_project_path': folder}, f)
        except Exception as e:
            self.log(f"Erro ao salvar sessão: {e}")

    def load_session(self):
        session_file = Path(__file__).parent.parent / 'data' / 'session.json'
        if session_file.exists():
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    last_path = data.get('last_project_path')
                    if last_path and os.path.exists(last_path):
                        # Use after para dar tempo da splash
                        self.after(2000, lambda: self.explorer_panel._load_directory_from_path(last_path))
            except Exception as e:
                self.log(f"Erro ao ler sessão: {e}")

    # =========================================================================
    # LÓGICA DE PROCESSAMENTO (MVC Controller)
    # =========================================================================
    def on_file_selected(self, filepath, item=None):
        if self.processing: return
        
        basename = os.path.basename(filepath)
        if basename.endswith("_audio.wav"):
            video_name = basename.replace("_audio.wav", ".mp4")
            if video_name in self.loaded_trials or (Path(__file__).parent.parent / "data" / "cache" / f"{video_name}.pkl").exists():
                basename = video_name
        self.current_trial_name = basename
        
        # Persistência na RAM (Já processado nesta sessão)
        if self.current_trial_name in self.loaded_trials:
            self.log(f"Recuperando {self.current_trial_name} da RAM.")
            self._load_from_cache(self.current_trial_name)
            self.workspace_panel.show_player(filepath)
            if item:
                self.explorer_panel.active_tree_item = item
                self.explorer_panel.finish_loading_animation(True)
            return
            
        # Fast-Load do HD (.pkl)
        cache_dir = Path(__file__).parent.parent / "data" / "cache"
        cache_path = cache_dir / f"{self.current_trial_name}.pkl"
        
        self.workspace_panel.show_player(filepath)
        
        if cache_path.exists():
            self.log(f"Fast-Load (HD): Recuperando {self.current_trial_name}...")
            try:
                temp_data = joblib.load(cache_path)
                self.loaded_trials[self.current_trial_name] = temp_data
                
                # Auto-healer: gera o json silenciosamente para versoes legadas (se nao existir)
                meta_file = cache_dir / f"{self.current_trial_name}_meta.json"
                if not meta_file.exists():
                    import json
                    f_df = temp_data.get('features')
                    meta_dict = {
                        'pred': temp_data.get('pred', 'N/A'),
                        'features': f_df.iloc[0].to_dict() if f_df is not None and not f_df.empty else {}
                    }
                    try:
                        with open(meta_file, 'w', encoding='utf-8') as f:
                            json.dump(meta_dict, f)
                        self.dataset_history[self.current_trial_name] = {'pred': meta_dict['pred'], 'features': f_df}
                        if hasattr(self, 'explorer_panel') and self.explorer_panel:
                            self.after(0, self.explorer_panel.refresh_cache_icons)
                    except: pass

                self._load_from_cache(self.current_trial_name)
                if item:
                    self.explorer_panel.active_tree_item = item
                    self.explorer_panel.finish_loading_animation(True)
                return
            except Exception as e:
                self.log(f"Cache Corrompido ou Erro: {e}")
            
        self.ai_panel.set_ml_result("Processando...", "gray")
        self.explorer_panel.prog_bar.set(0.1)
        self.explorer_panel.lbl_prog.configure(text="Iniciando Leitura...")
        self.processing = True
        self.explorer_panel.start_loading_animation(item)
        
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
        self.show_toast("Gráficos Visualizáveis Disponíveis!")

    def _process_single_file(self, path):
        name = os.path.basename(path)
        self.after(0, lambda: self.log(f"Extraindo features de: {name}"))
        try:
            ext = Path(path).suffix.lower()
            if ext == '.mp4':
                audio_filename = Path(path).stem + "_audio.wav"
                audio_path = os.path.join(os.path.dirname(path), audio_filename)
                if not os.path.exists(audio_path):
                    video = VideoFileClip(path)
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
            t = np.arange(len(audio_data)) / fs
            
            self.after(0, lambda: self._update_prog(0.5, "Processamento DSP Paralelo (PSD & Wavelet)..."))
            
            def process_psd():
                f, Pxx = DSPProcessor.calcular_psd_welch(audio_data, fs, config.DSP_CONFIG['WELCH_NPERSEG'])
                energia_media = np.sqrt(np.mean(audio_data**2))
                variancia_sinal = np.var(audio_data)
                taxa_cruzamento_zero = np.sum(np.diff(np.sign(audio_data)) != 0)
                indice_pico = np.argmax(Pxx)
                frequencia_pico_hz = f[indice_pico]
                energia_espectral_total = np.trapezoid(y=Pxx, x=f)
                features = pd.DataFrame([{
                    'energia_media': energia_media,
                    'variancia_sinal': variancia_sinal,
                    'taxa_cruzamento_zero': taxa_cruzamento_zero,
                    'frequencia_pico_hz': frequencia_pico_hz,
                    'energia_espectral_total': energia_espectral_total
                }])
                return f, Pxx, features
                
            def process_wavelet():
                freqs = np.linspace(config.DSP_CONFIG['FREQ_MIN'], config.DSP_CONFIG['FREQ_MAX'], config.DSP_CONFIG['NUM_SCALES'])
                coefs, t_cwt = DSPProcessor.cwt_morlet_otimizada(audio_data, fs, freqs)
                return freqs, coefs, t_cwt

            # Executando PSD (e Features) + Wavelet em paralelo
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_psd = executor.submit(process_psd)
                future_wavelet = executor.submit(process_wavelet)
                
                f, Pxx, features_df = future_psd.result()
                freqs, coefs, t_cwt = future_wavelet.result()
            
            self.after(0, lambda: self._update_prog(0.9, "Analisando com Machine Learning..."))
            
            # Predict
            predicao = "Desconhecido"
            if self.rf_model:
                predicao = self.rf_model.predict(features_df)[0]
            
            # Save to Cache (RAM e HD)
            self.loaded_trials[name] = {
                'time': {'t': t, 'signal': audio_data},
                'psd': {'f': f, 'Pxx': Pxx, 'fs': fs},
                'wavelet': {'coefs': coefs, 't': t_cwt, 'freqs': freqs},
                'features': features_df,
                'pred': predicao
            }
            
            try:
                cache_dir = Path(__file__).parent.parent / "data" / "cache"
                cache_dir.mkdir(parents=True, exist_ok=True)
                joblib.dump(self.loaded_trials[name], cache_dir / f"{name}.pkl")
                
                # Salva metadados leves pro history como JSON para leitura rapida no boot
                import json
                meta_dict = {
                    'pred': predicao,
                    'features': features_df.iloc[0].to_dict() if features_df is not None and not features_df.empty else {}
                }
                with open(cache_dir / f"{name}_meta.json", 'w', encoding='utf-8') as f:
                    json.dump(meta_dict, f)
                
                self.dataset_history[name] = {
                    'pred': predicao,
                    'features': features_df
                }
            except Exception as e:
                self.after(0, lambda e=e: self.log(f"Erro ao salvar Fast-Load no HD: {e}"))
            
            self.after(0, lambda: self._update_prog(1.0, "Pronto!"))
            self.after(0, lambda: self._update_ui_after_process(name, features_df, predicao))
        except Exception as e:
            def on_error():
                self.log(f"ERRO: {e}", "ERROR")
                self.ai_panel.set_ml_result("Erro DSP", "red")
                self._update_prog(0, "Falhou.")
                self.processing = False
                self.explorer_panel.finish_loading_animation(False)
                show_error(self, "Erro de Processamento", f"Ocorreu um erro ao processar os dados do arquivo.\n\nDetalhes: {e}")
            self.after(0, on_error)

    def _update_prog(self, val, text):
        self.explorer_panel.prog_bar.set(val)
        self.explorer_panel.lbl_prog.configure(text=f"Processamento: {int(val*100)}% - {text}")

    def _update_ui_after_process(self, name, features_df, predicao):
        self.current_features_cache = features_df
        cor = "#10B981" if predicao == "Spray" else "#3B82F6" if predicao == "Globular" else "#EF4444"
        self.ai_panel.set_ml_result(predicao, cor)
        self.workspace_panel.append_dataset_row(name, predicao, features_df)
        self.workspace_panel.update_plots(self.loaded_trials[name], name)
        
        # Voz: Fala a predição identificada
        from utils.voice_engine import speak
        speak(f"Análise do ensaio concluída. O algoritmo identificou o modo de transferência como: {predicao}.")
        
        self.processing = False
        self.explorer_panel.finish_loading_animation(True)
        self.show_toast("Gráficos Visualizáveis Disponíveis!")
