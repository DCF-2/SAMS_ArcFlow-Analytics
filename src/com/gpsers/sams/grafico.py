# =========================================================================
# GERADOR DE GRÁFICO — ESTILO DASHBOARD CORPORATIVO (Power BI like)
# =========================================================================
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.font_manager as fm
import numpy as np

# =========================================================================
# DADOS DO GRÁFICO (Resultados do Teste Gemini)
# =========================================================================
categorias = ['Curto-Circuito\n(1 de 9)', 'Globular\n(9 de 10)', 'Spray / Aerossol\n(8 de 9)']
taxas_acerto = [11.11, 90.00, 88.89]
media_geral = 64.29

# =========================================================================
# PALETA "DASHBOARD" (inspirada em Power BI / relatórios executivos)
# =========================================================================
COR_FUNDO       = '#F5F6FA'   # cinza muito claro (fundo da página)
COR_CARD        = '#FFFFFF'   # branco (fundo da área do gráfico)
COR_TEXTO       = '#1B1F3B'   # quase-preto azulado (títulos)
COR_TEXTO_SUAVE = '#6B7280'   # cinza médio (subtítulos/legendas)
COR_GRID        = '#E5E7EB'   # cinza claro (linhas de grade)
COR_ALERTA      = '#E63946'   # vermelho (baixo desempenho)
COR_SUCESSO     = '#2563EB'   # azul corporativo (bom desempenho)
COR_MEDIA       = '#0D9488'   # teal (linha de média)
cores_barras    = [COR_ALERTA, COR_SUCESSO, COR_SUCESSO]

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = COR_GRID

# =========================================================================
# FIGURA E LAYOUT (cabeçalho + KPIs + gráfico principal)
# =========================================================================
fig = plt.figure(figsize=(11, 7.5), dpi=300, facecolor=COR_FUNDO)

# Grade: linha 0 = KPIs (cards), linha 1 = gráfico principal
gs = fig.add_gridspec(2, 3, height_ratios=[1, 4.2], hspace=0.35, wspace=0.25,
                       left=0.06, right=0.96, top=0.86, bottom=0.10)

# -------------------------------------------------------------------------
# CABEÇALHO (título + subtítulo, estilo dashboard)
# -------------------------------------------------------------------------
fig.text(0.06, 0.965, 'Precisão de Classificação Visual por IA Generativa',
          fontsize=19, fontweight='bold', color=COR_TEXTO, ha='left')
fig.text(0.06, 0.925, 'Modelo avaliado: Gemini Flash (2.5 e 3.5)  •  Classificação de modos de transferência metálica em soldagem MIG/MAG',
          fontsize=10.5, color=COR_TEXTO_SUAVE, ha='left')

# -------------------------------------------------------------------------
# CARDS DE KPI (linha superior)
# -------------------------------------------------------------------------
kpi_info = [
    ("Curto-Circuito", "11,11%", "1 de 9 acertos", COR_ALERTA),
    ("Globular",       "90,00%", "9 de 10 acertos", COR_SUCESSO),
    ("Spray / Aerossol","88,89%", "8 de 9 acertos", COR_SUCESSO),
]

for i, (titulo, valor, detalhe, cor) in enumerate(kpi_info):
    ax_kpi = fig.add_subplot(gs[0, i])
    ax_kpi.set_xlim(0, 1); ax_kpi.set_ylim(0, 1)
    ax_kpi.axis('off')

    # Card com cantos arredondados
    card = FancyBboxPatch((0.02, 0.05), 0.96, 0.9,
                           boxstyle="round,pad=0.02,rounding_size=0.06",
                           linewidth=1, edgecolor=COR_GRID, facecolor=COR_CARD,
                           mutation_aspect=1)
    ax_kpi.add_patch(card)

    # Barra de destaque lateral (accent bar)
    accent = FancyBboxPatch((0.02, 0.05), 0.035, 0.9,
                             boxstyle="round,pad=0,rounding_size=0.02",
                             linewidth=0, facecolor=cor)
    ax_kpi.add_patch(accent)

    ax_kpi.text(0.14, 0.68, titulo, fontsize=11, color=COR_TEXTO_SUAVE,
                fontweight='bold', ha='left', va='center')
    ax_kpi.text(0.14, 0.38, valor, fontsize=22, color=COR_TEXTO,
                fontweight='bold', ha='left', va='center')
    ax_kpi.text(0.14, 0.16, detalhe, fontsize=9.5, color=COR_TEXTO_SUAVE,
                ha='left', va='center')

