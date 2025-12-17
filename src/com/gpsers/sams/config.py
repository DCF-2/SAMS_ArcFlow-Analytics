"""
config.py
=========
Arquivo de Configuração Centralizado
Ajuste parâmetros aqui sem modificar o código principal
"""

# ============================================================================
# CONFIGURAÇÕES DE DSP (Processamento Digital de Sinais)
# ============================================================================
DSP_CONFIG = {
    # Wavelet CWT
    'MAX_PIXELS': 3000,              # Resolução temporal máxima (3000 = boa qualidade)
                                     # Raspberry Pi: use 1500-2000
    
    'FREQ_MIN': 50,                  # Frequência mínima da Wavelet (Hz)
    'FREQ_MAX': 5000,                # Frequência máxima da Wavelet (Hz)
    'NUM_SCALES': 100,               # Número de escalas de frequência
    
    # PSD Welch
    'WELCH_NPERSEG': 1024,           # Tamanho da janela FFT
                                     # 512 = rápido, 2048 = alta resolução
    
    'WELCH_OVERLAP_RATIO': 0.5,     # Sobreposição (0.5 = 50%)
    
    # Geral
    'NORMALIZATION': True,           # Normalizar áudio para [-1, 1]
    'STEREO_TO_MONO': True,          # Converter estéreo para mono
}


# ============================================================================
# CONFIGURAÇÕES DA INTERFACE GRÁFICA
# ============================================================================
GUI_CONFIG = {
    # Janela Principal
    'WINDOW_WIDTH': 1400,            # Largura da janela (pixels)
    'WINDOW_HEIGHT': 900,            # Altura da janela (pixels)
    'THEME': 'dark',                 # 'dark', 'light', ou 'system'
    'COLOR_THEME': 'blue',           # 'blue', 'green', 'dark-blue'
    
    # Plots
    'PLOT_DPI': 100,                 # DPI dos gráficos (100 = padrão)
    'PLOT_FACECOLOR': '#2b2b2b',     # Cor de fundo dos plots
    'PLOT_LINEWIDTH': 1.5,           # Espessura das linhas
    
    # Cores dos Sinais
    'COLOR_TIME_SIGNAL': '#00d9ff',  # Cor do sinal temporal (ciano)
    'COLOR_PSD': '#00ff88',          # Cor da PSD (verde água)
    'COLORMAP_WAVELET': 'jet',       # Colormap da Wavelet ('jet', 'viridis', 'plasma')
    
    # Performance
    'ENABLE_THREADING': True,        # Usar threads para processamento
    'SHOW_PROGRESS': True,           # Mostrar barra de progresso
}


# ============================================================================
# CONFIGURAÇÕES DE ARQUIVOS
# ============================================================================
FILE_CONFIG = {
    # Áudio
    'AUDIO_FORMAT': 'wav',           # Formato de saída do áudio
    'AUDIO_SUFFIX': '_audio',        # Sufixo adicionado ao nome do arquivo
    
    # Vídeo
    'ALLOWED_VIDEO_FORMATS': ['.mp4', '.avi', '.mov', '.mkv'],
    
    # Exportação (futuro)
    'EXPORT_FORMAT': 'png',          # Formato de exportação de gráficos
    'EXPORT_DPI': 300,               # DPI para exportação
}


# ============================================================================
# CONFIGURAÇÕES DE DEBUG
# ============================================================================
DEBUG_CONFIG = {
    'VERBOSE': True,                 # Logs detalhados no terminal
    'SAVE_INTERMEDIATE': False,      # Salvar resultados intermediários
    'TIMING': True,                  # Mostrar tempo de execução
}