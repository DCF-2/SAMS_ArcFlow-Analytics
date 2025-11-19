% Salve este arquivo como: minha_cwt_morlet.m
% Esta função calcula a Transformada Wavelet manualmente
function coefs = cwt_morlet(sinal, fs, freqs)
  % Prepara a matriz de saída (linhas = frequencias, colunas = tempo)
  coefs = zeros(length(freqs), length(sinal));

  % Para cada frequência que queremos analisar...
  for i = 1:length(freqs)
    f = freqs(i);

    % 1. Criar a "janela" da Wavelet para essa frequência
    % Quanto maior a frequência, mais estreita a janela (sigma menor)
    sigma = 6 / (2*pi*f);

    % Definir o tempo da wavelet (janela curta)
    % Cortamos em +/- 4 sigmas para pegar a parte relevante
    t_wav = -4*sigma : 1/fs : 4*sigma;

    % 2. A Fórmula da Wavelet de Morlet (Complexa)
    % É uma senoide complexa multiplicada por uma gaussiana (sino)
    wavelet = (pi^(-0.25)) * exp(1i * 2*pi*f * t_wav) .* exp(-t_wav.^2 / (2*sigma^2));

    % Normalizar energia para que todas as frequências tenham peso igual
    wavelet = wavelet / sqrt(sum(abs(wavelet).^2));

    % 3. Convolução: "Passar" a wavelet pelo sinal
    % A convolução compara a wavelet com o sinal em cada ponto
    % 'same' garante que o resultado tenha o mesmo tamanho do sinal original
    coefs(i, :) = conv(sinal, conj(wavelet), 'same');
  end
end
