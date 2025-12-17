% Salve este arquivo como: cwt_morlet_otimizada.m
function [coefs, t_out] = cwt_morlet_otimizada(sinal, fs, freqs)
  % Configuração de Otimização
  L = length(sinal);
  MAX_PIXELS = 3000; % Reduzi para 3000 para garantir compatibilidade com qualquer tela

  if L > MAX_PIXELS
      step = floor(L / MAX_PIXELS);
  else
      step = 1;
  end

  % Vetor de tempo reduzido (indices exatos)
  indices = 1:step:L;
  t_out = (indices - 1) / fs;

  % Prepara matriz
  coefs = zeros(length(freqs), length(indices));

  % Loop das frequências
  for i = 1:length(freqs)
    f = freqs(i);
    sigma = 6 / (2*pi*f);
    t_wav = -4*sigma : 1/fs : 4*sigma;

    % Wavelet
    wavelet = (pi^(-0.25)) * exp(1i * 2*pi*f * t_wav) .* exp(-t_wav.^2 / (2*sigma^2));
    wavelet = wavelet / sqrt(sum(abs(wavelet).^2));

    % Convolução
    resultado_completo = conv(sinal, conj(wavelet), 'same');

    % Salva apenas os pontos necessários
    coefs(i, :) = resultado_completo(indices);
  end
end
