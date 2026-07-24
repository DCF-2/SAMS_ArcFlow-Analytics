import customtkinter as ctk
from tkinter import ttk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter
from pathlib import Path
from PIL import Image
import utils.config as config
from ui.components.tooltip import ToolTip
import threading
import time

class DashboardWindow(ctk.CTkToplevel):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        
        self.title("SAMS - Dashboard de Gráficos")
        self.geometry("1000x700")
        self.minsize(800, 600)
        self.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        self.last_results = None
        self.last_suffix = None
        
        self.tabview = ctk.CTkTabview(self, command=self.on_tab_change)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_time = self.tabview.add("Sinal no Tempo")
        self.tab_fft = self.tabview.add("PSD Welch")
        self.tab_wavelet = self.tabview.add("Wavelet Morlet")
        self.tab_dataset = self.tabview.add("Dataset & ML")
        
        self._setup_plot_tabs()
        self._setup_dataset_tab()
        
        # Preenche a tabela com todos os ensaios ja em memoria
        history = getattr(main_window, 'dataset_history', {})
        for t_name, t_data in history.items():
            try:
                self.append_dataset_row(t_name, t_data['pred'], t_data['features'])
            except: pass
            
        # Adiciona também os que estão na sessão atual RAM (redundância)
        for t_name, t_data in main_window.loaded_trials.items():
            if t_name not in history:
                try:
                    self.append_dataset_row(t_name, t_data['pred'], t_data['features'])
                except: pass
            
        # Se ja tiver um ensaio carregado no MainWindow, atualiza os graficos
        if main_window.current_trial_name and main_window.current_trial_name in main_window.loaded_trials:
            trial = main_window.loaded_trials[main_window.current_trial_name]
            self.update_plots(trial, main_window.current_trial_name)
            
    def hide_window(self):
        self.withdraw()
        
    def focus(self):
        self.deiconify()
        super().focus()

    def on_tab_change(self):
        if self.last_results and self.last_suffix:
            current_tab = self.tabview.get()
            if current_tab == "Sinal no Tempo":
                self._plot_time(self.last_results, self.last_suffix)
            elif current_tab == "PSD Welch":
                self._plot_fft(self.last_results)
            elif current_tab == "Wavelet Morlet":
                self._plot_wavelet(self.last_results)

    def _setup_plot_tabs(self):
        icons_dir = Path(__file__).parent.parent.parent / 'assets' / 'icons'
        self.icon_ajuda = None
        try:
            self.icon_ajuda = ctk.CTkImage(Image.open(icons_dir / "ajuda.png"), size=(16, 16))
        except: pass
        
        def create_plot_area(parent_tab, tooltip_text):
            header = ctk.CTkFrame(parent_tab, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=(5, 0))
            btn_help = ctk.CTkButton(header, text="", image=self.icon_ajuda, width=24, height=24, corner_radius=12, fg_color="transparent", hover_color="#333333")
            btn_help.pack(side="right")
            ToolTip(btn_help, tooltip_text)

            frame = ctk.CTkFrame(parent_tab, fg_color="transparent")
            frame.pack(fill="both", expand=True)
            fig = Figure(figsize=(8, 5), dpi=100, facecolor='#1e1e1e')
            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
            toolbar = NavigationToolbar2Tk(canvas, frame, pack_toolbar=False)
            toolbar.config(background='#1e1e1e')
            toolbar._message_label.config(background='#1e1e1e', foreground='white')
            for button in toolbar.winfo_children(): button.config(background='#1e1e1e')
            toolbar.update()
            toolbar.pack(side="bottom", fill="x")
            return fig, canvas

        self.fig_time, self.canvas_time = create_plot_area(self.tab_time, "Onda de Oscilograma Bruta: Exibe a amplitude e dinâmica temporal da corrente/tensão.")
        self.ax_time = self.fig_time.add_subplot(111)
        
        self.fig_fft, self.canvas_fft = create_plot_area(self.tab_fft, "Densidade Espectral (FFT): Exibe como a energia do sinal se distribui nas frequências.")
        self.ax_fft = self.fig_fft.add_subplot(111)
        
        self.fig_wavelet, self.canvas_wavelet = create_plot_area(self.tab_wavelet, "Espectrograma Morlet: Mostra as frequências e o tempo simultaneamente via transformada Wavelet.")
        self.ax_wavelet = self.fig_wavelet.add_subplot(111)

    def _setup_dataset_tab(self):
        self.tab_dataset.grid_rowconfigure(1, weight=1)
        self.tab_dataset.grid_columnconfigure(0, weight=1)
        
        lbl_data = ctk.CTkLabel(self.tab_dataset, text="Histórico de Análises da Sessão", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_data.grid(row=0, column=0, pady=10, sticky="w", padx=10)
        
        btn_help = ctk.CTkButton(self.tab_dataset, text="", image=getattr(self, 'icon_ajuda', None), width=24, height=24, corner_radius=12, fg_color="transparent", hover_color="#333333")
        btn_help.grid(row=0, column=0, pady=10, sticky="e", padx=10)
        ToolTip(btn_help, "Tabela de Extração de Features: Guarda as medições matemáticas de cada ensaio.")
        
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#444444", foreground="black")
        
        tree_frame = ctk.CTkFrame(self.tab_dataset, fg_color="transparent")
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.tree_data = ttk.Treeview(tree_frame, selectmode="browse")
        self.tree_data.grid(row=0, column=0, sticky="nsew")
        
        scroll_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_data.yview)
        self.tree_data.configure(yscrollcommand=scroll_y.set)
        scroll_y.grid(row=0, column=1, sticky="ns")
        
        scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree_data.xview)
        self.tree_data.configure(xscrollcommand=scroll_x.set)
        scroll_x.grid(row=1, column=0, sticky="ew")
        
        cols = ['Arquivo', 'Previsao_ML', 'Energia_Media', 'Variancia', 'Cruzamento_Zero', 'Freq_Pico_Hz', 'Energia_Espectral']
        self.tree_data["columns"] = cols
        self.tree_data["show"] = "headings"
        for col in cols:
            self.tree_data.heading(col, text=col.replace("_", " "))
            self.tree_data.column(col, width=130, anchor="center")

    def append_dataset_row(self, filename, pred, f_df):
        for item in self.tree_data.get_children():
            if self.tree_data.item(item, "values")[0] == filename: return
        row = [filename, pred]
        row.extend([round(f_df[col].iloc[0], 2) for col in f_df.columns])
        self.tree_data.insert("", "end", values=row)
        self.tree_data.yview_moveto(1)

    def update_plots(self, results, title_suffix):
        self.last_results = results
        self.last_suffix = title_suffix
        try:
            self._plot_time(results, title_suffix)
            self._plot_fft(results)
            self._plot_wavelet(results)
        except Exception as e:
            self.main_window.log(f"Erro ao atualizar gráficos: {e}")

    def _plot_time(self, results, title_suffix):
        try:
            self.ax_time.clear()
            self._dark_style(self.ax_time, f'Sinal Acústico no Tempo - {title_suffix}')
            line, = self.ax_time.plot([], [], color=config.GUI_CONFIG['COLOR_TIME_SIGNAL'], linewidth=0.5)
            self.ax_time.set_xlim(results['time']['t'][0], results['time']['t'][-1])
            y_min, y_max = np.min(results['time']['signal']), np.max(results['time']['signal'])
            self.ax_time.set_ylim(y_min - 0.1, y_max + 0.1)
            self.fig_time.tight_layout()
            self.canvas_time.draw()
            
            def animate_time_signal():
                t_full = results['time']['t']
                sig_full = results['time']['signal']
                steps = 15
                chunk_size = max(1, len(t_full) // steps)
                
                def update_line(end_idx):
                    min_len = min(len(t_full), len(sig_full))
                    safe_end = min(end_idx, min_len)
                    line.set_data(t_full[:safe_end], sig_full[:safe_end])
                    try: self.canvas_time.draw_idle()
                    except: pass

                for i in range(1, steps + 1):
                    end_idx = i * chunk_size
                    if end_idx > len(t_full) or i == steps:
                        end_idx = len(t_full)
                    
                    self.after(0, update_line, end_idx)
                    time.sleep(0.02)
            threading.Thread(target=animate_time_signal, daemon=True).start()
        except: pass

    def _plot_fft(self, results):
        try:
            self.ax_fft.clear()
            Pxx_db = 10 * np.log10(results['psd']['Pxx'] + 1e-12)
            
            self._dark_style(self.ax_fft, 'Densidade Espectral de Potência (Welch)')
            self.ax_fft.set_xlim([0, results['psd']['fs']/2])
            self.ax_fft.set_ylim([np.max(Pxx_db)-80, np.max(Pxx_db)+5])
            
            line, = self.ax_fft.plot([], [], color=config.GUI_CONFIG['COLOR_PSD'], linewidth=1)
            self.fig_fft.tight_layout()
            self.canvas_fft.draw()
            
            def animate_fft():
                f_full = results['psd']['f']
                Pxx_db = 10 * np.log10(results['psd']['Pxx'] + 1e-12)
                steps = 10
                chunk_size = max(1, len(f_full) // steps)
                
                def update_fft(end_idx):
                    line.set_data(f_full[:end_idx], Pxx_db[:end_idx])
                    try: self.canvas_fft.draw_idle()
                    except: pass
                
                for i in range(1, steps + 1):
                    end_idx = i * chunk_size
                    if i == steps: end_idx = len(f_full)
                    
                    self.after(0, update_fft, end_idx)
                    time.sleep(0.02)
                
                def finalize_fft():
                    try: 
                        self.ax_fft.fill_between(f_full, Pxx_db, -200, color=config.GUI_CONFIG['COLOR_PSD'], alpha=0.2)
                        self.canvas_fft.draw_idle()
                    except: pass
                self.after(0, finalize_fft)
                
            threading.Thread(target=animate_fft, daemon=True).start()
        except: pass

    def _plot_wavelet(self, results):
        try:
            self.fig_wavelet.clear()
            self.ax_wavelet = self.fig_wavelet.add_subplot(111)
            magnitude = np.abs(results['wavelet']['coefs'])
            max_val = np.max(magnitude) if np.max(magnitude) > 0 else 1e-12
            magnitude_db = 20 * np.log10((magnitude / max_val) + 1e-12)
            extent = [results['wavelet']['freqs'][0], results['wavelet']['freqs'][-1], results['wavelet']['t'][0], results['wavelet']['t'][-1]]
            im = self.ax_wavelet.imshow(magnitude_db.T, aspect='auto', origin='lower', cmap=config.GUI_CONFIG['COLORMAP_WAVELET'], extent=extent, vmin=-50, vmax=0)
            self._dark_style(self.ax_wavelet, 'Espectrograma Wavelet (CWT Morlet)')
            self.ax_wavelet.xaxis.set_major_formatter(ScalarFormatter())
            cbar = self.fig_wavelet.colorbar(im, ax=self.ax_wavelet)
            cbar.set_label('dB', color='white', rotation=0, labelpad=-10, y=1.05)
            cbar.ax.yaxis.set_tick_params(color='white')
            import matplotlib.pyplot as plt
            plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
            
            self.fig_wavelet.tight_layout()
            self.canvas_wavelet.draw()
        except Exception as e:
            self.main_window.log(f"Erro no Wavelet: {e}")

    def _dark_style(self, ax, title):
        ax.set_facecolor('#1e1e1e')
        ax.tick_params(colors='white', labelsize=8)
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.title.set_color('white')
        for spine in ax.spines.values(): spine.set_edgecolor('#555555')
        ax.grid(True, alpha=0.1, color='white', linestyle='--')
        ax.set_title(title)
