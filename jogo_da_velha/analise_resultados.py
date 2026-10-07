"""
analise_resultados.py
Analisa resultados do jogo da velha, gera gráficos e recortes.
Extrai os nomes dos agentes do nome do arquivo e organiza a saída
em uma pasta própria dentro de 'resultados/'.
"""

import os
import csv
from typing import List, Dict, Tuple, Optional
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ================================================================
# CONFIGURAÇÕES
# ================================================================

PASTA_SAIDA_BASE = "resultados"
EXPORTAR_CSV = True
GERAR_GRAFICO_INTELIGENTE = True

# ================================================================
# Constantes do jogo
# ================================================================

X = 1
O = -1
VAZIO = 0


# ================================================================
# Utilidades de arquivo/pasta
# ================================================================

def extrair_agentes_do_nome(caminho_arquivo: str) -> Tuple[str, str]:
    """
    A partir de 'resultado_ingenuo_vs_inteligente.txt', retorna
    ('ingenuo', 'inteligente').

    Se o padrão não for reconhecido, retorna ('j1', 'j2').
    """
    nome = os.path.basename(caminho_arquivo)
    nome_sem_ext = os.path.splitext(nome)[0]

    if nome_sem_ext.startswith("resultado_"):
        corpo = nome_sem_ext[len("resultado_"):]
    else:
        corpo = nome_sem_ext

    if "_vs_" in corpo:
        agente_x, agente_o = corpo.split("_vs_", 1)
        return agente_x, agente_o

    return "j1", "j2"


def preparar_pasta_saida(caminho_arquivo: str) -> str:
    """
    Cria uma pasta dentro de PASTA_SAIDA_BASE com o nome base do arquivo.
    Retorna o caminho da pasta.
    """
    nome_base = os.path.splitext(os.path.basename(caminho_arquivo))[0]
    pasta = os.path.join(PASTA_SAIDA_BASE, nome_base)
    os.makedirs(pasta, exist_ok=True)
    return pasta


# ================================================================
# Leitura de resultados
# ================================================================

def ler_arquivo_resultados(nome_arquivo: str) -> List[Dict]:
    if not os.path.exists(nome_arquivo):
        print(f"❌ Arquivo '{nome_arquivo}' não encontrado!")
        return []

    dados = []
    linhas_ignoradas = 0

    with open(nome_arquivo, 'r', encoding='utf-8') as f:
        linhas = f.readlines()

        if not linhas:
            print("❌ Arquivo vazio!")
            return []

        for linha in linhas[1:]:
            linha = linha.strip()
            if not linha:
                continue

            partes = linha.split('\t')

            if len(partes) >= 14:
                try:
                    registro = {
                        'partida': int(partes[0]),
                        'vitoria_x': int(partes[1]),
                        'vitoria_o': int(partes[2]),
                        'empate': int(partes[3]),
                        'num_jogadas': int(partes[4]),
                        'posicoes': [int(p) for p in partes[5:14]]
                    }
                    dados.append(registro)
                except (ValueError, IndexError):
                    linhas_ignoradas += 1
            else:
                linhas_ignoradas += 1

    if linhas_ignoradas > 0:
        print(f"ℹ️  {linhas_ignoradas} linhas foram ignoradas.")

    return dados


# ================================================================
# Análise geral
# ================================================================

