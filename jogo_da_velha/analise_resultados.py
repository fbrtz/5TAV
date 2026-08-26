"""
analise_resultados.py
Script para analisar os resultados do jogo da velha.
Exibe estatísticas e porcentagens das partidas.
Todas as configurações são feitas diretamente no código.
"""

import os
from typing import List, Dict
from collections import Counter

# ================================================================
# CONFIGURAÇÕES
# ================================================================

ARQUIVO_RESULTADOS = "resultados.txt"      # Nome do arquivo de resultados
EXPORTAR_CSV = False                       # True para exportar análise para CSV
NOME_CSV = "analise_detalhada.csv"         # Nome do arquivo CSV (se exportar)

# ================================================================
# Constantes do jogo (para análise)
# ================================================================

X = 1
O = -1
VAZIO = 0

# ================================================================
# Funções de Análise
# ================================================================

def ler_arquivo_resultados(nome_arquivo: str) -> List[Dict]:
    """
    Lê o arquivo de resultados e retorna uma lista de dicionários com os dados.
    """
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
        
        # Pula o cabeçalho
        for num_linha, linha in enumerate(linhas[1:], start=2):
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
    """
    Analisa os dados e retorna estatísticas detalhadas.
    """
    if not dados:
        return {}

    total = len(dados)
    
    # Resultados básicos
    vitorias_x = sum(1 for d in dados if d['vitoria_x'] == 1)
    vitorias_o = sum(1 for d in dados if d['vitoria_o'] == 1)
    empates = sum(1 for d in dados if d['empate'] == 1)
    
    # Estatísticas de número de jogadas
    jogadas = [d['num_jogadas'] for d in dados]
    jogadas_por_resultado = {
        'X': [d['num_jogadas'] for d in dados if d['vitoria_x'] == 1],
        'O': [d['num_jogadas'] for d in dados if d['vitoria_o'] == 1],
        'Empate': [d['num_jogadas'] for d in dados if d['empate'] == 1]
    }
    
    # Análise das posições finais
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
    
    # Análise por tipo de vitória
    vitorias_por_tipo = {
        'linha': 0,
        'coluna': 0,
        'diagonal': 0
    }
    
    # Sequências de vitória mais comuns
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
    """
    Exibe a análise formatada de forma clara e organizada.
    """
    if not estatisticas:
        print("❌ Nenhum dado para analisar.")
        return

    total = estatisticas['total']
    
    print("\n" + "=" * 70)
    print("                    📊 ANÁLISE DOS RESULTADOS")
    print("=" * 70)
    print(f"\n📈 Total de partidas: {total}")
    print("-" * 70)
    
    # 1. RESULTADOS
    print(f"\n🎯 RESULTADOS:")
    print(f"  🏆 Vitórias do J1 (X): {estatisticas['vitorias_x']:4d}  ({estatisticas['porcentagem_x']:6.2f}%)")
    print(f"  🏆 Vitórias do J2 (O): {estatisticas['vitorias_o']:4d}  ({estatisticas['porcentagem_o']:6.2f}%)")
    print(f"  🤝 Empates:            {estatisticas['empates']:4d}  ({estatisticas['porcentagem_empate']:6.2f}%)")
    
    # 2. NÚMERO DE JOGADAS
    print(f"\n⏱️  NÚMERO DE JOGADAS:")
    print(f"  Média geral: {estatisticas['media_jogadas']:.2f}")
    print(f"  Mínimo: {estatisticas['min_jogadas']} jogadas")
    print(f"  Máximo: {estatisticas['max_jogadas']} jogadas")
    
    for resultado, jogadas in estatisticas['jogadas_por_resultado'].items():
        if jogadas:
            media = sum(jogadas) / len(jogadas)
            print(f"  Média em vitórias de {resultado}: {media:.2f} (n={len(jogadas)})")
    
    # 3. POSIÇÕES FINAIS
    print(f"\n🎯 POSIÇÕES FINAIS (quantas vezes cada posição terminou com X):")
    posicoes = estatisticas['posicoes_finais']
    
    print("\n  Tabuleiro de posições finais (%):")
    for i in range(0, 9, 3):
        linha = "    "
        for j in range(3):
            pos = i + j
            porcentagem = (posicoes[pos] / total) * 100
            linha += f" {pos}:{porcentagem:5.1f}% "
        print(linha)
    
    # Detalhamento por jogador (apenas X e O, pois VAZIO é complementar)
    print("\n  Detalhamento por jogador (%):")
    pos_por_jogador = estatisticas['posicoes_por_jogador']
    
    # X
    print("    X:")
    for i in range(0, 9, 3):
        linha = "      "
        for j in range(3):
            pos = i + j
            porcentagem = (pos_por_jogador['X'][pos] / total) * 100
            linha += f" {pos}:{porcentagem:5.1f}% "
        print(linha)
    
    # O
    print("    O:")
    for i in range(0, 9, 3):
        linha = "      "
        for j in range(3):
            pos = i + j
            porcentagem = (pos_por_jogador['O'][pos] / total) * 100
            linha += f" {pos}:{porcentagem:5.1f}% "
        print(linha)
    
    # 4. TIPO DE VITÓRIA
    print(f"\n🏆 TIPO DE VITÓRIA:")
    total_vitorias = estatisticas['vitorias_x'] + estatisticas['vitorias_o']
    for tipo, count in estatisticas['vitorias_por_tipo'].items():
        porcentagem = (count / total_vitorias) * 100 if total_vitorias > 0 else 0
        print(f"  {tipo.capitalize()}: {count:4d} partidas ({porcentagem:6.2f}%)")
    
    # 5. SEQUÊNCIAS MAIS COMUNS
    if estatisticas['sequencias_vitoria']:
        print(f"\n🎲 SEQUÊNCIAS DE VITÓRIA MAIS COMUNS:")
        for sequencia, count in estatisticas['sequencias_vitoria'].most_common(5):
            porcentagem = (count / total_vitorias) * 100 if total_vitorias > 0 else 0
            print(f"  {sequencia}: {count:4d} vezes ({porcentagem:6.2f}%)")
    
    print("\n" + "=" * 70)


