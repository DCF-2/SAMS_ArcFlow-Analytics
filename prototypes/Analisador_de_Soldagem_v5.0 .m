% --- Analisador de Soldagem v5.0 (Com Legendas Técnicas) ---
pkg load signal;
clear; clc; close all;

% =========================================================================
% 1. CONFIGURAÇÃO DO EXPERIMENTO
% =========================================================================
% Coloque o caminho do seu arquivo aqui:
nome_arquivo = './Audios-PGD/PGD-INTM-AUDIOS/Ensaios-10.12/Ensaio-3/Ensaio-3.MP3';

% --- SELETOR DE LEGENDA (ESCOLHA O TIPO DE SOLDA) ---
% 1 = Solda Manual / Instável (Eletrodo Revestido ruim)
% 2 = MIG/MAG Estável (ASMR / Curto-Circuito Padrão)
% 3 = Alta Performance (Satisfying / Spray ou Alta Frequência)
% 0 = Genérico (Sem análise específica)
id_cenario = 1;

salvar_imagens = 1;

fprintf('=================================================\n');
fprintf('   ANALISADOR V5.0 - LEGENDAS TECNICAS\n');
fprintf('=================================================\n');

% ---------------------------------------------------------
% DEFINIÇÃO DAS LEGENDAS BASEADO NO CENÁRIO
% ---------------------------------------------------------
switch id_cenario
  case 1 % INSTÁVEL
    txt_tempo = "Diagnóstico: AMPLITUDE VARIÁVEL\nIndica instabilidade no arco ou\noscilação manual do soldador.";
    txt_fft   = "Diagnóstico: RUÍDO DE BANDA LARGA\nEnergia espalhada (caos acústico).\nFalta de harmônicos definidos.";
    txt_spec  = "Diagnóstico: TRANSITÓRIOS IRREGULARES\nFalhas na periodicidade dos curtos.\nInterrupções visíveis no arco.";
    cor_box   = [1 0.9 0.9]; % Fundo avermelhado

  case 2 % ESTÁVEL (MIG)
    txt_tempo = "Diagnóstico: AMPLITUDE CONSTANTE\nArco estável e contínuo.\nSem flutuações de energia.";
    txt_fft   = "Diagnóstico: PERFIL HARMÔNICO LIMPO\nEnergia concentrada em graves/médios.\nSom 'macio' e controlado.";
    txt_spec  = "Diagnóstico: PADRÃO RÍTMICO (BARRAS)\nPeriodicidade perfeita de transferência.\nEquilíbrio ideal Tensão x Velocidade.";
    cor_box   = [0.9 1 0.9]; % Fundo esverdeado

  case 3 % ALTA PERFORMANCE
    txt_tempo = "Diagnóstico: SATURAÇÃO DE EVENTOS\nDensidade máxima de sinal.\nArco elétrico potente e fixo.";
    txt_fft   = "Diagnóstico: ALTA RIQUEZA ESPECTRAL\nEnergia mantida >1.5kHz (Crocância).\nSom nítido e penetrante.";
    txt_spec  = "Diagnóstico: ALTA FREQUÊNCIA DE GOTAS\nLinhas verticais fundidas (Parede sólida).\nCiclo de curto-circuito rapidíssimo.";
    cor_box   = [0.9 0.9 1]; % Fundo azulado

  otherwise % GENÉRICO
    txt_tempo = "Visualização de Amplitude";
    txt_fft   = "Distribuição de Frequências";
    txt_spec  = "Mapa Tempo-Frequência";
    cor_box   = [1 1 1]; % Branco
end

% ---------------------------------------------------------
% PROCESSAMENTO (Igual v4.1)
% ---------------------------------------------------------
[~, nome_limpo, ~] = fileparts(nome_arquivo);

try
  [sinal_raw, Fs_raw] = audioread(nome_arquivo);
  fprintf('-> Arquivo: %s (Cenário %d)\n', nome_limpo, id_cenario);
catch
  error('Arquivo nao encontrado! Verifique o caminho.');
end

if size(sinal_raw, 2) > 1, sinal_raw = sinal_raw(:, 1); end
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
title(['1. Domínio do Tempo: ' nome_limpo], 'Interpreter', 'none', 'FontSize', 14);
xlabel('Tempo (s)'); ylabel('Amplitude'); grid on; axis tight;

% ADICIONAR LEGENDA (Caixa de Texto)
% Posição 0.02 (esquerda), 0.85 (topo) relativa ao gráfico
text(0.02, 0.85, txt_tempo, 'Units', 'normalized', ...
     'BackgroundColor', cor_box, 'EdgeColor', 'k', 'LineWidth', 1, ...
     'FontSize', 10, 'FontWeight', 'bold');

% =========================================================================
% GRAFICO 2: FFT (LOGARITMICA)
% =========================================================================
figure(2); set(gcf, 'Position', [50, 300, 600, 400]);
N = length(sinal);
Y = fft(sinal);
P2 = abs(Y/N);
P1 = P2(1:floor(N/2)+1); P1(2:end-1) = 2*P1(2:end-1);
f_eixo = Fs*(0:(floor(N/2)))/N;

semilogy(f_eixo, P1, 'LineWidth', 1.0, 'Color', [0.85 0.32 0.098]);
title('2. FFT (Espectro)', 'FontSize', 14);
xlabel('Frequencia (Hz)'); ylabel('Mag (Log)'); grid on; xlim([0 4000]);

% LEGENDA FFT
text(0.50, 0.85, txt_fft, 'Units', 'normalized', ...
     'BackgroundColor', cor_box, 'EdgeColor', 'k', 'LineWidth', 1, ...
     'FontSize', 10);

% =========================================================================
% GRAFICO 3: ESPECTROGRAMA
% =========================================================================
figure(3); set(gcf, 'Position', [50, 50, 1000, 400]);
janela = 512; step = 128;
[S, f, t_spec] = specgram(sinal, 2*janela, Fs, hanning(janela), janela-step);
imagesc(t_spec, f, 20*log10(abs(S)+1e-6));
axis xy; colormap(jet); colorbar;
title(['3. Espectrograma: ' nome_limpo], 'Interpreter', 'none', 'FontSize', 14);
xlabel('Tempo (s)'); ylabel('Frequencia (Hz)'); ylim([0 4000]);

% LEGENDA ESPECTROGRAMA
text(0.02, 0.90, txt_spec, 'Units', 'normalized', ...
     'BackgroundColor', 'white', 'EdgeColor', 'k', 'LineWidth', 2, ...
     'FontSize', 11, 'FontWeight', 'bold', 'Color', 'black');

% =========================================================================
% SALVAR
% =========================================================================
if salvar_imagens
  pasta = 'Grafico-PGD-Legendado';
  if ~exist(pasta, 'dir'), mkdir(pasta); end

  print(1, fullfile(pasta, [nome_limpo '_TEMPO_LEG.png']), '-dpng');
  print(2, fullfile(pasta, [nome_limpo '_FFT_LEG.png']), '-dpng');
  print(3, fullfile(pasta, [nome_limpo '_ESPECTRO_LEG.png']), '-dpng');
  fprintf('Imagens com legendas salvas em: %s/\n', pasta);
end
