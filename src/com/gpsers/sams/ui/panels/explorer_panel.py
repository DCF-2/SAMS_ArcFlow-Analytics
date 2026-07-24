import customtkinter as ctk
from tkinter import filedialog, ttk
import os
from pathlib import Path
from PIL import Image
from ui.components.tooltip import ToolTip

class ExplorerPanel(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=0, width=300)
        self.controller = controller
        
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Titulo: Removemos os colchetes
        self.lbl_logo = ctk.CTkLabel(self, text="SAMS Explorer", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_logo.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Carregando Ícones
        icons_dir = Path(__file__).parent.parent.parent / 'assets' / 'icons'
        icon_pasta = None
        icon_config = None
        try:
            icon_pasta = ctk.CTkImage(Image.open(icons_dir / "pasta.png"), size=(20, 20))
            icon_config = ctk.CTkImage(Image.open(icons_dir / "configuracoes-cog.png"), size=(20, 20))
        except: pass
        
        # Botoes do Topo
        self.btn_open_folder = ctk.CTkButton(
            self, text=" Abrir Pasta de Projeto", image=icon_pasta, command=self.load_directory,
            fg_color="#2c3e50", hover_color="#34495e"
        )
        self.btn_open_folder.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        # O botão config vai para a parte de baixo (row=5)
        self.btn_config = ctk.CTkButton(self, text=" Configurações", image=icon_config, command=self.controller.open_settings, fg_color="#333333", hover_color="#444444")
        self.btn_config.grid(row=5, column=0, padx=20, pady=(10, 20), sticky="ew")
        
        ToolTip(self.btn_open_folder, "Abre a pasta contendo os áudios ou vídeos dos ensaios (.wav, .mp4)")
        ToolTip(self.btn_config, "Abre o painel de Configurações, Modelos IA e Ajuda")
        
        # Barra de Progresso e Animação
        self.frame_prog = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_prog.grid(row=4, column=0, padx=20, pady=15, sticky="ew")
        self.frame_prog.grid_columnconfigure(1, weight=1)
        
        self.lbl_loading_icon = ctk.CTkLabel(self.frame_prog, text="")
        self.lbl_loading_icon.grid(row=0, column=0, padx=(0, 5), sticky="w")
        
        self.lbl_prog = ctk.CTkLabel(self.frame_prog, text="Pronto.", font=ctk.CTkFont(size=11))
        self.lbl_prog.grid(row=0, column=1, sticky="w")
        
        self.prog_bar = ctk.CTkProgressBar(self.frame_prog)
        self.prog_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 0))
        self.prog_bar.set(0)
        
        self.loading_frames = []
        self.tree_loading_frames = []
        self.tree_success_icon = None
        self.loading_idx = 0
        self.active_tree_item = None
        
        try:
            from PIL import ImageTk
            pil_sprite = Image.open(icons_dir / "carregando.png").convert("RGBA")
            self.loading_frames = []
            self.tree_loading_frames = []
            
            # Simulando rotação do sprite de engrenagem
            for i in range(0, 360, 45):
                rotated = pil_sprite.rotate(-i, resample=Image.BICUBIC)
                
                # Para label lateral
                img1 = ctk.CTkImage(light_image=rotated, dark_image=rotated, size=(16, 16))
                self.loading_frames.append(img1)
                
                # Para TreeView (PhotoImage puro do Tkinter nao lida bem com alpha, mas ImageTk sim)
                rotated_tree = rotated.resize((16, 16), Image.LANCZOS)
                self.tree_loading_frames.append(ImageTk.PhotoImage(rotated_tree))
                
            success_img = Image.open(icons_dir / "verificado.png").resize((16, 16))
            self.tree_success_icon = ImageTk.PhotoImage(success_img)
            
        except Exception as e:
            print(f"[ERRO] Falha ao carregar ícone giratório: {e}")
            self.loading_frames = []
        
        # Treeview de Arquivos
        style = ttk.Style()
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0, font=("Segoe UI", 10))
        style.map("Treeview", background=[("selected", "#0078D7")])
        
        tree_frame = ctk.CTkFrame(self, fg_color="transparent")
        tree_frame.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(tree_frame, show="tree")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

    def start_loading_animation(self, item_id=None):
        if item_id:
            self.active_tree_item = item_id
            
        if self.loading_frames:
            self.loading_idx = (self.loading_idx + 1) % len(self.loading_frames)
            self.lbl_loading_icon.configure(image=self.loading_frames[self.loading_idx])
            
            if self.active_tree_item and self.tree_loading_frames:
                try:
                    self.tree.item(self.active_tree_item, image=self.tree_loading_frames[self.loading_idx])
                except: pass
            
        if getattr(self.controller, 'processing', False):
            self.after(50, self.start_loading_animation)
        else:
            self.lbl_loading_icon.configure(image=None)

    def finish_loading_animation(self, success=True):
        if self.active_tree_item:
            try:
                if success and hasattr(self, 'tree_success_icon'):
                    self.tree.item(self.active_tree_item, image=self.tree_success_icon)
                else:
                    self.tree.item(self.active_tree_item, image="")
            except: pass
        self.active_tree_item = None
        self.lbl_loading_icon.configure(image=None)
        if success:
            self.lbl_prog.configure(text="Processamento: Concluído")
        self.refresh_cache_icons()

    def load_directory(self):
        folder = filedialog.askdirectory(title="Selecione a pasta do projeto")
        if not folder: return
        self._load_directory_from_path(folder)
        
    def _load_directory_from_path(self, folder):
        if not os.path.exists(folder): return
        self.tree.delete(*self.tree.get_children())
        self.controller.log(f"Carregando pasta: {folder}")
        root_node = self.tree.insert("", "end", text=os.path.basename(folder), open=True, tags=("dir",))
        self._populate_tree(folder, root_node)
        
        # Salva a memoria da sessao
        self.controller.save_session(folder)

    def _check_cache(self, basename):
        cache_dir = Path(__file__).parent.parent / "data" / "cache"
        return (cache_dir / f"{basename}.pkl").exists()

    def _populate_tree(self, path, parent_node):
        for item in sorted(os.listdir(path)):
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                node = self.tree.insert(parent_node, "end", text=item, open=False, tags=("dir",))
                self._populate_tree(full_path, node)
            else:
                ext = Path(item).suffix.lower()
                if ext in ['.wav', '.mp4']:
                    node = self.tree.insert(parent_node, "end", text=item, values=(full_path,), tags=("file",))
                    if self._check_cache(item) and getattr(self, 'tree_success_icon', None):
                        self.tree.item(node, image=self.tree_success_icon)

    def refresh_cache_icons(self):
        if not hasattr(self, 'tree_success_icon'): return
        
        for item_id in self.tree.get_children():
            self._recursive_refresh(item_id)
            
    def _recursive_refresh(self, node):
        text = self.tree.item(node, "text").strip()
        basename = text
        if basename.endswith("_audio.wav"):
            basename = basename.replace("_audio.wav", ".mp4")
            
        if basename in self.controller.loaded_trials or basename in getattr(self.controller, 'dataset_history', {}):
            try: self.tree.item(node, image=self.tree_success_icon)
            except: pass
            
        for child in self.tree.get_children(node):
            self._recursive_refresh(child)

    def _on_tree_select(self, event):
        selection = self.tree.selection()
        if not selection: return
        item = selection[0]
        tags = self.tree.item(item, "tags")
        if "file" not in tags: return
        
        filepath = self.tree.item(item, "values")[0]
        self.controller.on_file_selected(filepath, item)
