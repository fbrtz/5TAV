"""
analise_resultados.py
Script para analisar os resultados do jogo da velha.
Exibe estatísticas, porcentagens e gera gráficos acumulados desde o início.
Todas as configurações são feitas diretamente no código.
"""

import os
from typing import List, Dict
from collections import Counter

import matplotlib
matplotlib.use("Agg")  # backend sem interface gráfica
import matplotlib.pyplot as plt

# ================================================================
# CONFIGURAÇÕES
# ================================================================

ARQUIVO_RESULTADOS = "resultados.txt"
EXPORTAR_CSV = True
NOME_CSV = "Resultados.csv"

# Nomes dos arquivos de gráfico
ARQUIVO_GRAFICO_ACUMULADO_ABS = "grafico_acumulado_absoluto.png"
ARQUIVO_GRAFICO_ACUMULADO_PCT = "grafico_acumulado_percentual.png"
ARQUIVO_GRAFICO_INTELIGENTE   = "grafico_inteligente.png"

# Se True, gera também o gráfico do jogador inteligente (assumindo que é J2/O)
GERAR_GRAFICO_INTELIGENTE = True

# Nome do jogador inteligente (informativo, apenas no título do gráfico)
NOME_INTELIGENTE = "inteligente"

# ================================================================
# Constantes do jogo
# ================================================================

X = 1
O = -1
VAZIO = 0

# ================================================================
# Funções de Análise
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
    posicoes_por_jogador = {
        'X': [0] * 9,
        'O': [0] * 9,
        'VAZIO': [0] * 9
    }

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


def exibir_analise(estatisticas: Dict):
    if not estatisticas:
        print("❌ Nenhum dado para analisar.")
        return

    total = estatisticas['total']

    print("\n" + "=" * 70)
    print("                    📊 ANÁLISE DOS RESULTADOS")
    print("=" * 70)
    print(f"\n📈 Total de partidas: {total}")
    print("-" * 70)

    print(f"\n🎯 RESULTADOS:")
    print(f"  🏆 Vitórias do J1 (X): {estatisticas['vitorias_x']:4d}  ({estatisticas['porcentagem_x']:6.2f}%)")
    print(f"  🏆 Vitórias do J2 (O): {estatisticas['vitorias_o']:4d}  ({estatisticas['porcentagem_o']:6.2f}%)")
    print(f"  🤝 Empates:            {estatisticas['empates']:4d}  ({estatisticas['porcentagem_empate']:6.2f}%)")

    print(f"\n⏱️  NÚMERO DE JOGADAS:")
    print(f"  Média geral: {estatisticas['media_jogadas']:.2f}")
    print(f"  Mínimo: {estatisticas['min_jogadas']} jogadas")
    print(f"  Máximo: {estatisticas['max_jogadas']} jogadas")

    for resultado, jogadas in estatisticas['jogadas_por_resultado'].items():
        if jogadas:
            media = sum(jogadas) / len(jogadas)
            print(f"  Média em vitórias de {resultado}: {media:.2f} (n={len(jogadas)})")

    print(f"\n🎯 POSIÇÕES FINAIS:")
    posicoes = estatisticas['posicoes_finais']

    print("\n  Tabuleiro de posições finais (%):")
    for i in range(0, 9, 3):
        linha = "    "
        for j in range(3):
            pos = i + j
            porcentagem = (posicoes[pos] / total) * 100
            linha += f" {pos}:{porcentagem:5.1f}% "
        print(linha)

    print("\n  Detalhamento por jogador (%):")
    pos_por_jogador = estatisticas['posicoes_por_jogador']

    print("    X:")
    for i in range(0, 9, 3):
        linha = "      "
        for j in range(3):
            pos = i + j
            porcentagem = (pos_por_jogador['X'][pos] / total) * 100
            linha += f" {pos}:{porcentagem:5.1f}% "
        print(linha)

    print("    O:")
    for i in range(0, 9, 3):
        linha = "      "
        for j in range(3):
            pos = i + j
            porcentagem = (pos_por_jogador['O'][pos] / total) * 100
            linha += f" {pos}:{porcentagem:5.1f}% "
        print(linha)

    print(f"\n🏆 TIPO DE VITÓRIA:")
    total_vitorias = estatisticas['vitorias_x'] + estatisticas['vitorias_o']
    for tipo, count in estatisticas['vitorias_por_tipo'].items():
        porcentagem = (count / total_vitorias) * 100 if total_vitorias > 0 else 0
        print(f"  {tipo.capitalize()}: {count:4d} partidas ({porcentagem:6.2f}%)")

    if estatisticas['sequencias_vitoria']:
        print(f"\n🎲 SEQUÊNCIAS DE VITÓRIA MAIS COMUNS:")
        for sequencia, count in estatisticas['sequencias_vitoria'].most_common(5):
            porcentagem = (count / total_vitorias) * 100 if total_vitorias > 0 else 0
            print(f"  {sequencia}: {count:4d} vezes ({porcentagem:6.2f}%)")

    print("\n" + "=" * 70)


