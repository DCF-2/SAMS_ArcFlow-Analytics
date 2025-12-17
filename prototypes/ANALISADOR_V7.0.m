% --- Analisador de Soldagem v7.0 (Com Zoom na Senoide) ---
pkg load signal;
clear; clc; close all;

% =========================================================================
% 1. CONFIGURAÇÃO
% =========================================================================
nome_arquivo = './Audios-PGD/PGD-INTM-AUDIOS/Ensaios-10.12/Ensaio-2/Ensaio-2.MP3';
id_cenario = 2; % 1=Instável, 2=Estável, 3=Performance
salvar_imagens = 1;

fprintf('=================================================\n');
fprintf('   ANALISADOR V7.0 - ZOOM NA SENOIDE\n');
fprintf('=================================================\n');

[~, nome_limpo, ~] = fileparts(nome_arquivo);

try
  [sinal_raw, Fs_raw] = audioread(nome_arquivo);
  fprintf('-> Processando: %s\n', nome_limpo);
catch
  error('Arquivo nao encontrado!');
end

if size(sinal_raw, 2) > 1, sinal_raw = sinal_raw(:, 1); end

% Downsampling Otimizado
Fs_alvo = 16000;
if Fs_raw > Fs_alvo
  sinal = resample(sinal_raw, Fs_alvo, Fs_raw);
  Fs = Fs_alvo;
else
  sinal = sinal_raw; Fs = Fs_raw;
end
t = (0:length(sinal)-1)/Fs;

% =========================================================================
% GRAFICO 1: TEMPO COMPLETO (OSCILOGRAMA GERAL)
% =========================================================================
figure(1); set(gcf, 'Position', [50, 600, 1000, 300]);
plot(t, sinal, 'Color', [0 0.447 0.741]);
title(['1. Domínio do Tempo (Completo): ' nome_limpo], 'Interpreter', 'none');
xlabel('Tempo (s)'); ylabel('Amplitude'); axis tight; grid on;

% =========================================================================
% GRAFICO 2: FFT SUAVIZADA (PSD - MÉTODO WELCH)
% =========================================================================
figure(2); set(gcf, 'Position', [50, 300, 600, 400]);
window = hanning(1024); nfft = 1024;
[Pxx, f_eixo] = pwelch(sinal, window, [], nfft, Fs);
plot(f_eixo, 10*log10(Pxx), 'LineWidth', 2, 'Color', [0.85 0.32 0.098]);
title('2. Espectro Suavizado (Tendência de Frequência)');
xlabel('Frequencia (Hz)'); ylabel('Intensidade (dB/Hz)');
grid on; xlim([0 4000]);
set(gca, 'XMinorGrid', 'on', 'YMinorGrid', 'on');

% =========================================================================
% GRAFICO 3: ESPECTROGRAMA (SONAR)
% =========================================================================
figure(3); set(gcf, 'Position', [50, 50, 1000, 400]);
janela = 512; step = 128;

% Calcula o Spectrograma
[t_spec, f, S] = specgram(sinal, 2*janela, Fs, hanning(janela), janela-step);

% Converte para dB
S_dB = 20*log10(abs(S)+1e-6);

% Plota
imagesc(t_spec, f, S_dB);
axis xy; colormap(jet);

cb = colorbar;
% O comando 'title' aplicado ao handle 'cb' coloca o texto EM CIMA da barra
h_title = title(cb, 'Intensidade (Decibeis)');
set(h_title, 'FontSize', 11, 'FontWeight', 'bold', 'Color', 'black');
% ------------------------------------

title(['3. Espectrograma: ' nome_limpo], 'Interpreter', 'none');
xlabel('Tempo (s)'); ylabel('Frequencia (Hz)'); ylim([0 4000]);

% =========================================================================
% GRAFICO 4: ZOOM NA SENOIDE (O QUE O PROFESSOR QUER VER)
% =========================================================================
% Aqui está o segredo: Pegamos apenas 0.05 segundos (50ms) do meio do áudio.
% Isso é suficiente para ver 3 ciclos de onda de 60Hz.
figure(4); set(gcf, 'Position', [650, 300, 600, 400]);

meio = floor(length(sinal)/2);
janela_zoom = round(0.05 * Fs); % 50ms de janela
inicio = meio;
fim = min(meio + janela_zoom, length(sinal));

t_zoom = t(inicio:fim);
sinal_zoom = sinal(inicio:fim);

% Plota com "bolinhas" (-o) para mostrar que são pontos digitais formando a onda
plot(t_zoom, sinal_zoom, '-o', 'Color', [0.466 0.674 0.188], 'MarkerSize', 3);
title('4. Detalhe da Forma de Onda (Senoide)', 'FontSize', 12);
xlabel('Tempo (s)'); ylabel('Amplitude');
grid on; axis tight;

% Adiciona anotação explicativa
text(0.5, 0.9, 'Zoom de 0.05s', 'Units', 'normalized', 'HorizontalAlignment', 'center', 'BackgroundColor', 'w');


% =========================================================================
% SALVAR
% =========================================================================
if salvar_imagens
  pasta = 'Grafico-PGD-Final-v7';
  if ~exist(pasta, 'dir'), mkdir(pasta); end

  print(1, fullfile(pasta, [nome_limpo '_TEMPO.png']), '-dpng');
  print(2, fullfile(pasta, [nome_limpo '_FFT_PSD.png']), '-dpng');
  print(3, fullfile(pasta, [nome_limpo '_ESPECTRO.png']), '-dpng');
  print(4, fullfile(pasta, [nome_limpo '_SENOIDE_ZOOM.png']), '-dpng');
  fprintf('Imagens salvas em: %s/\n', pasta);
end
