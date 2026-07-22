import customtkinter as ctk
from tkinter import ttk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter
import utils.config as config

class WorkspacePanel(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_time = self.tabview.add("Sinal no Tempo")
        self.tab_fft = self.tabview.add("PSD Welch")
        self.tab_wavelet = self.tabview.add("Wavelet Morlet")
        self.tab_dataset = self.tabview.add("Dataset & ML")
        
        self._setup_plot_tabs()
        self._setup_dataset_tab()

    def _setup_plot_tabs(self):
        def create_plot_area(parent_tab):
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

        self.fig_time, self.canvas_time = create_plot_area(self.tab_time)
        self.ax_time = self.fig_time.add_subplot(111)
        self.fig_fft, self.canvas_fft = create_plot_area(self.tab_fft)
        self.ax_fft = self.fig_fft.add_subplot(111)
        self.fig_wavelet, self.canvas_wavelet = create_plot_area(self.tab_wavelet)
        self.ax_wavelet = self.fig_wavelet.add_subplot(111)

    def _setup_dataset_tab(self):
        self.tab_dataset.grid_rowconfigure(1, weight=1)
        self.tab_dataset.grid_columnconfigure(0, weight=1)
        
        lbl_data = ctk.CTkLabel(self.tab_dataset, text="Histórico de Análises da Sessão", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_data.grid(row=0, column=0, pady=10, sticky="w", padx=10)
        
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#444444", foreground="black")
        
        tree_frame = ctk.CTkFrame(self.tab_dataset, fg_color="transparent")
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.tree_data = ttk.Treeview(tree_frame, selectmode="browse")
        self.tree_data.grid(row=0, column=0, sticky="nsew")
        self.tree_data.bind("<<TreeviewSelect>>", self._on_dataset_row_select)
        
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

    def _on_dataset_row_select(self, event):
        selection = self.tree_data.selection()
        if not selection: return
        item = selection[0]
        filename = self.tree_data.item(item, "values")[0]
        # Quando clica na linha, ele tenta carregar o gráfico do cache
        self.controller.on_file_selected_from_cache(filename)

    def append_dataset_row(self, filename, pred, f_df):
        # Verifica se já não inseriu (caso o usuario reclique no arquivo)
        for item in self.tree_data.get_children():
            if self.tree_data.item(item, "values")[0] == filename:
                return # Já existe
                
        row = [filename, pred]
        row.extend([round(f_df[col].iloc[0], 2) for col in f_df.columns])
        self.tree_data.insert("", "end", values=row)
        self.tree_data.yview_moveto(1)

    def update_plots(self, results, title_suffix):
        try:
            self.ax_time.clear()
            self.ax_time.plot(results['time']['t'], results['time']['signal'], color=config.GUI_CONFIG['COLOR_TIME_SIGNAL'], linewidth=0.5)
            self._dark_style(self.ax_time, f'Sinal Acústico no Tempo - {title_suffix}')
            self.fig_time.tight_layout()
            self.canvas_time.draw()
            
            self.ax_fft.clear()
            Pxx_db = 10 * np.log10(results['psd']['Pxx'] + 1e-12)
            self.ax_fft.fill_between(results['psd']['f'], Pxx_db, -200, color=config.GUI_CONFIG['COLOR_PSD'], alpha=0.2)
            self.ax_fft.plot(results['psd']['f'], Pxx_db, color=config.GUI_CONFIG['COLOR_PSD'], linewidth=1)
            self.ax_fft.set_xlim([0, results['psd']['fs']/2])
            self.ax_fft.set_ylim([np.max(Pxx_db)-80, np.max(Pxx_db)+5])
            self._dark_style(self.ax_fft, 'Densidade Espectral de Potência (Welch)')
            self.fig_fft.tight_layout()
            self.canvas_fft.draw()
            
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
            self.controller.log(f"Erro ao plotar gráficos: {e}")

    def _dark_style(self, ax, title):
        ax.set_facecolor('#1e1e1e')
        ax.tick_params(colors='white', labelsize=8)
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.title.set_color('white')
        for spine in ax.spines.values(): spine.set_edgecolor('#555555')
        ax.grid(True, alpha=0.1, color='white', linestyle='--')
        ax.set_title(title)
