% --- Analisador de Soldagem v12.0 (High Frequency + Otimizado) ---
pkg load signal;
clear; clc; close all;

% =========================================================================
% 1. SELEÇÃO E CONFIGURAÇÃO
% =========================================================================
fprintf('=================================================\n');
fprintf('   ANALISADOR V12.0 - ALTA DEFINIÇÃO (22kHz)\n');
fprintf('=================================================\n');

[nome_arq, caminho_arq] = uigetfile({'*.mp3;*.wav', 'Audios (*.mp3, *.wav)'}, 'Selecione o Audio');
if isequal(nome_arq, 0), disp('Cancelado.'); return; end
nome_completo = fullfile(caminho_arq, nome_arq);
[~, nome_limpo, ~] = fileparts(nome_arq);

% --- CONFIGURAÇÃO CRÍTICA PARA ALTA FREQUÊNCIA ---
% Para ver 22kHz, precisamos de no mínimo 44.1kHz de amostragem.
Fs_alvo = 44100;

try
  [sinal_raw, Fs_raw] = audioread(nome_completo);
catch
  error('Erro ao ler arquivo. Tente converter para WAV.');
end

if size(sinal_raw, 2) > 1, sinal_raw = sinal_raw(:, 1); end

% Resample apenas se necessário (se o original for menor que 44k, mantemos o original)
if Fs_raw > Fs_alvo
    fprintf('-> Ajustando de %d Hz para %d Hz...\n', Fs_raw, Fs_alvo);
    sinal = resample(sinal_raw, Fs_alvo, Fs_raw);
    Fs = Fs_alvo;
elseif Fs_raw < Fs_alvo
    fprintf('-> Aviso: O audio original tem apenas %d Hz.\n', Fs_raw);
    fprintf('   A frequência máxima visível será %d Hz (Nyquist).\n', Fs_raw/2);
    sinal = sinal_raw;
    Fs = Fs_raw;
else
    sinal = sinal_raw;
    Fs = Fs_raw;
end

t_full = (0:length(sinal)-1)/Fs;

% =========================================================================
% GRAFICOS (1 e 2 - Padrão)
% =========================================================================
% 1. Tempo
figure(1); set(gcf, 'Position', [50, 600, 1000, 250]);
plot(t_full, sinal, 'Color', [0.1 0.1 0.1]); axis tight; grid on;
title(['1. Sinal no Tempo: ' nome_limpo], 'Interpreter', 'none');

% 2. PSD (Espectro)
figure(2); set(gcf, 'Position', [50, 300, 600, 350]);
[Pxx, f_eixo] = pwelch(sinal, hanning(1024), [], 1024, Fs);
area(f_eixo, 10*log10(Pxx), 'FaceColor', [0 0.45 0.74], 'FaceAlpha', 0.6);
grid on; xlim([0 Fs/2]);
xlabel('Frequencia (Hz)'); title('2. Espectro de Frequência (PSD)');

% =========================================================================
% GRAFICO 3: WAVELET OTIMIZADA (O Segredo)
% =========================================================================
figure(3); set(gcf, 'Position', [50, 50, 900, 600]);
fprintf('-> Calculando Wavelet Otimizada (Aguarde...)\n');

if exist('cwt_morlet_otimizada', 'file') == 2
    % Frequências: Focando onde você quer (até 22k, ênfase em 8k-15k)
    % Usamos logspace para dar mais detalhe nas baixas, ou linspace para linear.
    % Vamos usar linear para ver bem o intervalo 8k-15k.
    num_freqs = 150;
    freqs = linspace(100, Fs/2, num_freqs);

    % CHAMADA DA FUNÇÃO NOVA (Retorna coefs e o tempo já reduzidos)
    [coefs, t_wavelet] = cwt_morlet_otimizada(sinal, Fs, freqs);

    % Processamento Visual
    S_mag = abs(coefs);
    S_dB = 20 * log10(S_mag ./ max(max(S_mag)));

    % PLOTAGEM
    % Note que usamos 't_wavelet' que veio da função, não o 't' original
    imagesc(freqs, t_wavelet, S_dB');

    axis xy; shading interp; colormap(jet);
    caxis([-50 0]); % Contraste focado nos picos

    cb = colorbar; title(cb, 'dB');
    xlabel('Frequencia (Hz)'); ylabel('Tempo (s)');
    title(['3. Spectroid Alta Frequência (Max: ' num2str(Fs/2/1000) ' kHz)'], 'Interpreter', 'none');

    % Zoom visual opcional no eixo X se quiser focar na banda 8k-15k
    % xlim([0 22000]);
else
    error('Falta o arquivo cwt_morlet_otimizada.m na pasta!');
end

% =========================================================================
% GRAFICO 4: ZOOM SENOIDE
% =========================================================================
figure(4); set(gcf, 'Position', [700, 300, 500, 300]);
meio = floor(length(sinal)/2);
janela_zoom = round(0.005 * Fs); % 5ms de zoom (bem detalhado para alta freq)
idx_zoom = meio : min(meio+janela_zoom, length(sinal));
plot(t_full(idx_zoom), sinal(idx_zoom), 'o-', 'MarkerSize', 3);
axis tight; grid on; title('4. Zoom Ultra-Fino (Forma de Onda)');

% Salvar
pasta = 'Grafico-PGD-V12-HighFreq';
if ~exist(pasta, 'dir'), mkdir(pasta); end
print(3, fullfile(pasta, 'SPECTRO_FULL.png'), '-dpng');
fprintf('Concluido! Imagens salvas em %s\n', pasta);
