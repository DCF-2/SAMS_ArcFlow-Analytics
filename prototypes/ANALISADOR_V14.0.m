% --- Analisador de Soldagem v14.0 (Organização de Pastas Automática) ---
pkg load signal;
clear; clc; close all;

% =========================================================================
% 1. SELEÇÃO E LEITURA
% =========================================================================
fprintf('=================================================\n');
fprintf('   ANALISADOR V14.0 - ORGANIZADOR AUTOMATICO\n');
fprintf('=================================================\n');

% Seleção do arquivo
[nome_arq, caminho_arq] = uigetfile({'*.mp3;*.wav', 'Arquivos de Audio'}, 'Selecione o Audio');
if isequal(nome_arq, 0), disp('Cancelado.'); return; end

% Prepara nomes e caminhos
nome_completo = fullfile(caminho_arq, nome_arq);
[~, nome_limpo, ~] = fileparts(nome_arq); % 'nome_limpo' é o nome sem .mp3

% Configuração de Amostragem (44.1k para ver até 22k)
Fs_alvo = 44100;

try
  [sinal_raw, Fs_raw] = audioread(nome_completo);
  fprintf('-> Processando arquivo: %s\n', nome_limpo);
catch
  error('Erro ao ler arquivo. Converta para WAV se for MP3 corrompido.');
end

if size(sinal_raw, 2) > 1, sinal_raw = sinal_raw(:, 1); end

% Resample se necessário
if Fs_raw > Fs_alvo
    sinal = resample(sinal_raw, Fs_alvo, Fs_raw);
    Fs = Fs_alvo;
elseif Fs_raw < Fs_alvo
    sinal = sinal_raw;
    Fs = Fs_raw;
    fprintf('Aviso: Audio original (%d Hz) é menor que o alvo.\n', Fs);
else
    sinal = sinal_raw;
    Fs = Fs_raw;
end

t_full = (0:length(sinal)-1)/Fs;

% Função auxiliar para garantir que o gráfico salvo seja igual ao da tela
configurar_figura = @(fig_handle) set(fig_handle, 'PaperPositionMode', 'auto', 'Units', 'pixels');

% =========================================================================
% GRAFICO 1: TEMPO
% =========================================================================
figure(1); set(gcf, 'Position', [100, 600, 800, 250]);
plot(t_full, sinal, 'Color', [0.1 0.1 0.1]);
axis tight; grid on;
title(['1. Domínio do Tempo: ' nome_limpo], 'Interpreter', 'none');
xlabel('Tempo (s)'); ylabel('Amplitude');
configurar_figura(gcf);

% =========================================================================
% GRAFICO 2: PSD
% =========================================================================
figure(2); set(gcf, 'Position', [100, 300, 600, 300]);
[Pxx, f_eixo] = pwelch(sinal, hanning(1024), [], 1024, Fs);
area(f_eixo, 10*log10(Pxx), 'FaceColor', [0 0.45 0.74], 'FaceAlpha', 0.6);
grid on; xlim([0 Fs/2]);
xlabel('Frequencia (Hz)'); ylabel('dB/Hz');
title(['2. Espectro PSD: ' nome_limpo], 'Interpreter', 'none');
configurar_figura(gcf);

% =========================================================================
% GRAFICO 3: WAVELET SPECTROID (Otimizada)
% =========================================================================
figure(3); set(gcf, 'Position', [50, 50, 900, 600]);
fprintf('-> Calculando Wavelet (Aguarde...)\n');

if exist('cwt_morlet_otimizada', 'file') == 2
    num_freqs = 150;
    freqs = linspace(100, Fs/2, num_freqs);

    [coefs, t_wavelet] = cwt_morlet_otimizada(sinal, Fs, freqs);

    S_mag = abs(coefs);
    S_dB = 20 * log10(S_mag ./ max(max(S_mag)));

    try
        imagesc(freqs, t_wavelet, S_dB');
        axis xy; shading interp; colormap(jet); caxis([-50 0]);

        cb = colorbar; title(cb, 'dB');
        xlabel('Frequencia (Hz)', 'FontSize', 11, 'FontWeight', 'bold');
        ylabel('Tempo (s)', 'FontSize', 11, 'FontWeight', 'bold');
        title(['3. Spectroid: ' nome_limpo], 'Interpreter', 'none', 'FontSize', 12);
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
janela_zoom = round(0.005 * Fs);
idx_zoom = meio : min(meio+janela_zoom, length(sinal));
plot(t_full(idx_zoom), sinal(idx_zoom), 'o-', 'MarkerSize', 3, 'Color', [0.85 0.32 0.09]);
axis tight; grid on; title('4. Zoom Onda (5ms)');
configurar_figura(gcf);

% =========================================================================
% SALVAR (MODIFICADO PARA ORGANIZAÇÃO AUTOMÁTICA)
% =========================================================================

% 1. Define o nome da pasta usando o nome do arquivo carregado
% Adicionamos o prefixo "RESULTADOS_" para evitar conflito se já existir arquivo com mesmo nome
pasta_saida = ['RESULTADOS_' nome_limpo];

if ~exist(pasta_saida, 'dir')
    mkdir(pasta_saida);
    fprintf('-> Pasta criada: %s\n', pasta_saida);
else
    fprintf('-> Usando pasta existente: %s\n', pasta_saida);
end

fprintf('-> Salvando imagens...\n');

figuras = [1, 2, 3, 4];
sufixos = {'TEMPO', 'PSD', 'SPECTROID', 'ZOOM'};

for i = 1:4
    try
        figure(figuras(i));
        drawnow;

        % 2. Constrói o nome do arquivo: "NomeDoAudio_Sufixo.png"
        nome_imagem = sprintf('%s_%s.png', nome_limpo, sufixos{i});
        caminho_final = fullfile(pasta_saida, nome_imagem);

        print(figuras(i), caminho_final, '-dpng', '-r150');
    catch err
        fprintf('Aviso: Erro ao salvar %s (%s)\n', sufixos{i}, err.message);
    end
end

fprintf('=================================================\n');
fprintf('CONCLUÍDO! Verifique a pasta: %s\n', pasta_saida);
fprintf('=================================================\n');
