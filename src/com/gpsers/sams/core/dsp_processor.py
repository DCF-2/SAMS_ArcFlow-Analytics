"""
dsp_processor.py
================
Módulo de Processamento Digital de Sinais (DSP)
Contém algoritmos matemáticos para análise espectral

Autor: Sistema de Monitoramento de Soldagem
Versão: 2.0
"""

import numpy as np
from scipy.signal import welch


class DSPProcessor:
    """
    Classe responsável pelo processamento de sinais (DSP)
    Implementa algoritmos otimizados para hardware embarcado
    """
    
    @staticmethod
    def cwt_morlet_otimizada(sinal, fs, freqs):
        """
        Implementação da Transformada Wavelet Contínua com Morlet
        Portado EXATAMENTE do código Octave cwt_morlet_otimizada.m
        
        Otimizações:
        - Decimação adaptativa (MAX_PIXELS = 3000)
        - Vetorização com NumPy
        - Normalização energética da wavelet
        
        Args:
            sinal (np.ndarray): Array 1D com o sinal de áudio
            fs (int): Taxa de amostragem em Hz
            freqs (np.ndarray): Array com frequências de interesse em Hz
            
        Returns:
            tuple: (coefs, t_out)
                - coefs (np.ndarray): Matriz complexa (len(freqs) x len(indices))
                - t_out (np.ndarray): Vetor de tempo reduzido em segundos
                
        Exemplo:
            >>> sinal = np.random.randn(48000)  # 1 segundo @ 48kHz
            >>> fs = 48000
            >>> freqs = np.logspace(np.log10(50), np.log10(5000), 50)
            >>> coefs, t = DSPProcessor.cwt_morlet_otimizada(sinal, fs, freqs)
            >>> print(coefs.shape)  # (50, ~3000)
        """
        L = len(sinal)
        MAX_PIXELS = 3000  # Limite para otimização de memória
        
        # Otimização: reduzir resolução temporal se necessário
        if L > MAX_PIXELS:
            step = int(np.floor(L / MAX_PIXELS))
        else:
            step = 1
        
        # Vetor de tempo reduzido (índices exatos - compatível com Octave)
        indices = np.arange(0, L, step)
        t_out = indices / fs
        
        # Prepara matriz de coeficientes (complexos)
        coefs = np.zeros((len(freqs), len(indices)), dtype=np.complex128)
        
        # Loop pelas frequências de interesse
        for i, f in enumerate(freqs):
            # Parâmetros da wavelet Morlet
            # sigma controla a largura temporal da wavelet
            sigma = 6 / (2 * np.pi * f)
            
            # Vetor de tempo da wavelet (suporte de -4σ a +4σ)
            t_wav = np.arange(-4*sigma, 4*sigma, 1/fs)
            
            # Construção da wavelet Morlet complexa
            # ψ(t) = π^(-1/4) * exp(j*2πf*t) * exp(-t²/(2σ²))
            wavelet = (np.pi**(-0.25)) * \
                      np.exp(1j * 2*np.pi*f * t_wav) * \
                      np.exp(-t_wav**2 / (2*sigma**2))
            
            # Normalização energética (preserva energia unitária)
            wavelet = wavelet / np.sqrt(np.sum(np.abs(wavelet)**2))
            
            # Convolução com o sinal (mode='same' mantém tamanho original)
            # Usa conjugado da wavelet para correlação cruzada
            resultado_completo = np.convolve(sinal, np.conj(wavelet), mode='same')
            
            # Salva apenas os pontos decimados (reduz memória)
            coefs[i, :] = resultado_completo[indices]
        
        return coefs, t_out
    
    @staticmethod
    def calcular_psd_welch(sinal, fs, nperseg=1024):
        """
        Calcula a Densidade Espectral de Potência usando o Método de Welch
        Equivalente ao pwelch() do Matlab/Octave
        
        Método de Welch:
        - Divide o sinal em segmentos sobrepostos
        - Aplica janela de Hanning em cada segmento
        - Calcula FFT de cada segmento
        - Faz média das FFTs para reduzir variância
        
        Args:
            sinal (np.ndarray): Sinal de áudio
            fs (int): Taxa de amostragem em Hz
            nperseg (int): Tamanho do segmento (janela). 
                          Default=1024 (boa resolução freq. para maioria dos casos)
            
        Returns:
            tuple: (f, Pxx)
                - f (np.ndarray): Vetor de frequências em Hz
                - Pxx (np.ndarray): Densidade espectral de potência em V²/Hz
                
        Exemplo:
            >>> sinal = np.random.randn(48000)
            >>> fs = 48000
            >>> f, Pxx = DSPProcessor.calcular_psd_welch(sinal, fs)
            >>> Pxx_db = 10 * np.log10(Pxx + 1e-12)  # Converte para dB
        """
        f, Pxx = welch(
            sinal, 
            fs, 
            window='hann',           # Janela de Hanning (boa supressão de lóbulos)
            nperseg=nperseg,         # Tamanho da janela
            noverlap=nperseg//2,     # 50% de sobreposição (padrão Matlab)
            scaling='density'        # PSD em V²/Hz
        )
        return f, Pxx
    
    @staticmethod
    def detectar_falhas_threshold(coefs, freqs, threshold_db=-30):
        """
        FUNÇÃO EXTRA: Detecta regiões de possíveis falhas na soldagem
        Baseado em threshold de magnitude da wavelet
        
        Args:
            coefs: Coeficientes da wavelet
            freqs: Vetor de frequências
            threshold_db: Limiar em dB para detecção
            
        Returns:
            dict: Regiões suspeitas com tempo e frequência
        """
        magnitude_db = 20 * np.log10(np.abs(coefs) + 1e-12)
        
        # Encontra regiões acima do threshold
        suspeitas = np.where(magnitude_db > threshold_db)
        
        if len(suspeitas[0]) > 0:
            return {
                'indices_freq': suspeitas[0],
                'indices_tempo': suspeitas[1],
                'num_pontos': len(suspeitas[0])
            }
        return None