import customtkinter as ctk
from tkinter import filedialog, ttk
import os
from pathlib import Path

class ExplorerPanel(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=0, width=300)
        self.controller = controller
        
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Titulo: Removemos os colchetes
        self.lbl_logo = ctk.CTkLabel(self, text="SAMS Explorer", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_logo.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Botoes do Topo
        self.btn_open_folder = ctk.CTkButton(
            self, text="Abrir Pasta de Projeto", command=self.load_directory,
            fg_color="#2c3e50", hover_color="#34495e"
        )
        self.btn_open_folder.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        # O botão config vai para a parte de baixo (row=5)
        self.btn_config = ctk.CTkButton(self, text="⚙️ Configurações", command=self.controller.open_settings, fg_color="#333333", hover_color="#444444")
        self.btn_config.grid(row=5, column=0, padx=20, pady=(10, 20), sticky="ew")
        
        # Barra de Progresso
        self.frame_prog = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_prog.grid(row=4, column=0, padx=20, pady=15, sticky="ew")
        self.frame_prog.grid_columnconfigure(0, weight=1)
        
        self.lbl_prog = ctk.CTkLabel(self.frame_prog, text="Pronto.", font=ctk.CTkFont(size=11))
        self.lbl_prog.grid(row=0, column=0, sticky="w")
        
        self.prog_bar = ctk.CTkProgressBar(self.frame_prog)
        self.prog_bar.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        self.prog_bar.set(0)
        
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

    def load_directory(self):
        folder = filedialog.askdirectory(title="Selecione a pasta do projeto")
        if not folder: return
        self.tree.delete(*self.tree.get_children())
        self.controller.log(f"Carregando pasta: {folder}")
        root_node = self.tree.insert("", "end", text=os.path.basename(folder), open=True, tags=("dir",))
        self._populate_tree(folder, root_node)

    def _populate_tree(self, path, parent_node):
        for item in sorted(os.listdir(path)):
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                node = self.tree.insert(parent_node, "end", text=item, open=False, tags=("dir",))
                self._populate_tree(full_path, node)
            else:
                ext = Path(item).suffix.lower()
                if ext in ['.wav', '.mp4']:
                    self.tree.insert(parent_node, "end", text=item, values=(full_path,), tags=("file",))

    def _on_tree_select(self, event):
        selection = self.tree.selection()
        if not selection: return
        item = selection[0]
        tags = self.tree.item(item, "tags")
        if "file" not in tags: return
        
        filepath = self.tree.item(item, "values")[0]
        self.controller.on_file_selected(filepath)
