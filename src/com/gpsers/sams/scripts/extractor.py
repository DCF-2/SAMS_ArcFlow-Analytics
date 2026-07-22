"""
SAMS - Extrator de Features
Módulo Visual de Treinamento da IA (GUI) usando CustomTkinter.
Gera o dataset inicial (CSV) para treinamento de Machine Learning.
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
import numpy as np
import pandas as pd
# pyrefly: ignore [missing-import]
from scipy.io import wavfile

# Garante que o módulo consegue importar arquivos da pasta pai (sams)
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
diretorio_pai = os.path.dirname(diretorio_atual)
sys.path.append(diretorio_pai)

# Importamos o módulo DSP
from core.dsp_processor import DSPProcessor 

class ExtractorGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuração da janela principal
        self.title("SAMS - Módulo de Treinamento (Extrator de Features)")
        self.geometry("600x500")
        ctk.set_appearance_mode("dark")  # Visual moderno estilo SAMS
        ctk.set_default_color_theme("blue")
        
        # Variáveis de estado
        self.diretorio_audio = ""
        self.modo_selecionado = ctk.StringVar(value="Curto-Circuito")
        
        # =======================================================
        # CABEÇALHO
        # =======================================================
        self.label_titulo = ctk.CTkLabel(
            self, text="Extrator de Features de Soldagem", 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.label_titulo.pack(pady=(25, 5))
        
        self.label_desc = ctk.CTkLabel(
            self, 
            text="Este módulo varre pastas de áudios (.wav), extrai dados matemáticos\ne constrói a base de dados para o modelo de Machine Learning.",
            text_color="gray", justify="center"
        )
        self.label_desc.pack(pady=(0, 20))
        
        # =======================================================
        # FRAME 1: SELEÇÃO DE PASTA
        # =======================================================
        self.frame_pasta = ctk.CTkFrame(self)
        self.frame_pasta.pack(pady=10, padx=30, fill="x")
        
        self.btn_selecionar = ctk.CTkButton(
            self.frame_pasta, text="📁 Selecionar Pasta de Áudios", 
            command=self.selecionar_pasta, width=200
        )
        self.btn_selecionar.pack(side="left", padx=15, pady=15)
        
        self.label_pasta = ctk.CTkLabel(
            self.frame_pasta, text="Nenhuma pasta selecionada", 
            text_color="gray", font=ctk.CTkFont(size=12)
        )
        self.label_pasta.pack(side="left", padx=10, pady=15)
        
        # =======================================================
        # FRAME 2: SELEÇÃO DA CLASSE (MODO)
        # =======================================================
        self.frame_modo = ctk.CTkFrame(self)
        self.frame_modo.pack(pady=10, padx=30, fill="x")
        
        self.label_modo = ctk.CTkLabel(
            self.frame_modo, text="Modo de Transferência da pasta escolhida:", 
            font=ctk.CTkFont(weight="bold")
        )
        self.label_modo.pack(pady=(15, 10))
        
        # Grid para alinhar os RadioButtons horizontalmente
        self.frame_radios = ctk.CTkFrame(self.frame_modo, fg_color="transparent")
        self.frame_radios.pack(pady=(0, 15))
        
        self.radio_cc = ctk.CTkRadioButton(
            self.frame_radios, text="Curto-Circuito", 
            variable=self.modo_selecionado, value="Curto-Circuito"
        )
        self.radio_cc.grid(row=0, column=0, padx=15)
        
        self.radio_gl = ctk.CTkRadioButton(
            self.frame_radios, text="Globular", 
            variable=self.modo_selecionado, value="Globular"
        )
        self.radio_gl.grid(row=0, column=1, padx=15)
        
        self.radio_sp = ctk.CTkRadioButton(
            self.frame_radios, text="Spray / Aerossol", 
            variable=self.modo_selecionado, value="Spray"
        )
        self.radio_sp.grid(row=0, column=2, padx=15)
        
        # =======================================================
        # AÇÃO PRINCIPAL E STATUS
        # =======================================================
        self.btn_extrair = ctk.CTkButton(
            self, text="⚡ Iniciar Extração e Salvar no Dataset", 
            command=self.iniciar_extracao, 
            fg_color="#0D9488", hover_color="#0F766E", height=45,
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.btn_extrair.pack(pady=(25, 10))
        
        self.label_status = ctk.CTkLabel(
            self, text="Aguardando seleção...", text_color="gray",
            font=ctk.CTkFont(size=13)
        )
        self.label_status.pack(pady=5)

    def selecionar_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta raiz dos áudios")
        if pasta:
            self.diretorio_audio = pasta
            # Trunca o texto se for muito longo
            texto_exibicao = f"...{pasta[-35:]}" if len(pasta) > 35 else pasta
            self.label_pasta.configure(text=texto_exibicao, text_color="white")
            self.label_status.configure(text="Pasta carregada. Selecione o Modo e clique em Iniciar.", text_color="white")
            
    def iniciar_extracao(self):
        if not self.diretorio_audio:
            self.label_status.configure(text="Erro: Selecione uma pasta primeiro!", text_color="#E63946")
            return
            
        modo = self.modo_selecionado.get()
        self.btn_extrair.configure(state="disabled", text="Processando...")
        self.label_status.configure(text=f"Processando áudios da pasta como '{modo}'...", text_color="#F59E0B")
        self.update() # Força a atualização visual da interface
        
        # Executa a função lógica fora da classe UI
        sucesso, msg = extrair_features_lote(self.diretorio_audio, modo)
        
        if sucesso:
            self.label_status.configure(text=msg, text_color="#10B981") # Verde
        else:
            self.label_status.configure(text=msg, text_color="#E63946") # Vermelho
            
        self.btn_extrair.configure(state="normal", text="⚡ Iniciar Extração e Salvar no Dataset")


def extrair_features_lote(diretorio_audio, modo_escolhido):
    """
    Realiza a varredura e extração DSP sem congelar o sistema.
    Retorna (Booleano_Sucesso, String_Mensagem).
    """
    try:
        linhas_dataset = []
        caminhos_arquivos = []
        
        # Varredura
        for root_dir, dirs, files in os.walk(diretorio_audio):
            for f in files:
                if f.lower().endswith('.wav'):
                    caminhos_arquivos.append(os.path.join(root_dir, f))
                    
        caminhos_arquivos.sort()
        
        if not caminhos_arquivos:
            return False, "Erro: Nenhum arquivo .wav encontrado nesta pasta!"
        
        # Gerenciamento do ID para o arquivo CSV
        pasta_data = os.path.join(diretorio_pai, "data")
        os.makedirs(pasta_data, exist_ok=True)
        nome_csv = os.path.join(pasta_data, 'dataset_features.csv')
        
        id_ensaio = 1
        arquivo_existe = os.path.isfile(nome_csv)
        if arquivo_existe:
            try:
                df_existente = pd.read_csv(nome_csv)
                if not df_existente.empty and 'id_ensaio' in df_existente.columns:
                    id_ensaio = df_existente['id_ensaio'].max() + 1
            except Exception:
                pass
                
        # Processamento
        for caminho_completo in caminhos_arquivos:
            nome_arquivo = os.path.basename(caminho_completo)
            fs, sinal = wavfile.read(caminho_completo)
            sinal = sinal.astype(np.float64)
            if sinal.ndim > 1: sinal = sinal[:, 0]
            
            energia_media = np.sqrt(np.mean(sinal**2))
            variancia_sinal = np.var(sinal)
            taxa_cruzamento_zero = np.sum(np.diff(np.sign(sinal)) != 0)
            
            f, Pxx = DSPProcessor.calcular_psd_welch(sinal, fs)
            indice_pico = np.argmax(Pxx)
            frequencia_pico_hz = f[indice_pico]
            energia_espectral_total = np.trapezoid(y=Pxx, x=f)
            
            linhas_dataset.append({
                'id_ensaio': id_ensaio,
                'nome_arquivo': nome_arquivo,
                'energia_media': energia_media,
                'variancia_sinal': variancia_sinal,
                'taxa_cruzamento_zero': taxa_cruzamento_zero,
                'frequencia_pico_hz': frequencia_pico_hz,
                'energia_espectral_total': energia_espectral_total,
                'modo_transferencia': modo_escolhido
            })
            id_ensaio += 1
            
        # Exportação
        df = pd.DataFrame(linhas_dataset)
        df.to_csv(nome_csv, mode='a', header=not arquivo_existe, index=False)
        return True, f"✔ Sucesso! {len(df)} ensaios extraídos para dataset_features.csv"
        
    except Exception as e:
        return False, f"Erro inesperado: {str(e)}"

if __name__ == "__main__":
    app = ExtractorGUI()
    app.mainloop()