# -------------------------------------------------------------------------
# GRÁFICO PRINCIPAL (barras)
# -------------------------------------------------------------------------
ax = fig.add_subplot(gs[1, :])
ax.set_facecolor(COR_CARD)

# Grade horizontal suave, apenas no eixo Y
ax.yaxis.grid(True, color=COR_GRID, linewidth=1, zorder=0)
ax.set_axisbelow(True)

x_pos = np.arange(len(categorias))
largura = 0.45

barras = ax.bar(x_pos, taxas_acerto, width=largura, color=cores_barras,
                 edgecolor='white', linewidth=0, zorder=3)

# Efeito de "sombra" sutil por baixo das barras (leve profundidade)
ax.bar(x_pos, taxas_acerto, width=largura, color='black', alpha=0.06,
       zorder=2, bottom=0, align='center')

# Rótulos de valor no topo das barras
for barra, valor in zip(barras, taxas_acerto):
    ax.annotate(f'{valor:.2f}%'.replace('.', ','),
                xy=(barra.get_x() + barra.get_width() / 2, valor),
                xytext=(0, 8), textcoords="offset points",
                ha='center', va='bottom', fontsize=13, fontweight='bold',
                color=COR_TEXTO, zorder=4)

# Linha de média geral
ax.axhline(y=media_geral, color=COR_MEDIA, linestyle=(0, (6, 4)), linewidth=2, zorder=3)
ax.annotate(f'Média Geral: {media_geral:.2f}%'.replace('.', ','),
            xy=(len(categorias) - 0.5, media_geral),
            xytext=(8, 6), textcoords="offset points",
            fontsize=10.5, fontweight='bold', color=COR_MEDIA,
            ha='left', va='bottom')

# Eixos
ax.set_xticks(x_pos)
ax.set_xticklabels(categorias, fontsize=11.5, color=COR_TEXTO)
ax.set_ylim(0, 108)
ax.set_yticks(np.arange(0, 101, 20))
ax.set_yticklabels([f'{v}%' for v in np.arange(0, 101, 20)], fontsize=10, color=COR_TEXTO_SUAVE)
ax.set_ylabel('Taxa de Acerto', fontsize=11.5, fontweight='bold', color=COR_TEXTO, labelpad=12)

ax.tick_params(axis='x', length=0, pad=10)
ax.tick_params(axis='y', length=0)

# Remover bordas (estilo clean/flat de dashboard)
for spine in ['top', 'right', 'left']:
    ax.spines[spine].set_visible(False)
ax.spines['bottom'].set_color(COR_GRID)

# Legenda customizada (cores) no canto superior direito do gráfico
legenda_itens = [
    mpatches.Patch(color=COR_ALERTA, label='Desempenho crítico (< 50%)'),
    mpatches.Patch(color=COR_SUCESSO, label='Desempenho adequado (≥ 50%)'),
]
legend = ax.legend(handles=legenda_itens, loc='upper left', bbox_to_anchor=(0.0, 1.13),
                    ncol=2, fontsize=9.5, frameon=False, handlelength=1.2, handleheight=1.2)

# -------------------------------------------------------------------------
# RODAPÉ (fonte dos dados / nota)
# -------------------------------------------------------------------------
fig.text(0.06, 0.03,
         'Fonte: testes internos de classificação de imagens de transferência metálica (Gemini Flash) • n = 28 amostras',
         fontsize=8.5, color=COR_TEXTO_SUAVE, ha='left')

fig.patch.set_facecolor(COR_FUNDO)

# =========================================================================
# EXPORTAÇÃO
# =========================================================================
nome_arquivo = 'grafico_precisao_gemini_dashboard.png'
plt.savefig(nome_arquivo, dpi=300, facecolor=COR_FUNDO, bbox_inches='tight')
print(f"✅ Gráfico estilo dashboard gerado e guardado como: {nome_arquivo}")