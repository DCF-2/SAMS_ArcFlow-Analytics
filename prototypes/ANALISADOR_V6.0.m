% --- Analisador de Soldagem v6.0 (FFT Suavizada - Método Welch) ---
pkg load signal;
clear; clc; close all;

% =========================================================================
% 1. CONFIGURAÇÃO
% =========================================================================
% Coloque seu arquivo aqui
nome_arquivo = './Audios-PGD/PGD-INTM-AUDIOS/Ensaios-10.12/Ensaio-2/Ensaio-2.MP3';

% LEGENDA AUTOMÁTICA
% 1=Instável, 2=Estável (MIG), 3=Alta Performance
id_cenario = 2;

salvar_imagens = 1;

fprintf('=================================================\n');
fprintf('   ANALISADOR V6.0 - FFT SUAVIZADA (WELCH)\n');
fprintf('=================================================\n');

% Extrair nome
[~, nome_limpo, ~] = fileparts(nome_arquivo);

% Carregar
try
  [sinal_raw, Fs_raw] = audioread(nome_arquivo);
  fprintf('-> Processando: %s\n', nome_limpo);
catch
  error('Arquivo nao encontrado!');
end

% Mono
if size(sinal_raw, 2) > 1, sinal_raw = sinal_raw(:, 1); end

% Downsampling (16kHz é suficiente e acelera o cálculo)
Fs_alvo = 16000;
if Fs_raw > Fs_alvo
  sinal = resample(sinal_raw, Fs_alvo, Fs_raw);
  Fs = Fs_alvo;
else
  sinal = sinal_raw; Fs = Fs_raw;
end
t = (0:length(sinal)-1)/Fs;

% =========================================================================
% GRAFICO 1: TEMPO (OSCILOGRAMA)
% =========================================================================
figure(1); set(gcf, 'Position', [50, 600, 1000, 300]);
plot(t, sinal, 'Color', [0 0.447 0.741]);
title(['1. Domínio do Tempo: ' nome_limpo], 'Interpreter', 'none');
xlabel('Tempo (s)'); ylabel('Amplitude'); axis tight; grid on;

% =========================================================================
% GRAFICO 2: FFT SUAVIZADA (MÉTODO WELCH / PSD)
% =========================================================================
% AQUI ESTA A CORREÇÃO: Em vez de FFT pura, usamos pwelch para suavizar.
figure(2); set(gcf, 'Position', [50, 300, 600, 400]);

% Configuração do Welch
window = hanning(1024); % Janela de suavização
nfft = 1024;            % Resolução de frequência

% Calcula a Densidade Espectral de Potência (PSD)
[Pxx, f_eixo] = pwelch(sinal, window, [], nfft, Fs);

% Plota em Decibéis (10*log10) para ficar igual som profissional
plot(f_eixo, 10*log10(Pxx), 'LineWidth', 2, 'Color', [0.85 0.32 0.098]);

title('2. Espectro Suavizado (PSD)', 'FontSize', 12);
xlabel('Frequencia (Hz)');
ylabel('Intensidade (dB/Hz)'); % Agora o eixo Y faz sentido físico
grid on;
xlim([0 4000]); % Foco na solda

% Adiciona uma grade menor para facilitar leitura
set(gca, 'XMinorGrid', 'on', 'YMinorGrid', 'on');

% =========================================================================
% GRAFICO 3: ESPECTROGRAMA (SONAR)
% =========================================================================
figure(3); set(gcf, 'Position', [50, 50, 1000, 400]);
janela = 512; step = 128;

[S, f, t_spec] = specgram(sinal, 2*janela, Fs, hanning(janela), janela-step);

% Convertendo para dB para bater com a explicação
S_dB = 20*log10(abs(S)+1e-6);

imagesc(t_spec, f, S_dB);
axis xy; colormap(jet);
cb = colorbar;
ylabel(cb, 'Intensidade (dB)'); % Legenda da barra de cores

title(['3. Espectrograma: ' nome_limpo], 'Interpreter', 'none');
xlabel('Tempo (s)'); ylabel('Frequencia (Hz)'); ylim([0 4000]);

% =========================================================================
% SALVAR
% =========================================================================
if salvar_imagens
  pasta = 'Grafico-PGD-Final';
  if ~exist(pasta, 'dir'), mkdir(pasta); end

  print(1, fullfile(pasta, [nome_limpo '_TEMPO.png']), '-dpng');
  print(2, fullfile(pasta, [nome_limpo '_FFT_PSD.png']), '-dpng');
  print(3, fullfile(pasta, [nome_limpo '_ESPECTRO.png']), '-dpng');
  fprintf('Imagens salvas em: %s/\n', pasta);
end