def exportar_analise_para_csv(estatisticas: Dict, nome_arquivo: str = "analise_detalhada.csv"):
    """
    Exporta a análise para um arquivo CSV para processamento posterior.
    """
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
        
        # Posições finais (X)
        for i, count in enumerate(estatisticas['posicoes_finais']):
            f.write(f"Posicao_{i}_X,{count}\n")
        
        # Posições por jogador
        for jogador in ['X', 'O']:
            for i, count in enumerate(estatisticas['posicoes_por_jogador'][jogador]):
                f.write(f"Posicao_{i}_{jogador},{count}\n")
        
        # Tipos de vitória
        for tipo, count in estatisticas['vitorias_por_tipo'].items():
            f.write(f"Vitoria_{tipo},{count}\n")
    
    print(f"📁 Análise detalhada exportada para '{nome_arquivo}'")


# ================================================================
# Função Principal
# ================================================================

def main():
    """
    Função principal - executa a análise automaticamente.
    """
    print("\n" + "=" * 70)
    print("                    📊 ANALISADOR DE RESULTADOS")
    print("=" * 70 + "\n")
    
    print(f"📖 Lendo arquivo: {ARQUIVO_RESULTADOS}")
    dados = ler_arquivo_resultados(ARQUIVO_RESULTADOS)
    
    if dados:
        print(f"✅ {len(dados)} registros carregados com sucesso!")
        
        estatisticas = analisar_resultados(dados)
        exibir_analise(estatisticas)
        
        if EXPORTAR_CSV:
            exportar_analise_para_csv(estatisticas, NOME_CSV)
    else:
        print("❌ Não foi possível ler os dados do arquivo.")
        print("   Verifique se o arquivo existe e está no formato correto.")


if __name__ == "__main__":
    main()