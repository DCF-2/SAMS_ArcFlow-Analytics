% --- Analisador de Soldagem PRO v3.0 (Full Audio) ---
pkg load signal;
try pkg load wavelet; catch end
clear; clc; close all;

% =========================================================================
% 1. CONFIGURAÇÃO
% =========================================================================
% Nome do arquivo (pode ser longo agora!)
nome_arquivo = './Audios - PGD/aud_2.wav';

% Quer salvar as imagens automaticamente? (1 = Sim, 0 = Não)
salvar_imagens = 1;

fprintf('=================================================\n');
fprintf('   ANALISADOR DE SOLDAGEM PRO - VERSAO FULL\n');
fprintf('=================================================\n');

% 1.1 Carregar Arquivo
try
  [sinal_raw, Fs_raw] = audioread(nome_arquivo);
  fprintf('-> Arquivo "%s" carregado.\n', nome_arquivo);
  fprintf('   Taxa Original: %d Hz | Duracao: %.2f s\n', Fs_raw, length(sinal_raw)/Fs_raw);
catch
  fprintf('ERRO: Arquivo nao encontrado!\n');
  fprintf('Gerando sinal SIMULADO LONGO (10 segundos) para teste...\n');
  Fs_raw = 44100;
  t_sim = 0:1/Fs_raw:10.0;
  % Simula solda com variação no meio
  sinal_raw = 0.3*sin(2*pi*100*t_sim') + 0.05*randn(size(t_sim'));
  % Adiciona eventos de curto-circuito esparsos
  sinal_raw(1:5000:end) = 2.0;
  nome_arquivo = 'Simulacao_Longa';
end

% Garantir Mono
if size(sinal_raw, 2) > 1, sinal_raw = sinal_raw(:, 1); end

% =========================================================================
% 2. OTIMIZAÇÃO (A Mágica para não travar)
% =========================================================================
% Soldagem acontece em baixas frequencias (< 4kHz).
% Se a taxa for muito alta, vamos reduzir para ~10-12kHz para acelerar.
Fs_alvo = 11025;

if Fs_raw > Fs_alvo
  fator = floor(Fs_raw / Fs_alvo);
  fprintf('-> Otimizando sinal... (Reduzindo taxa em %dx)\n', fator);

  % Filtro simples (media) para evitar serrilhado antes de reduzir
  % (Versao manual do 'decimate' para garantir compatibilidade)
  sinal_filt = conv(sinal_raw, ones(fator,1)/fator, 'same');
  sinal = sinal_filt(1:fator:end);
  Fs = Fs_raw / fator;
else
  sinal = sinal_raw;
  Fs = Fs_raw;
end

fprintf('   Nova Taxa de Analise: %d Hz\n', floor(Fs));
t = (0 : length(sinal)-1) / Fs;

% =========================================================================
% 3. ANÁLISE COMPLETA
% =========================================================================

% --- A. Sinal no Tempo (Oscilograma) ---
figure(1); set(gcf, 'Position', [100, 100, 1000, 400]); % Janela larga
% Para visualizar tempo, podemos usar downsampling visual agressivo
passo_plot = ceil(length(sinal) / 5000); % Garante max 5000 pontos na tela
plot(t(1:passo_plot:end), sinal(1:passo_plot:end));
title(['Sinal Completo: ' nome_arquivo]); xlabel('Tempo (s)'); grid on;
xlim([0 max(t)]);

% --- B. FFT (Espectro Médio) ---
figure(2);
N = length(sinal);
Y = fft(sinal);
P2 = abs(Y/N);
P1 = P2(1:floor(N/2)+1);
P1(2:end-1) = 2*P1(2:end-1);
f_eixo = Fs*(0:(floor(N/2)))/N;

plot(f_eixo, P1);
title('Espectro de Frequencia (Media do Arquivo Todo)');
xlabel('Frequencia (Hz)'); xlim([0 2000]); grid on;

% --- C. Wavelet (O Filme Completo) ---
figure(3); set(gcf, 'Position', [100, 500, 1000, 400]); % Janela larga
fprintf('-> Calculando Wavelet do arquivo completo... (Isso processa blocos grandes)\n');

% Frequencias de interesse (Solda)
freqs_wav = linspace(50, 3000, 80);

% Chama nossa funcao manual
coefs = cwt_morlet(sinal, Fs, freqs_wav);

% RESOLUÇÃO DINÂMICA PARA O GRÁFICO
% Queremos uma imagem de largura ~2000 pixels maximo para não dar erro OpenGL
largura_maxima = 2000;
passo_vis = ceil(length(sinal) / largura_maxima);

if passo_vis < 1, passo_vis = 1; end
fprintf('   Gerando grafico com compressao visual de %dx...\n', passo_vis);

t_vis = t(1:passo_vis:end);
c_vis = coefs(:, 1:passo_vis:end);

imagesc(t_vis, freqs_wav, abs(c_vis));
axis xy; colormap(jet); colorbar;
title(['Wavelet Completa: ' nome_arquivo]);
xlabel('Tempo (s)'); ylabel('Frequencia (Hz)');

% =========================================================================
% 4. SALVAMENTO AUTOMATICO
% =========================================================================
if salvar_imagens
  fprintf('-> Salvando resultados em imagens PNG...\n');
  nome_base = strrep(nome_arquivo, '.wav', ''); % Remove extensao

  print(1, [nome_base '_TEMPO.png'], '-dpng');
  print(2, [nome_base '_FFT.png'], '-dpng');
  print(3, [nome_base '_WAVELET.png'], '-dpng');
  fprintf('   Sucesso! Imagens salvas na pasta atual.\n');
end

fprintf('--- Analise Finalizada ---\n');
