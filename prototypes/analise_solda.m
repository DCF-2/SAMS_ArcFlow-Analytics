% --- Analisador de Soldagem v1.0 ---
pkg load signal;
clear; clc;

% 1. Carregar o Arquivo de Áudio
% TROQUE O NOME ABAIXO pelo nome do seu arquivo real
nome_arquivo = './Audios - PGD/freq1200.wav';

try
  [sinal, Fs] = audioread(nome_arquivo);
  fprintf('Arquivo "%s" carregado com sucesso!\n', nome_arquivo);
  fprintf('Taxa de Amostragem: %d Hz\n', Fs);
  fprintf('Duração: %.2f segundos\n', length(sinal)/Fs);
catch
  error('Erro: Não achei o arquivo. Verifique o nome ou coloque na mesma pasta!');
end

% 2. Garantir que é Mono (apenas 1 canal)
% Se o áudio for estéreo, pegamos só a esquerda
if size(sinal, 2) > 1
  sinal = sinal(:, 1);
end

% 3. Pegar apenas um trecho (para não travar o PC)
% Vamos pegar o primeiro 1 segundo de solda
segundos_analise = 1.0;
amostras_analise = min(length(sinal), round(segundos_analise * Fs));
sinal_cut = sinal(1:amostras_analise);
t = (0 : length(sinal_cut)-1) / Fs;

% --- ANÁLISE 1: FFT (A Receita) ---
figure(1);
Y = fft(sinal_cut);
N = length(sinal_cut);
P2 = abs(Y/N);
P1 = P2(1:N/2+1);
P1(2:end-1) = 2*P1(2:end-1);
f_eixo = Fs*(0:(N/2))/N;

plot(f_eixo, P1);
title(['Espectro FFT: ' nome_arquivo]);
xlabel('Frequencia (Hz)');
xlim([0 2000]); % Foco em baixas frequencias (onde a solda "canta")


% --- ANÁLISE 2: Wavelet (O Filme) ---
fprintf('Calculando Wavelet da solda... (pode demorar um pouco)\n');

% Vamos olhar de 50Hz até 3000Hz (onde está o som do arco elétrico)
freqs_wav = linspace(50, 3000, 100);
coefs = minha_cwt_morlet(sinal_cut, Fs, freqs_wav);

% Reduzir para visualizar (Evitar erro OpenGL)
passo = 50;
t_vis = t(1:passo:end);
c_vis = coefs(:, 1:passo:end);

figure(2);
imagesc(t_vis, freqs_wav, abs(c_vis));
axis xy; colormap(jet); colorbar;
title(['Wavelet: ' nome_arquivo]);
xlabel('Tempo (s)');
ylabel('Frequencia (Hz)');
