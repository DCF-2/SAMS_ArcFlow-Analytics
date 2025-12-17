% --- Analisador de Soldagem v10.1 (Seletor de Arquivo + Debug) ---
pkg load signal;
clear; clc; close all;

% =========================================================================
% 1. SELEÇÃO DO ARQUIVO (AUTOMÁTICA)
% =========================================================================
fprintf('=================================================\n');
fprintf('   ANALISADOR V10.1 - SELECIONE O ARQUIVO\n');
fprintf('=================================================\n');

% Abre uma janela para você escolher o arquivo
[nome_arq, caminho_arq] = uigetfile({'*.mp3;*.wav', 'Arquivos de Audio (*.mp3, *.wav)'}, 'Selecione o Audio do Ensaio');

if isequal(nome_arq, 0)
    disp('Seleção cancelada pelo usuário.');
    return;
end

nome_completo = fullfile(caminho_arq, nome_arq);
[~, nome_limpo, ~] = fileparts(nome_arq);

fprintf('-> Arquivo selecionado: %s\n', nome_arq);

% Tenta ler SEM esconder o erro real
try
  [sinal_raw, Fs_raw] = audioread(nome_completo);
  fprintf('-> Leitura OK! Taxa de amostragem: %d Hz\n', Fs_raw);
catch err
  fprintf('\nERRO CRÍTICO NA LEITURA DO ARQUIVO:\n');
  fprintf('%s\n', err.message);
  fprintf('--------------------------------------------------\n');
  fprintf('DICA: Se o erro for "mpg123" ou "junk", seu MP3 está corrompido.\n');
  fprintf('SOLUÇÃO: Converta esse audio para .WAV usando um conversor online ou ffmpeg.\n');
  error('Execução interrompida.');
end

if size(sinal_raw, 2) > 1, sinal_raw = sinal_raw(:, 1); end

% Downsampling para 22kHz (Otimização para Wavelet)
Fs_alvo = 44100;
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
plot(t, sinal, 'Color', [0.1 0.1 0.1]);
title(['1. Domínio do Tempo: ' nome_limpo], 'Interpreter', 'none', 'FontWeight', 'bold');
xlabel('Tempo (s)'); ylabel('Amplitude'); axis tight; grid on;
set(gca, 'GridAlpha', 0.3);

% =========================================================================
% GRAFICO 2: FFT SUAVIZADA (PSD)
% =========================================================================
figure(2); set(gcf, 'Position', [50, 300, 600, 400]);
window = hanning(1024); nfft = 1024;
[Pxx, f_eixo] = pwelch(sinal, window, [], nfft, Fs);

area(f_eixo, 10*log10(Pxx), 'FaceColor', [0 0.447 0.741], 'EdgeColor', 'none', 'FaceAlpha', 0.6);
hold on;
plot(f_eixo, 10*log10(Pxx), 'Color', [0 0.3 0.6], 'LineWidth', 1.5);

title('2. Espectro de Frequência (PSD)', 'FontWeight', 'bold');
xlabel('Frequencia (Hz)'); ylabel('dB/Hz');
grid on; xlim([0 Fs/2]);
box on;

% =========================================================================
% GRAFICO 3: WAVELET SCALOGRAM (VISUAL SPECTROID)
% =========================================================================
figure(3); set(gcf, 'Position', [50, 50, 900, 700]);

fprintf('-> Calculando Wavelet Morlet...\n');

if exist('cwt_morlet', 'file') == 2
    % Definição de frequências
    num_freqs = 200;
    freqs = linspace(10, Fs/2, num_freqs);

    % Cálculo
    coefs = cwt_morlet(sinal, Fs, freqs);

    % Conversão para Visual Bonito (dB)
    S_mag = abs(coefs);
    max_val = max(max(S_mag));
    S_dB = 20 * log10(S_mag ./ max_val);

    % Otimização de Plotagem (Evita travar o PC)
    max_pixels_display = 4000;
    if length(t) > max_pixels_display
        step_plot = ceil(length(t) / max_pixels_display);
        indices_plot = 1:step_plot:length(t);
        S_plot = S_dB(:, indices_plot);
        t_plot = t(indices_plot);
    else
        S_plot = S_dB;
        t_plot = t;
    end

    % PLOTAGEM INVERTIDA (Eixo X = Freq, Eixo Y = Tempo)
    imagesc(freqs, t_plot, S_plot');

    axis xy;
    shading interp;
    colormap(jet);
    caxis([-60 0]); % Contraste alto

    cb = colorbar;
    title(cb, 'dB');

    xlabel('Frequencia (Hz)', 'FontSize', 12, 'FontWeight', 'bold');
    ylabel('Tempo (s)', 'FontSize', 12, 'FontWeight', 'bold');
    title(['3. Wavelet Spectroid: ' nome_limpo], 'Interpreter', 'none', 'FontSize', 14);

    set(gca, 'FontSize', 10, 'LineWidth', 1.5);
else
    msgbox('ERRO: O arquivo cwt_morlet.m não está na mesma pasta!', 'Erro de Dependência', 'error');
    error('Falta arquivo cwt_morlet.m');
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

plot(t_zoom, sinal_zoom, 'o-', 'Color', [0.85 0.32 0.098], 'MarkerSize', 4, 'LineWidth', 1.5, 'MarkerFaceColor', 'w');
title('4. Zoom na Senoide (0.05s)', 'FontWeight', 'bold');
xlabel('Tempo (s)'); ylabel('Amplitude'); grid on; axis tight;
set(gca, 'GridAlpha', 0.4);

% =========================================================================
% SALVAR
% =========================================================================
salvar_imagens = 1; % Forcei para 1
if salvar_imagens
  pasta = 'Grafico-PGD-Final-v10_1';
  if ~exist(pasta, 'dir'), mkdir(pasta); end

  drawnow;
  print(1, fullfile(pasta, [nome_limpo '_TEMPO.png']), '-dpng');
  print(2, fullfile(pasta, [nome_limpo '_PSD.png']), '-dpng');
  print(3, fullfile(pasta, [nome_limpo '_SPECTROID_PRO.png']), '-dpng');
  print(4, fullfile(pasta, [nome_limpo '_ZOOM.png']), '-dpng');
  fprintf('Imagens salvas em: %s/\n', pasta);
end