def analisar_resultados(dados: List[Dict]) -> Dict:
    if not dados:
        return {}

    total = len(dados)

    vitorias_x = sum(1 for d in dados if d['vitoria_x'] == 1)
    vitorias_o = sum(1 for d in dados if d['vitoria_o'] == 1)
    empates = sum(1 for d in dados if d['empate'] == 1)

    jogadas = [d['num_jogadas'] for d in dados]
    jogadas_por_resultado = {
        'X': [d['num_jogadas'] for d in dados if d['vitoria_x'] == 1],
        'O': [d['num_jogadas'] for d in dados if d['vitoria_o'] == 1],
        'Empate': [d['num_jogadas'] for d in dados if d['empate'] == 1]
    }

    posicoes_finais = [0] * 9
    posicoes_por_jogador = {'X': [0] * 9, 'O': [0] * 9, 'VAZIO': [0] * 9}

    for d in dados:
        for i, val in enumerate(d['posicoes']):
            if val == X:
                posicoes_finais[i] += 1
                posicoes_por_jogador['X'][i] += 1
            elif val == O:
                posicoes_por_jogador['O'][i] += 1
            else:
                posicoes_por_jogador['VAZIO'][i] += 1

    vitorias_por_tipo = {'linha': 0, 'coluna': 0, 'diagonal': 0}
    sequencias_vitoria = Counter()

    for d in dados:
        if d['vitoria_x'] == 1 or d['vitoria_o'] == 1:
            pos = d['posicoes']
            combinacoes = [
                ((0,1,2), 'linha'), ((3,4,5), 'linha'), ((6,7,8), 'linha'),
                ((0,3,6), 'coluna'), ((1,4,7), 'coluna'), ((2,5,8), 'coluna'),
                ((0,4,8), 'diagonal'), ((2,4,6), 'diagonal')
            ]
            for (a,b,c), tipo in combinacoes:
                soma = pos[a] + pos[b] + pos[c]
                if soma == 3 or soma == -3:
                    vitorias_por_tipo[tipo] += 1
                    sequencias_vitoria[f"({a},{b},{c})"] += 1
                    break

    return {
        'total': total,
        'vitorias_x': vitorias_x,
        'vitorias_o': vitorias_o,
        'empates': empates,
        'porcentagem_x': (vitorias_x / total) * 100 if total > 0 else 0,
        'porcentagem_o': (vitorias_o / total) * 100 if total > 0 else 0,
        'porcentagem_empate': (empates / total) * 100 if total > 0 else 0,
        'media_jogadas': sum(jogadas) / len(jogadas) if jogadas else 0,
        'min_jogadas': min(jogadas) if jogadas else 0,
        'max_jogadas': max(jogadas) if jogadas else 0,
        'jogadas_por_resultado': jogadas_por_resultado,
        'posicoes_finais': posicoes_finais,
        'posicoes_por_jogador': posicoes_por_jogador,
        'vitorias_por_tipo': vitorias_por_tipo,
        'sequencias_vitoria': sequencias_vitoria
    }


# ================================================================
# Recortes
# ================================================================

def _calcular_taxas_bloco(dados: List[Dict]) -> Dict:
    n = len(dados)
    if n == 0:
        return {
            'n': 0, 'vx': 0, 'vo': 0, 'emp': 0,
            'pct_vx': 0.0, 'pct_vo': 0.0, 'pct_emp': 0.0,
            'pct_nao_derrota_x': 0.0, 'pct_nao_derrota_o': 0.0,
        }
    vx = sum(1 for d in dados if d['vitoria_x'] == 1)
    vo = sum(1 for d in dados if d['vitoria_o'] == 1)
    emp = sum(1 for d in dados if d['empate'] == 1)
    pct_vx = vx / n * 100
    pct_vo = vo / n * 100
    pct_emp = emp / n * 100
    return {
        'n': n, 'vx': vx, 'vo': vo, 'emp': emp,
        'pct_vx': pct_vx,
        'pct_vo': pct_vo,
        'pct_emp': pct_emp,
        'pct_nao_derrota_x': pct_vx + pct_emp,
        'pct_nao_derrota_o': pct_vo + pct_emp,
    }


