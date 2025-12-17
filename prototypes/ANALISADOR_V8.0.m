% --- Analisador de Soldagem v9.0 (Correção OpenGL + Spectroid View) ---
pkg load signal;
clear; clc; close all;

% =========================================================================
% 1. CONFIGURAÇÃO
% =========================================================================
% Ajuste o nome do arquivo aqui
nome_arquivo = './Audios-PGD/PGD-INTM-AUDIOS/Ensaios-10.12/Ensaio-2/Ensaio-2.MP3';
salvar_imagens = 1;

fprintf('=================================================\n');
fprintf('   ANALISADOR V9.0 - CORRECAO VISUAL\n');
fprintf('=================================================\n');

[~, nome_limpo, ~] = fileparts(nome_arquivo);

try
  [sinal_raw, Fs_raw] = audioread(nome_arquivo);
  fprintf('-> Processando: %s\n', nome_limpo);
catch
  error('Arquivo nao encontrado! Verifique o caminho e o nome.');
end

if size(sinal_raw, 2) > 1, sinal_raw = sinal_raw(:, 1); end

% Downsampling para 16kHz (Matematica pesada da Wavelet exige isso)
Fs_alvo = 16000;
if Fs_raw > Fs_alvo
  sinal = resample(sinal_raw, Fs_alvo, Fs_raw);
  Fs = Fs_alvo;
else
  sinal = sinal_raw; Fs = Fs_raw;
end
t = (0:length(sinal)-1)/Fs;

% =========================================================================
% GRAFICO 1: TEMPO COMPLETO
% =========================================================================
figure(1); set(gcf, 'Position', [50, 600, 1000, 300]);
plot(t, sinal, 'Color', [0 0.447 0.741]);
title(['1. Domínio do Tempo: ' nome_limpo], 'Interpreter', 'none');
xlabel('Tempo (s)'); ylabel('Amplitude'); axis tight; grid on;

% =========================================================================
% GRAFICO 2: FFT SUAVIZADA (PSD)
% =========================================================================
figure(2); set(gcf, 'Position', [50, 300, 600, 400]);
window = hanning(1024); nfft = 1024;
[Pxx, f_eixo] = pwelch(sinal, window, [], nfft, Fs);
plot(f_eixo, 10*log10(Pxx), 'LineWidth', 2, 'Color', [0.85 0.32 0.098]);
title('2. Espectro de Frequência (PSD)');
xlabel('Frequencia (Hz)'); ylabel('dB/Hz');
grid on;
xlim([0 Fs/2]); % Mostra ate o limite real (ex: 8000Hz)
set(gca, 'XMinorGrid', 'on', 'YMinorGrid', 'on');

% =========================================================================
% GRAFICO 3: WAVELET SCALOGRAM (ESTILO SPECTROID)
% =========================================================================
figure(3); set(gcf, 'Position', [50, 50, 800, 600]);

fprintf('-> Calculando Wavelet Morlet (Aguarde)...\n');

if exist('cwt_morlet', 'file') == 2
    % 1. Definir Frequências
    num_freqs = 150;
    freqs = linspace(10, Fs/2, num_freqs);

    % 2. Calcular Wavelet
    coefs = cwt_morlet(sinal, Fs, freqs);
    S_wavelet = abs(coefs); % [Linhas=Freq, Colunas=Tempo]

    % 3. REDUÇÃO DE RESOLUÇÃO PARA PLOTAGEM (CORREÇÃO DO ERRO OPENGL)
    % Se a imagem for muito alta (>4000 pixels), reduzimos apenas para exibir.
    % Isso não afeta o cálculo, apenas a visualização.
    max_pixels_display = 4000;

    if length(t) > max_pixels_display
        step_plot = ceil(length(t) / max_pixels_display);
        indices_plot = 1:step_plot:length(t);

        % Pegamos apenas as amostras necessárias
        S_plot = S_wavelet(:, indices_plot);
        t_plot = t(indices_plot);
        fprintf('   (Aviso: Visualização otimizada de %d para %d pontos no tempo)\n', length(t), length(t_plot));
    else
        S_plot = S_wavelet;
        t_plot = t;
    end

    % 4. PLOTAGEM INVERTIDA (Espectroid)
    % Eixo X = Frequência (freqs)
    % Eixo Y = Tempo (t_plot)
    % Matriz Transposta (S_plot') para alinhar [Tempo x Freq]
    imagesc(freqs, t_plot, S_plot');

    axis xy; % Tempo 0 embaixo
    colormap(jet);
    shading interp; % Suaviza o visual

    xlabel('Frequencia (Hz)');
    ylabel('Tempo (s)');
    title(['3. Wavelet Morlet (Spectroid View): ' nome_limpo], 'Interpreter', 'none');

else
    fprintf('ERRO CRÍTICO: O arquivo "cwt_morlet.m" nao está na pasta!\n');
    title('ERRO: Falta arquivo cwt_morlet.m');
end

% =========================================================================
% GRAFICO 4: ZOOM NA SENOIDE
% =========================================================================
figure(4); set(gcf, 'Position', [650, 300, 600, 400]);
meio = floor(length(sinal)/2);
janela_zoom = round(0.05 * Fs);
inicio = meio;
fim = min(meio + janela_zoom, length(sinal));
t_zoom = t(inicio:fim);
sinal_zoom = sinal(inicio:fim);

plot(t_zoom, sinal_zoom, '-o', 'Color', [0.466 0.674 0.188], 'MarkerSize', 3);
title('4. Zoom na Senoide (0.05s)');
xlabel('Tempo (s)'); ylabel('Amplitude'); grid on; axis tight;

% =========================================================================
% SALVAR
% =========================================================================
if salvar_imagens
  pasta = 'Grafico-PGD-Wavelet-v9';
  if ~exist(pasta, 'dir'), mkdir(pasta); end

  % Força atualização do gráfico antes de salvar
  drawnow;

  print(1, fullfile(pasta, [nome_limpo '_TEMPO.png']), '-dpng');
  print(2, fullfile(pasta, [nome_limpo '_PSD.png']), '-dpng');
  print(3, fullfile(pasta, [nome_limpo '_WAVELET_SPECTROID.png']), '-dpng');
  print(4, fullfile(pasta, [nome_limpo '_ZOOM.png']), '-dpng');
  fprintf('Imagens salvas em: %s/\n', pasta);
end
