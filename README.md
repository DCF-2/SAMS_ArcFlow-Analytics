# PGD - Projeto Gêmeos Digitais - INTM


**Desenvolvido por:** DEXTER GPSERS - Soluções Inteligentes & Davi Freitas

---

## 📖 Sobre o Projeto
O **PGD (Projeto Gêmeos Digitais)** visa criar uma representação virtual fidedigna dos processos de soldagem industrial. Este repositório (`PDG-Projeto_Gemio_Digital-INTM`) contém o núcleo de engenharia, algoritmos de processamento de sinais, códigos embarcados e protótipos de software.

O foco atual é o monitoramento acústico e a classificação de modos de transferência (Curto-Circuito, Spray, etc.) utilizando técnicas avançadas de DSP (Digital Signal Processing).

---

## 📂 Estrutura do Repositório

```text
soldagem-core/
│
├── prototypes/           # Scripts de Estudo e Validação (Octave)
│   ├── 01_fft_estudos/   # Testes iniciais com FFT e sinais tonais
│   ├── 02_wavelet_lib/   # Biblioteca manual de Wavelet (CWT Morlet)
│   └── 03_analisador_pro/# Ferramenta final de análise automatizada
│
├── hardware/             # Projetos de Hardware e Firmware (Em Breve)
│   └── arduino/          # Códigos de aquisição de sensores
│
└── src/                  # Aplicação Principal (Em Breve - Python/Java)

```

# 🚀 Estado Atual do Desenvolvimento (Fase 1)

Atualmente, finalizamos o módulo de **Processamento Digital de Sinais (PDS)** no GNU Octave. As seguintes ferramentas foram desenvolvidas e validadas:

---

## 1. Algoritmo de Wavelet Manual

Devido a limitações em bibliotecas legadas, desenvolvemos um algoritmo próprio de **Transformada Wavelet Contínua (CWT)** utilizando a **Wavelet de Morlet**.

**Capacidade:** Identificação precisa de eventos transientes (curtos-circuitos) no domínio do tempo.

**Validação:** Testado com sinais não-estacionários (variação de frequência temporal).

---

## 2. Analisador de Soldagem Pro (v3.0)

Script robusto para processamento em lote de arquivos de áudio de soldagem.

- **Otimização:** Realiza *downsampling* automático (redução de taxa de amostragem) para processar arquivos longos sem travar a memória.  
- **Compressão Visual:** Algoritmo de renderização dinâmica para evitar erros de GPU (OpenGL).  
- **Saída:** Gera automaticamente **3 relatórios gráficos por amostra**:

  - 📉 Oscilograma (Amplitude x Tempo)  
  - 📊 Espectro FFT (Assinatura de Frequência)  
  - 🔥 Scalograma Wavelet (Mapa de Calor Tempo-Frequência)

---

# 🛠️ Como Utilizar os Scripts (Protótipos)

## Pré-requisitos

- GNU Octave (v6.0 ou superior)  
- Pacote `signal` (`pkg load signal`)

## Executando a Análise

1. Navegue até a pasta `prototypes/03_analisador_pro/`.
2. Coloque seus arquivos de áudio `.wav` na mesma pasta.
3. Abra o arquivo `analise_solda_pro.m`.
4. Edite a variável `nome_arquivo` com o nome do seu áudio.
5. Execute o script.  
   As imagens de resultado serão salvas automaticamente na pasta.

---

# 🔗 Documentação Completa

Para acessar o manual do usuário, teoria detalhada e resultados visuais, acesse nosso Portal de Documentação:

**[Link para o Site de Documentação - Em Breve]**

---

© **2025 DEXTER GPSERS & Davi Freitas.** Todos os direitos reservados.
