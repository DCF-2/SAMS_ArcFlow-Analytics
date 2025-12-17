% --- Analisador de Soldagem v13.0 (Correção de Plotagem e Exportação) ---
pkg load signal;
clear; clc; close all;

% =========================================================================
% 1. SELEÇÃO E LEITURA
% =========================================================================
fprintf('=================================================\n');
fprintf('   ANALISADOR V13.0 - ALTA DEFINIÇÃO (CORRIGIDO)\n');
fprintf('=================================================\n');

[nome_arq, caminho_arq] = uigetfile({'*.mp3;*.wav', 'Audios'}, 'Selecione o Audio');
if isequal(nome_arq, 0), disp('Cancelado.'); return; end
nome_completo = fullfile(caminho_arq, nome_arq);
[~, nome_limpo, ~] = fileparts(nome_arq);

% Para ver até 22kHz, precisamos de 44.1kHz
Fs_alvo = 44100;

try
  [sinal_raw, Fs_raw] = audioread(nome_completo);
catch
  error('Erro ao ler arquivo. Converta para WAV.');
end

if size(sinal_raw, 2) > 1, sinal_raw = sinal_raw(:, 1); end

% Resample Inteligente
if Fs_raw > Fs_alvo
    sinal = resample(sinal_raw, Fs_alvo, Fs_raw);
    Fs = Fs_alvo;
elseif Fs_raw < Fs_alvo
    % Se o áudio for gravado em 8k, não adianta inventar dados, mas mantemos o script rodando
    sinal = sinal_raw;
    Fs = Fs_raw;
    fprintf('Aviso: Audio original é de %d Hz. Freq máx será %d Hz.\n', Fs, Fs/2);
else
    sinal = sinal_raw;
    Fs = Fs_raw;
end

t_full = (0:length(sinal)-1)/Fs;

% =========================================================================
% CONFIGURAÇÃO GRÁFICA GERAL (Corrige o "Zoom" e Cortes)
% =========================================================================
% Função auxiliar para configurar a figura antes de salvar
configurar_figura = @(fig_handle) set(fig_handle, 'PaperPositionMode', 'auto', 'Units', 'pixels');

% =========================================================================
% GRAFICO 1: TEMPO
% =========================================================================
figure(1); set(gcf, 'Position', [100, 600, 800, 250]); % Tamanho mais contido
plot(t_full, sinal, 'Color', [0.1 0.1 0.1]);
axis tight; grid on;
title(['1. Sinal no Tempo: ' nome_limpo], 'Interpreter', 'none');
xlabel('Tempo (s)'); ylabel('Amplitude');
configurar_figura(gcf); % Aplica a correção

% =========================================================================
% GRAFICO 2: PSD
% =========================================================================
figure(2); set(gcf, 'Position', [100, 300, 600, 300]);
[Pxx, f_eixo] = pwelch(sinal, hanning(1024), [], 1024, Fs);
area(f_eixo, 10*log10(Pxx), 'FaceColor', [0 0.45 0.74], 'FaceAlpha', 0.6);
grid on; xlim([0 Fs/2]);
xlabel('Frequencia (Hz)'); ylabel('dB/Hz');
title('2. Espectro de Frequência');
configurar_figura(gcf);

% =========================================================================
% GRAFICO 3: WAVELET SPECTROID (O Principal)
% =========================================================================
figure(3); set(gcf, 'Position', [50, 50, 900, 600]);
fprintf('-> Calculando Wavelet Otimizada (Aguarde...)\n');

if exist('cwt_morlet_otimizada', 'file') == 2
    % Frequências lineares para ver bem de 0 a 22k
    num_freqs = 150;
    freqs = linspace(100, Fs/2, num_freqs);

    % Chama função
    [coefs, t_wavelet] = cwt_morlet_otimizada(sinal, Fs, freqs);

    % Converte dB
    S_mag = abs(coefs);
    S_dB = 20 * log10(S_mag ./ max(max(S_mag)));

    % PLOTAGEM
    % Try-Catch para garantir que se o plot falhar, avisa o erro
    try
        imagesc(freqs, t_wavelet, S_dB');
        axis xy;
        shading interp;
        colormap(jet);
        caxis([-50 0]); % Contraste

        cb = colorbar; title(cb, 'dB');
        xlabel('Frequencia (Hz)', 'FontSize', 11, 'FontWeight', 'bold');
        ylabel('Tempo (s)', 'FontSize', 11, 'FontWeight', 'bold');
        title(['3. Spectroid Alta Freq: ' nome_limpo], 'Interpreter', 'none', 'FontSize', 12);

        % Força o desenho AGORA para garantir que existe antes de salvar
        drawnow;
    catch err_plot
        fprintf('Erro ao desenhar grafico 3: %s\n', err_plot.message);
    end
else
    error('ARQUIVO "cwt_morlet_otimizada.m" NÃO ENCONTRADO!');
end
configurar_figura(gcf);

% =========================================================================
% GRAFICO 4: ZOOM
% =========================================================================
figure(4); set(gcf, 'Position', [750, 300, 500, 300]);
meio = floor(length(sinal)/2);
janela_zoom = round(0.005 * Fs); % 5ms
idx_zoom = meio : min(meio+janela_zoom, length(sinal));
plot(t_full(idx_zoom), sinal(idx_zoom), 'o-', 'MarkerSize', 3, 'Color', [0.85 0.32 0.09]);
axis tight; grid on;
title('4. Zoom Onda (5ms)');
xlabel('Tempo (s)');
configurar_figura(gcf);

% =========================================================================
% SALVAR (Com proteções extras)
% =========================================================================
pasta = 'Grafico-PGD-V13-Final';
if ~exist(pasta, 'dir'), mkdir(pasta); end

fprintf('-> Salvando imagens em "%s"...\n', pasta);

% Salva cada figura individualmente
figuras = [1, 2, 3, 4];
nomes = {'TEMPO', 'PSD', 'SPECTROID', 'ZOOM'};

for i = 1:4
    try
        % Ativa a figura antes de salvar
        figure(figuras(i));
        drawnow;

        arquivo_saida = fullfile(pasta, [nomes{i} '.png']);
        print(figuras(i), arquivo_saida, '-dpng', '-r150'); % -r150 melhora resolução
    catch err
        fprintf('Aviso: Não foi possível salvar a figura %d. Erro: %s\n', i, err.message);
    end
end

fprintf('Concluído!\n');