# ================================================================
# Amostragem adaptativa
# ================================================================

def calcular_passo(total: int) -> int:
    """
    Escolhe o passo de amostragem com base no número total de partidas.
    Regra:
      <= 1.000         → 1 (todos os pontos)
      <= 10.000        → 100
      <= 100.000       → 1.000
      <= 1.000.000     → 100.000
      > 1.000.000      → total // 1.000.000 (mínimo 100.000)
    """
    if total <= 1_000:
        return 1
    if total <= 10_000:
        return 100
    if total <= 100_000:
        return 1_000
    if total <= 1_000_000:
        return 100_000
    return max(100_000, total // 1_000_000)


# ================================================================
# Cálculo acumulado (desde a partida 1)
# ================================================================

def _calcular_acumulados(dados, passo):
    """
    Retorna listas paralelas:
      eixo_x: número da partida (amostrado)
      acum_j1, acum_j2, acum_emp: contagens ACUMULADAS absolutas
      pct_j1, pct_j2, pct_emp: taxas ACUMULADAS em %
    """
    n = len(dados)
    eixo_x = []
    acum_j1, acum_j2, acum_emp = [], [], []
    pct_j1, pct_j2, pct_emp = [], [], []

    total_j1 = 0
    total_j2 = 0
    total_emp = 0

    for i, d in enumerate(dados, start=1):
        total_j1 += d['vitoria_x']
        total_j2 += d['vitoria_o']
        total_emp += d['empate']

        if i % passo == 0 or i == n:
            eixo_x.append(i)
            acum_j1.append(total_j1)
            acum_j2.append(total_j2)
            acum_emp.append(total_emp)
            pct_j1.append(total_j1 / i * 100)
            pct_j2.append(total_j2 / i * 100)
            pct_emp.append(total_emp / i * 100)

    return eixo_x, acum_j1, acum_j2, acum_emp, pct_j1, pct_j2, pct_emp


# ================================================================
# Gráficos
# ================================================================

def gerar_grafico_acumulado_absoluto(dados, passo, arquivo_saida):
    """Acumulado absoluto desde a partida 1 (contagem)."""
    eixo_x, a1, a2, ae, _, _, _ = _calcular_acumulados(dados, passo)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(eixo_x, a1, label="Vitórias J1 (X) acumuladas", color="#1f77b4", linewidth=1.8)
    ax.plot(eixo_x, a2, label="Vitórias J2 (O) acumuladas", color="#d62728", linewidth=1.8)
    ax.plot(eixo_x, ae, label="Empates acumulados", color="#2ca02c", linewidth=1.8)

    ax.set_xlabel("Número da partida")
    ax.set_ylabel("Contagem acumulada (absoluta)")
    ax.set_title("Acumulado absoluto desde o início")
    ax.grid(True, alpha=0.3)
    ax.legend()

    plt.tight_layout()
    plt.savefig(arquivo_saida, dpi=120)
    plt.close(fig)
    print(f"📊 Gráfico acumulado absoluto salvo em '{arquivo_saida}'")


def gerar_grafico_acumulado_percentual(dados, passo, arquivo_saida):
    """Acumulado percentual desde a partida 1 (taxas)."""
    eixo_x, _, _, _, p1, p2, pe = _calcular_acumulados(dados, passo)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(eixo_x, p1, label="Vitórias J1 (X) %", color="#1f77b4", linewidth=1.8)
    ax.plot(eixo_x, p2, label="Vitórias J2 (O) %", color="#d62728", linewidth=1.8)
    ax.plot(eixo_x, pe, label="Empates %", color="#2ca02c", linewidth=1.8)

    ax.set_xlabel("Número da partida")
    ax.set_ylabel("Taxa acumulada (%)")
    ax.set_title("Taxas acumuladas desde o início")
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_ylim(-2, 102)

    plt.tight_layout()
    plt.savefig(arquivo_saida, dpi=120)
    plt.close(fig)
    print(f"📊 Gráfico acumulado percentual salvo em '{arquivo_saida}'")


def gerar_grafico_inteligente(dados, passo, nome_inteligente, arquivo_saida):
    """
    Gráfico do jogador inteligente, assumindo que ele é J2 (O).
    Plota taxas acumuladas desde o início:
      - não-derrota (vitória J2 + empate)
      - vitória J2
      - empate
    """
    eixo_x, _, _, _, _, p2, pe = _calcular_acumulados(dados, passo)
    nao_derrota = [v + e for v, e in zip(p2, pe)]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(eixo_x, nao_derrota, label="Não-derrota (vitória J2 + empate)",
            color="#2ca02c", linewidth=2.0)
    ax.plot(eixo_x, p2, label="Vitória do inteligente (J2)",
            color="#1f77b4", linewidth=1.3, linestyle="--")
    ax.plot(eixo_x, pe, label="Empate",
            color="#ff7f0e", linewidth=1.3, linestyle=":")

    ax.set_xlabel("Número da partida")
    ax.set_ylabel("Taxa acumulada (%)")
    ax.set_title(f"Desempenho do jogador '{nome_inteligente}' — acumulado desde o início")
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_ylim(-2, 102)

    plt.tight_layout()
    plt.savefig(arquivo_saida, dpi=120)
    plt.close(fig)
    print(f"📊 Gráfico do inteligente salvo em '{arquivo_saida}'")


# ================================================================
# Exportação CSV
# ================================================================

def exportar_analise_para_csv(estatisticas: Dict, nome_arquivo: str = "analise_detalhada.csv"):
    if not estatisticas:
        return

    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        f.write("Metrica,Valor\n")
        f.write(f"Total de Partidas,{estatisticas['total']}\n")
        f.write(f"Vitorias_X,{estatisticas['vitorias_x']}\n")
        f.write(f"Vitorias_O,{estatisticas['vitorias_o']}\n")
        f.write(f"Empates,{estatisticas['empates']}\n")
        f.write(f"Porcentagem_X,{estatisticas['porcentagem_x']:.2f}\n")
        f.write(f"Porcentagem_O,{estatisticas['porcentagem_o']:.2f}\n")
        f.write(f"Porcentagem_Empate,{estatisticas['porcentagem_empate']:.2f}\n")
        f.write(f"Media_Jogadas,{estatisticas['media_jogadas']:.2f}\n")
        f.write(f"Min_Jogadas,{estatisticas['min_jogadas']}\n")
        f.write(f"Max_Jogadas,{estatisticas['max_jogadas']}\n")

        for i, count in enumerate(estatisticas['posicoes_finais']):
            f.write(f"Posicao_{i}_X,{count}\n")

        for jogador in ['X', 'O']:
            for i, count in enumerate(estatisticas['posicoes_por_jogador'][jogador]):
                f.write(f"Posicao_{i}_{jogador},{count}\n")

        for tipo, count in estatisticas['vitorias_por_tipo'].items():
            f.write(f"Vitoria_{tipo},{count}\n")

    print(f"📁 Análise detalhada exportada para '{nome_arquivo}'")


# ================================================================
# Função Principal
# ================================================================

def main():
    print("\n" + "=" * 70)
    print("                    📊 ANALISADOR DE RESULTADOS")
    print("=" * 70 + "\n")

    print(f"📖 Lendo arquivo: {ARQUIVO_RESULTADOS}")
    dados = ler_arquivo_resultados(ARQUIVO_RESULTADOS)

    if not dados:
        print("❌ Não foi possível ler os dados do arquivo.")
        print("   Verifique se o arquivo existe e está no formato correto.")
        return

    print(f"✅ {len(dados)} registros carregados com sucesso!")

    estatisticas = analisar_resultados(dados)
    exibir_analise(estatisticas)

    if EXPORTAR_CSV:
        exportar_analise_para_csv(estatisticas, NOME_CSV)

    # Passo de amostragem adaptativo (calculado pelo total)
    passo = calcular_passo(len(dados))
    print(f"\n📈 Gerando gráficos (passo de amostragem: {passo})...")

    gerar_grafico_acumulado_absoluto(dados, passo, ARQUIVO_GRAFICO_ACUMULADO_ABS)
    gerar_grafico_acumulado_percentual(dados, passo, ARQUIVO_GRAFICO_ACUMULADO_PCT)

    if GERAR_GRAFICO_INTELIGENTE:
        gerar_grafico_inteligente(dados, passo, NOME_INTELIGENTE,
                                  ARQUIVO_GRAFICO_INTELIGENTE)

    print("\n✅ Análise concluída.")


if __name__ == "__main__":
    main()