def _gerar_cortes_para_total(total: int) -> List[int]:
    if total <= 1_000:
        base = [100, 250, 500, 1000]
    elif total <= 10_000:
        base = [100, 500, 1_000, 2_500, 5_000, 10_000]
    elif total <= 100_000:
        base = [100, 500, 1_000, 5_000, 10_000, 25_000, 50_000, 100_000]
    elif total <= 1_000_000:
        base = [100, 500, 1_000, 5_000, 10_000, 25_000, 50_000,
                100_000, 250_000, 500_000, 1_000_000]
    else:
        base = [100, 1_000, 10_000, 100_000, 250_000, 500_000,
                1_000_000, 2_500_000, 5_000_000, 10_000_000,
                total // 2, total]
    cortes = sorted(set(c for c in base if 0 < c <= total))
    if total not in cortes:
        cortes.append(total)
    return cortes


def _calcular_recortes(dados: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Retorna (recortes_acumulados, recortes_janelas), cada um uma lista de dicts
    com os dados de cada corte.
    """
    total = len(dados)
    cortes = _gerar_cortes_para_total(total)

    acumulados = []
    for corte in cortes:
        bloco = dados[:corte]
        taxas = _calcular_taxas_bloco(bloco)
        taxas['rotulo'] = str(corte)
        taxas['corte'] = corte
        taxas['inicio'] = 0
        acumulados.append(taxas)

    janelas = []
    anterior = 0
    for corte in cortes:
        bloco = dados[anterior:corte]
        taxas = _calcular_taxas_bloco(bloco)
        taxas['rotulo'] = f"{anterior}-{corte}"
        taxas['corte'] = corte
        taxas['inicio'] = anterior
        janelas.append(taxas)
        anterior = corte

    return acumulados, janelas


# ================================================================
# Utilidades de formatação
# ================================================================

def _abreviar_numero(n: int) -> str:
    """Abrevia números grandes para rótulos curtos. Ex: 1000 → '1k'."""
    if n >= 1_000_000:
        return f"{n // 1_000_000}M"
    if n >= 1_000:
        return f"{n // 1_000}k"
    return str(n)


def _formatar_rotulo_janela(janela: Dict) -> str:
    """Retorna um rótulo curto tipo '0-5k' ou '5k-10k' para o eixo X."""
    return f"{_abreviar_numero(janela['inicio'])}-{_abreviar_numero(janela['corte'])}"


def _anotar_pontos(ax, posicoes, valores, cor):
    """Anota o valor numérico acima de cada ponto."""
    for i, v in enumerate(valores):
        ax.annotate(
            f"{v:.1f}",
            xy=(posicoes[i], v),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            color=cor,
        )


# ================================================================
# Gráficos gerais (série temporal contínua)
# ================================================================

def _plot_taxas_acumuladas(dados, passo, arquivo_saida):
    n = len(dados)
    eixo_x, pct_j1, pct_j2, pct_emp = [], [], [], []
    total_j1 = total_j2 = total_emp = 0
    for i, d in enumerate(dados, start=1):
        total_j1 += d['vitoria_x']
        total_j2 += d['vitoria_o']
        total_emp += d['empate']
        if i % passo == 0 or i == n:
            eixo_x.append(i)
            pct_j1.append(total_j1 / i * 100)
            pct_j2.append(total_j2 / i * 100)
            pct_emp.append(total_emp / i * 100)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(eixo_x, pct_j1, label="Vitórias J1 (X) %", color="#1f77b4", linewidth=1.8)
    ax.plot(eixo_x, pct_j2, label="Vitórias J2 (O) %", color="#d62728", linewidth=1.8)
    ax.plot(eixo_x, pct_emp, label="Empates %", color="#2ca02c", linewidth=1.8)
    ax.set_xlabel("Número da partida")
    ax.set_ylabel("Taxa acumulada (%)")
    ax.set_title("Taxas acumuladas desde o início")
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_ylim(-2, 102)
    plt.tight_layout()
    plt.savefig(arquivo_saida, dpi=120)
    plt.close(fig)
    print(f"📊 {arquivo_saida}")


def _plot_acumulado_absoluto(dados, passo, arquivo_saida):
    n = len(dados)
    eixo_x, acum_j1, acum_j2, acum_emp = [], [], [], []
    total_j1 = total_j2 = total_emp = 0
    for i, d in enumerate(dados, start=1):
        total_j1 += d['vitoria_x']
        total_j2 += d['vitoria_o']
        total_emp += d['empate']
        if i % passo == 0 or i == n:
            eixo_x.append(i)
            acum_j1.append(total_j1)
            acum_j2.append(total_j2)
            acum_emp.append(total_emp)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(eixo_x, acum_j1, label="Vitórias J1 (X) acumuladas", color="#1f77b4", linewidth=1.8)
    ax.plot(eixo_x, acum_j2, label="Vitórias J2 (O) acumuladas", color="#d62728", linewidth=1.8)
    ax.plot(eixo_x, acum_emp, label="Empates acumulados", color="#2ca02c", linewidth=1.8)
    ax.set_xlabel("Número da partida")
    ax.set_ylabel("Contagem acumulada (absoluta)")
    ax.set_title("Acumulado absoluto desde o início")
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.savefig(arquivo_saida, dpi=120)
    plt.close(fig)
    print(f"📊 {arquivo_saida}")


def _plot_grafico_inteligente(dados, passo, nome_inteligente, eh_segundo,
                              arquivo_saida):
    """
    Plota a taxa de 'não-derrota' do inteligente, mais a taxa de vitória
    dele e a taxa de empate, tudo acumulado desde o início.
    """
    n = len(dados)
    eixo_x = []
    taxa_nao_derrota = []
    taxa_vitoria = []
    taxa_empate = []

    total_v_int = 0
    total_emp = 0

    for i, d in enumerate(dados, start=1):
        if eh_segundo:
            total_v_int += d['vitoria_o']
        else:
            total_v_int += d['vitoria_x']
        total_emp += d['empate']

        if i % passo == 0 or i == n:
            eixo_x.append(i)
            taxa_vitoria.append(total_v_int / i * 100)
            taxa_empate.append(total_emp / i * 100)
            taxa_nao_derrota.append((total_v_int + total_emp) / i * 100)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(eixo_x, taxa_nao_derrota, label="Não-derrota do inteligente",
            color="#2ca02c", linewidth=2.0)
    ax.plot(eixo_x, taxa_vitoria, label="Vitória do inteligente",
            color="#1f77b4", linewidth=1.3, linestyle="--")
    ax.plot(eixo_x, taxa_empate, label="Empate",
            color="#ff7f0e", linewidth=1.3, linestyle=":")
    ax.set_xlabel("Número da partida")
    ax.set_ylabel("Taxa acumulada (%)")
    ax.set_title(f"Desempenho do '{nome_inteligente}'")
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_ylim(-2, 102)
    plt.tight_layout()
    plt.savefig(arquivo_saida, dpi=120)
    plt.close(fig)
    print(f"📊 {arquivo_saida}")


# ================================================================
# Gráficos de recorte por JANELA (rótulos + anotações)
# ================================================================

def _plot_recortes_janela_taxas(janelas: List[Dict], nome_x: str, nome_o: str,
                                arquivo_saida: str):
    """
    Taxas por janela — VitX%, VitO%, Emp%.
    Eixo X rotulado com o nome da janela (0-5k, 5k-10k, ...).
    """
    if not janelas:
        return

    rotulos = [_formatar_rotulo_janela(j) for j in janelas]
    posicoes = list(range(len(janelas)))

    fig, ax = plt.subplots(figsize=(12, 6))

    v_vx = [j['pct_vx'] for j in janelas]
    v_vo = [j['pct_vo'] for j in janelas]
    v_emp = [j['pct_emp'] for j in janelas]

    ax.plot(posicoes, v_vx, label=f"Vitórias {nome_x} (X)",
            color="#1f77b4", linewidth=1.8, marker="o", markersize=5)
    ax.plot(posicoes, v_vo, label=f"Vitórias {nome_o} (O)",
            color="#d62728", linewidth=1.8, marker="o", markersize=5)
    ax.plot(posicoes, v_emp, label="Empates",
            color="#2ca02c", linewidth=1.8, marker="o", markersize=5)

    _anotar_pontos(ax, posicoes, v_vx, "#1f77b4")
    _anotar_pontos(ax, posicoes, v_vo, "#d62728")
    _anotar_pontos(ax, posicoes, v_emp, "#2ca02c")

    ax.set_xticks(posicoes)
    ax.set_xticklabels(rotulos, rotation=45, ha="right")
    ax.set_xlabel("Janela (partidas)")
    ax.set_ylabel("Taxa na janela (%)")
    ax.set_title(f"Taxas por janela — {nome_x} (X) vs {nome_o} (O)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    ax.set_ylim(-2, 105)

    plt.tight_layout()
    plt.savefig(arquivo_saida, dpi=120)
    plt.close(fig)
    print(f"📊 {arquivo_saida}")


def _plot_recortes_janela_nao_derrota(janelas: List[Dict], nome_x: str, nome_o: str,
                                      arquivo_saida: str):
    """
    Não-derrota por janela — NãoDerrota X%, NãoDerrota O%.
    """
    if not janelas:
        return

    rotulos = [_formatar_rotulo_janela(j) for j in janelas]
    posicoes = list(range(len(janelas)))

    fig, ax = plt.subplots(figsize=(12, 6))

    v_ndx = [j['pct_nao_derrota_x'] for j in janelas]
    v_ndo = [j['pct_nao_derrota_o'] for j in janelas]

    ax.plot(posicoes, v_ndx, label=f"Não-derrota {nome_x} (X)",
            color="#1f77b4", linewidth=1.8, marker="o", markersize=5)
    ax.plot(posicoes, v_ndo, label=f"Não-derrota {nome_o} (O)",
            color="#d62728", linewidth=1.8, marker="o", markersize=5)

    _anotar_pontos(ax, posicoes, v_ndx, "#1f77b4")
    _anotar_pontos(ax, posicoes, v_ndo, "#d62728")

    ax.set_xticks(posicoes)
    ax.set_xticklabels(rotulos, rotation=45, ha="right")
    ax.set_xlabel("Janela (partidas)")
    ax.set_ylabel("Não-derrota na janela (%)")
    ax.set_title(f"Não-derrota por janela — {nome_x} (X) vs {nome_o} (O)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    ax.set_ylim(-2, 105)

    plt.tight_layout()
    plt.savefig(arquivo_saida, dpi=120)
    plt.close(fig)
    print(f"📊 {arquivo_saida}")


# ================================================================
# Gráficos de recorte por ACUMULADO (até o corte)
# ================================================================

def _plot_recortes_acumulado_taxas(acumulados: List[Dict], nome_x: str,
                                   nome_o: str, arquivo_saida: str):
    """
    Taxas acumuladas até cada corte.
    Eixo X = número absoluto da partida (corte).
    """
    if not acumulados:
        return

    eixo_x = [r['corte'] for r in acumulados]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(eixo_x, [r['pct_vx'] for r in acumulados],
            label=f"Vitórias {nome_x} (X)", color="#1f77b4",
            linewidth=1.8, marker="o", markersize=4)
    ax.plot(eixo_x, [r['pct_vo'] for r in acumulados],
            label=f"Vitórias {nome_o} (O)", color="#d62728",
            linewidth=1.8, marker="o", markersize=4)
    ax.plot(eixo_x, [r['pct_emp'] for r in acumulados],
            label="Empates", color="#2ca02c",
            linewidth=1.8, marker="o", markersize=4)
    ax.set_xlabel("Partidas acumuladas (corte)")
    ax.set_ylabel("Taxa acumulada (%)")
    ax.set_title(f"Taxas acumuladas por corte — {nome_x} (X) vs {nome_o} (O)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    ax.set_ylim(-2, 105)
    plt.tight_layout()
    plt.savefig(arquivo_saida, dpi=120)
    plt.close(fig)
    print(f"📊 {arquivo_saida}")


def _plot_recortes_acumulado_nao_derrota(acumulados: List[Dict], nome_x: str,
                                         nome_o: str, arquivo_saida: str):
    """
    Não-derrota acumulada até cada corte.
    """
    if not acumulados:
        return

    eixo_x = [r['corte'] for r in acumulados]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(eixo_x, [r['pct_nao_derrota_x'] for r in acumulados],
            label=f"Não-derrota {nome_x} (X)", color="#1f77b4",
            linewidth=1.8, marker="o", markersize=4)
    ax.plot(eixo_x, [r['pct_nao_derrota_o'] for r in acumulados],
            label=f"Não-derrota {nome_o} (O)", color="#d62728",
            linewidth=1.8, marker="o", markersize=4)
    ax.set_xlabel("Partidas acumuladas (corte)")
    ax.set_ylabel("Não-derrota acumulada (%)")
    ax.set_title(f"Não-derrota acumulada por corte — {nome_x} (X) vs {nome_o} (O)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    ax.set_ylim(-2, 105)
    plt.tight_layout()
    plt.savefig(arquivo_saida, dpi=120)
    plt.close(fig)
    print(f"📊 {arquivo_saida}")


# ================================================================
# Agregador de gráficos de recorte
# ================================================================

def gerar_graficos_recortes(recortes_acumulados: List[Dict],
                            recortes_janelas: List[Dict],
                            nome_x: str, nome_o: str,
                            pasta: str):
    """
    Gera quatro gráficos de recorte independentes:
      1. recortes_taxas_janela.png            — taxas por janela (com rótulos)
      2. recortes_nao_derrota_janela.png      — não-derrota por janela
      3. recortes_taxas_acumulado.png         — taxas acumuladas por corte
      4. recortes_nao_derrota_acumulado.png   — não-derrota acumulada por corte
    """
    _plot_recortes_janela_taxas(
        recortes_janelas, nome_x, nome_o,
        os.path.join(pasta, "recortes_taxas_janela.png")
    )
    _plot_recortes_janela_nao_derrota(
        recortes_janelas, nome_x, nome_o,
        os.path.join(pasta, "recortes_nao_derrota_janela.png")
    )
    _plot_recortes_acumulado_taxas(
        recortes_acumulados, nome_x, nome_o,
        os.path.join(pasta, "recortes_taxas_acumulado.png")
    )
    _plot_recortes_acumulado_nao_derrota(
        recortes_acumulados, nome_x, nome_o,
        os.path.join(pasta, "recortes_nao_derrota_acumulado.png")
    )


# ================================================================
# CSV / TXT
# ================================================================

def exportar_recortes_csv(recortes: List[Dict], nome_arquivo: str, tipo: str):
    """
    Exporta uma lista de recortes (acumulados ou janelas) para CSV.
    """
    if not recortes:
        return
    with open(nome_arquivo, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        if tipo == "acumulado":
            writer.writerow(["Corte", "N", "VitX%", "VitO%", "Emp%",
                             "NaoDerrotaX%", "NaoDerrotaO%",
                             "VitX", "VitO", "Empates"])
        else:
            writer.writerow(["Janela", "N", "VitX%", "VitO%", "Emp%",
                             "NaoDerrotaX%", "NaoDerrotaO%",
                             "VitX", "VitO", "Empates"])
        for r in recortes:
            writer.writerow([
                r['rotulo'], r['n'],
                f"{r['pct_vx']:.2f}", f"{r['pct_vo']:.2f}", f"{r['pct_emp']:.2f}",
                f"{r['pct_nao_derrota_x']:.2f}", f"{r['pct_nao_derrota_o']:.2f}",
                r['vx'], r['vo'], r['emp']
            ])
    print(f"📁 {nome_arquivo}")


def exportar_recortes_txt(recortes_acumulados: List[Dict],
                          recortes_janelas: List[Dict],
                          nome_x: str, nome_o: str,
                          arquivo_saida: str):
    """
    Gera um TXT formatado com as duas tabelas de recorte
    (acumulado e janela) para leitura humana direta.
    """
    if not recortes_acumulados or not recortes_janelas:
        return

    # Larguras fixas para alinhar as colunas
    LARG_REC = 22
    LARG_N = 8
    LARG_PCT = 8
    LARG_ND = 11

    def _linha_separadora():
        return (
            "-" * LARG_REC + "-+-" +
            "-" * LARG_N + "-+-" +
            "-" * LARG_PCT + "-+-" +
            "-" * LARG_PCT + "-+-" +
            "-" * LARG_PCT + "-+-" +
            "-" * LARG_ND + "-+-" +
            "-" * LARG_ND
        )

    def _cabecalho_tabela(rotulo_col1: str):
        return (
            f"{rotulo_col1:>{LARG_REC}} | "
            f"{'N':>{LARG_N}} | "
            f"{'VitX%':>{LARG_PCT}} | "
            f"{'VitO%':>{LARG_PCT}} | "
            f"{'Emp%':>{LARG_PCT}} | "
            f"{'NDerX%':>{LARG_ND}} | "
            f"{'NDerO%':>{LARG_ND}}"
        )

    def _linha_tabela(r: Dict):
        return (
            f"{r['rotulo']:>{LARG_REC}} | "
            f"{r['n']:>{LARG_N}} | "
            f"{r['pct_vx']:>{LARG_PCT}.2f} | "
            f"{r['pct_vo']:>{LARG_PCT}.2f} | "
            f"{r['pct_emp']:>{LARG_PCT}.2f} | "
            f"{r['pct_nao_derrota_x']:>{LARG_ND}.2f} | "
            f"{r['pct_nao_derrota_o']:>{LARG_ND}.2f}"
        )

    linhas = []
    linhas.append("=" * (LARG_REC + LARG_N + LARG_PCT * 3 + LARG_ND * 2 + 3 * 6))
    linhas.append(f"  RECORTES — {nome_x} (X) vs {nome_o} (O)")
    linhas.append("=" * (LARG_REC + LARG_N + LARG_PCT * 3 + LARG_ND * 2 + 3 * 6))
    linhas.append("")
    linhas.append("Legenda:")
    linhas.append("  VitX%   = % de vitórias do jogador X")
    linhas.append("  VitO%   = % de vitórias do jogador O")
    linhas.append("  Emp%    = % de empates")
    linhas.append("  NDerX%  = Não-derrota de X (VitX% + Emp%)")
    linhas.append("  NDerO%  = Não-derrota de O (VitO% + Emp%)")
    linhas.append("")
    linhas.append("")

    # ---- Tabela 1: acumulado ----
    linhas.append("TABELA 1 — ACUMULADO (do início até o corte)")
    linhas.append("")
    linhas.append(_cabecalho_tabela("Corte"))
    linhas.append(_linha_separadora())
    for r in recortes_acumulados:
        linhas.append(_linha_tabela(r))
    linhas.append("")
    linhas.append("")

    # ---- Tabela 2: janelas ----
    linhas.append("TABELA 2 — JANELAS (cada trecho isolado)")
    linhas.append("")
    linhas.append(_cabecalho_tabela("Janela"))
    linhas.append(_linha_separadora())
    for r in recortes_janelas:
        linhas.append(_linha_tabela(r))
    linhas.append("")

    with open(arquivo_saida, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))

    print(f"📁 {arquivo_saida}")


def exportar_resumo_txt(estatisticas: Dict, nome_x: str, nome_o: str,
                        nome_arquivo: str):
    """
    Salva um resumo em texto puro, mais legível que o CSV.
    """
    if not estatisticas:
        return
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write(f"Resumo: {nome_x} (X) vs {nome_o} (O)\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total de partidas: {estatisticas['total']}\n")
        f.write(f"Vitórias de {nome_x} (X): {estatisticas['vitorias_x']} "
                f"({estatisticas['porcentagem_x']:.2f}%)\n")
        f.write(f"Vitórias de {nome_o} (O): {estatisticas['vitorias_o']} "
                f"({estatisticas['porcentagem_o']:.2f}%)\n")
        f.write(f"Empates: {estatisticas['empates']} "
                f"({estatisticas['porcentagem_empate']:.2f}%)\n")
        f.write(f"\nMédia de jogadas por partida: {estatisticas['media_jogadas']:.2f}\n")
        f.write(f"Mínimo: {estatisticas['min_jogadas']}\n")
        f.write(f"Máximo: {estatisticas['max_jogadas']}\n")
    print(f"📁 {nome_arquivo}")


# ================================================================
# Impressão no terminal
# ================================================================

def exibir_analise(estatisticas: Dict, nome_x: str, nome_o: str):
    if not estatisticas:
        print("❌ Nenhum dado para analisar.")
        return

    total = estatisticas['total']

    print("\n" + "=" * 70)
    print(f"   📊 ANÁLISE: {nome_x} (X) vs {nome_o} (O)")
    print("=" * 70)
    print(f"\n📈 Total de partidas: {total}")
    print("-" * 70)
    print(f"  🏆 Vitórias de {nome_x} (X): "
          f"{estatisticas['vitorias_x']:>7} ({estatisticas['porcentagem_x']:6.2f}%)")
    print(f"  🏆 Vitórias de {nome_o} (O): "
          f"{estatisticas['vitorias_o']:>7} ({estatisticas['porcentagem_o']:6.2f}%)")
    print(f"  🤝 Empates:                   "
          f"{estatisticas['empates']:>7} ({estatisticas['porcentagem_empate']:6.2f}%)")
    print(f"\n  Não-derrota de {nome_x}: "
          f"{estatisticas['porcentagem_x'] + estatisticas['porcentagem_empate']:.2f}%")
    print(f"  Não-derrota de {nome_o}: "
          f"{estatisticas['porcentagem_o'] + estatisticas['porcentagem_empate']:.2f}%")
    print("=" * 70)


def exibir_recortes(recortes: List[Dict], tipo: str):
    titulo = "ACUMULADO" if tipo == "acumulado" else "JANELAS"
    print("\n" + "=" * 100)
    print(f"        📊 RECORTES — {titulo}")
    print("=" * 100)
    print(f"{'Recorte':>22} | {'N':>8} | {'VitX%':>7} | {'VitO%':>7} | "
          f"{'Emp%':>7} | {'NãoDerrX%':>10} | {'NãoDerrO%':>10}")
    print("-" * 100)
    for r in recortes:
        print(f"{r['rotulo']:>22} | {r['n']:>8} | "
              f"{r['pct_vx']:>7.2f} | {r['pct_vo']:>7.2f} | "
              f"{r['pct_emp']:>7.2f} | "
              f"{r['pct_nao_derrota_x']:>10.2f} | "
              f"{r['pct_nao_derrota_o']:>10.2f}")
    print("=" * 100)


# ================================================================
# Função Principal
# ================================================================

def calcular_passo(total: int) -> int:
    if total <= 1_000:
        return 1
    if total <= 10_000:
        return 100
    if total <= 100_000:
        return 1_000
    if total <= 1_000_000:
        return 100_000
    return max(100_000, total // 1_000_000)


def main(arquivo_resultado: Optional[str] = None):
    print("\n" + "=" * 70)
    print("                    📊 ANALISADOR DE RESULTADOS")
    print("=" * 70 + "\n")

    # 1. Resolve caminho do arquivo
    caminho = arquivo_resultado if arquivo_resultado else "resultados.txt"
    if not os.path.exists(caminho):
        print(f"❌ Arquivo '{caminho}' não encontrado.")
        return

    # 2. Extrai nomes dos agentes do nome do arquivo
    nome_x, nome_o = extrair_agentes_do_nome(caminho)
    print(f"📖 Arquivo: {caminho}")
    print(f"👥 Agentes detectados: '{nome_x}' (X) vs '{nome_o}' (O)")

    # 3. Lê os dados
    dados = ler_arquivo_resultados(caminho)
    if not dados:
        print("❌ Sem dados para analisar.")
        return

    print(f"✅ {len(dados)} partidas carregadas.")

    # 4. Prepara a pasta de saída
    pasta = preparar_pasta_saida(caminho)
    print(f"📂 Pasta de saída: {pasta}\n")

    # 5. Análise geral
    estatisticas = analisar_resultados(dados)
    exibir_analise(estatisticas, nome_x, nome_o)

    exportar_resumo_txt(estatisticas, nome_x, nome_o,
                        os.path.join(pasta, "resumo.txt"))

    # 6. Recortes
    recortes_acumulados, recortes_janelas = _calcular_recortes(dados)
    exibir_recortes(recortes_acumulados, "acumulado")
    exibir_recortes(recortes_janelas, "janela")

    if EXPORTAR_CSV:
        exportar_recortes_csv(recortes_acumulados,
                              os.path.join(pasta, "recortes_acumulados.csv"),
                              "acumulado")
        exportar_recortes_csv(recortes_janelas,
                              os.path.join(pasta, "recortes_janelas.csv"),
                              "janela")
        exportar_recortes_txt(recortes_acumulados, recortes_janelas,
                        nome_x, nome_o,
                        os.path.join(pasta, "recortes.txt"))

    # 7. Gráficos gerais (série temporal contínua)
    passo = calcular_passo(len(dados))
    print(f"\n📈 Gerando gráficos (passo de amostragem: {passo})...")

    _plot_acumulado_absoluto(dados, passo,
                             os.path.join(pasta, "grafico_acumulado_absoluto.png"))
    _plot_taxas_acumuladas(dados, passo,
                           os.path.join(pasta, "grafico_acumulado_percentual.png"))

    # Gráfico específico do inteligente (se houver)
    if GERAR_GRAFICO_INTELIGENTE:
        if "inteligente" in (nome_x, nome_o):
            eh_segundo = (nome_o == "inteligente")
            nome_inteligente = "inteligente"
            _plot_grafico_inteligente(
                dados, passo, nome_inteligente, eh_segundo,
                os.path.join(pasta, "grafico_inteligente.png")
            )

    # 8. Gráficos de recorte (janela e acumulado, separados por categoria)
    gerar_graficos_recortes(recortes_acumulados, recortes_janelas,
                            nome_x, nome_o, pasta)

    print("\n✅ Análise concluída.\n")


if __name__ == "__main__":
    main()