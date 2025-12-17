% --- Analisador de Soldagem v10.0 (Visual Pro + Spectroid View) ---
pkg load signal;
clear; clc; close all;

% =========================================================================
% 1. CONFIGURAÇÃO
% =========================================================================
nome_arquivo = './Audios-PGD/PGD-INTM-AUDIOS/teste.wav';
salvar_imagens = 1;

fprintf('=================================================\n');
fprintf('   ANALISADOR V10.0 - VISUAL PROFISSIONAL\n');
fprintf('=================================================\n');

[~, nome_limpo, ~] = fileparts(nome_arquivo);

try
  [sinal_raw, Fs_raw] = audioread(nome_arquivo);
  fprintf('-> Processando: %s\n', nome_limpo);
catch
  error('Arquivo nao encontrado! Verifique o caminho.');
end

if size(sinal_raw, 2) > 1, sinal_raw = sinal_raw(:, 1); end

% Downsampling para 16kHz (Otimização)
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
plot(t, sinal, 'Color', [0.1 0.1 0.1]); % Cinza escuro quase preto
title(['1. Domínio do Tempo: ' nome_limpo], 'Interpreter', 'none', 'FontWeight', 'bold');
xlabel('Tempo (s)'); ylabel('Amplitude'); axis tight; grid on;
set(gca, 'GridAlpha', 0.3); % Grade mais suave

% =========================================================================
% GRAFICO 2: FFT SUAVIZADA (PSD)
% =========================================================================
figure(2); set(gcf, 'Position', [50, 300, 600, 400]);
window = hanning(1024); nfft = 1024;
[Pxx, f_eixo] = pwelch(sinal, window, [], nfft, Fs);

% Plotagem com preenchimento (Area) fica mais bonito visualmente
area(f_eixo, 10*log10(Pxx), 'FaceColor', [0 0.447 0.741], 'EdgeColor', 'none', 'FaceAlpha', 0.6);
hold on;
plot(f_eixo, 10*log10(Pxx), 'Color', [0 0.3 0.6], 'LineWidth', 1.5); % Linha de contorno

title('2. Espectro de Frequência (PSD)', 'FontWeight', 'bold');
xlabel('Frequencia (Hz)'); ylabel('dB/Hz');
grid on; xlim([0 Fs/2]);
box on;

% =========================================================================
% GRAFICO 3: WAVELET SCALOGRAM (ESTILO SPECTROID PRO)
% =========================================================================
figure(3); set(gcf, 'Position', [50, 50, 900, 700]);

fprintf('-> Calculando Wavelet Morlet...\n');

if exist('cwt_morlet', 'file') == 2
    % 1. Definir Frequências
    num_freqs = 200; % Aumentei um pouco a resolução de frequência
    freqs = linspace(10, Fs/2, num_freqs);

    % 2. Calcular Wavelet
    coefs = cwt_morlet(sinal, Fs, freqs);

    % --- O SEGREDO DO VISUAL ESTÁ AQUI ---
    % Converte para Magnitude
    S_mag = abs(coefs);

    % Converte para Decibéis (dB) normalizado pelo máximo
    % Isso garante que o pico seja 0 dB e o resto negativo
    max_val = max(max(S_mag));
    S_dB = 20 * log10(S_mag ./ max_val);

    % 3. Redução de Resolução para Plotagem (Evita erro OpenGL)
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

    % 4. PLOTAGEM INVERTIDA (Spectroid)
    % Transposta (S_plot') para virar: Freq=X, Tempo=Y
    imagesc(freqs, t_plot, S_plot');

    axis xy; % Tempo 0 embaixo
    shading interp; % Suavização máxima
    colormap(jet); % Jet é clássico, mas tente 'hot' ou 'inferno' se tiver pacote extra

    % --- AJUSTE FINO DE CONTRASTE ---
    % Mostra apenas os dados entre -60dB e 0dB.
    % Tudo abaixo de -60dB vira azul solido (fundo).
    caxis([-60 0]);

    cb = colorbar;
    title(cb, 'dB');

    xlabel('Frequencia (Hz)', 'FontSize', 12, 'FontWeight', 'bold');
    ylabel('Tempo (s)', 'FontSize', 12, 'FontWeight', 'bold');
    title(['3. Wavelet Spectroid: ' nome_limpo], 'Interpreter', 'none', 'FontSize', 14);

    % Ajuste de visualização dos eixos
    set(gca, 'FontSize', 10, 'LineWidth', 1.5);

else
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

plot(t_zoom, sinal_zoom, 'o-', 'Color', [0.85 0.32 0.098], 'MarkerSize', 4, 'LineWidth', 1.5, 'MarkerFaceColor', 'w');
title('4. Zoom na Senoide (0.05s)', 'FontWeight', 'bold');
xlabel('Tempo (s)'); ylabel('Amplitude'); grid on; axis tight;
set(gca, 'GridAlpha', 0.4);

% =========================================================================
% SALVAR
% =========================================================================
if salvar_imagens
  pasta = 'Grafico-PGD-Final-v10';
  if ~exist(pasta, 'dir'), mkdir(pasta); end

  drawnow;
  print(1, fullfile(pasta, [nome_limpo '_TEMPO.png']), '-dpng');
  print(2, fullfile(pasta, [nome_limpo '_PSD.png']), '-dpng');
  print(3, fullfile(pasta, [nome_limpo '_SPECTROID_PRO.png']), '-dpng');
  print(4, fullfile(pasta, [nome_limpo '_ZOOM.png']), '-dpng');
  fprintf('Imagens salvas em: %s/\n', pasta);
end
