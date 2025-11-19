% --- Analisador de Soldagem Completo v2.0 ---
pkg load signal;
% Tenta carregar wavelet, se der erro avisa mas continua (usando nossa funcao manual)
try pkg load wavelet; catch end

clear; clc; close all;

% =========================================================================
% 1. CONFIGURAÇÃO E LEITURA
% =========================================================================
nome_arquivo = './Audios - PGD/aud_2.wav';

fprintf('--- Iniciando Analise de: %s ---\n', nome_arquivo);

try
  [sinal, Fs] = audioread(nome_arquivo);
  fprintf('-> Arquivo carregado! Taxa: %d Hz\n', Fs);
catch
  % Se nao tiver arquivo, vamos GERAR um sinal de solda FALSO para teste
  fprintf('AVISO: Arquivo nao encontrado. Gerando sinal SIMULADO de solda...\n');
  Fs = 44100;
  t_sim = 0:1/Fs:1.0;
  % Simula um zumbido de 100Hz + picos aleatorios (curto circuito)
  sinal = 0.3*sin(2*pi*100*t_sim') + 0.1*randn(size(t_sim'));
  % Adiciona "estouros" periodicos
  sinal(1:2000:end) = sinal(1:2000:end) + 2.0;
  nome_arquivo = 'Simulacao (Teste)';
end

% Garantir Mono
if size(sinal, 2) > 1
  sinal = sinal(:, 1);
end

% Recortar 1 segundo para analise rapida
segundos = 1.0;
amostras = min(length(sinal), round(segundos * Fs));
sinal_cut = sinal(1:amostras);
t = (0 : length(sinal_cut)-1) / Fs;

% =========================================================================
% 2. ANÁLISE 1: O SINAL NO TEMPO (A "Senoide")
% =========================================================================
figure(1);
plot(t, sinal_cut);
title(['1. Oscilograma (Sinal no Tempo): ' nome_arquivo]);
xlabel('Tempo (segundos)');
ylabel('Amplitude');
grid on;
xlim([0 segundos]);
% Dica visual: Se for solda, vai parecer um "rabisco" denso com picos.

% =========================================================================
% 3. ANÁLISE 2: FFT (ESPECTRO)
% =========================================================================
figure(2);
N = length(sinal_cut);
Y = fft(sinal_cut);
P2 = abs(Y/N);
P1 = P2(1:N/2+1);
P1(2:end-1) = 2*P1(2:end-1);
f_eixo = Fs*(0:(N/2))/N;

plot(f_eixo, P1);
title(['2. Espectro de Frequencia (FFT)']);
xlabel('Frequencia (Hz)');
ylabel('Magnitude');
grid on;
xlim([0 2000]); % Foco nos graves (onde a solda acontece)

% =========================================================================
% 4. ANÁLISE 3: WAVELET (TEMPO-FREQUÊNCIA)
% =========================================================================
fprintf('-> Calculando Wavelet... (aguarde um instante)\n');

% Configura frequencias de 50Hz a 3000Hz
freqs_wav = linspace(50, 3000, 100);

% Chama sua funcao MANUAL (que criamos antes)
% Certifique-se que o arquivo 'minha_cwt_morlet.m' esta na mesma pasta!
coefs = cwt_morlet(sinal_cut, Fs, freqs_wav);

% Reduz resolução para o grafico nao travar (Passo 50)
passo = 50;
t_vis = t(1:passo:end);
c_vis = coefs(:, 1:passo:end);

figure(3);
imagesc(t_vis, freqs_wav, abs(c_vis));
axis xy;
colormap(jet);
colorbar;
title(['3. Wavelet (Scalograma): Eventos no Tempo']);
xlabel('Tempo (s)');
ylabel('Frequencia (Hz)');

fprintf('--- Analise Concluida! Veja as 3 Figuras. ---\n');
