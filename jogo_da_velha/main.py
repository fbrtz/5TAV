import random
import time
import os
from typing import List, Optional, Tuple

# ================================================================
# CONFIGURAÇÕES (altere aqui conforme desejar)
# ================================================================

NUM_PARTIDAS = 30                # Quantas partidas serão simuladas
ARQUIVO_RESULTADOS = "resultados.txt"

# Escolha os agentes:
# opções: "especialista", "ingenuo", "random" (ingenuo é random)
AGENTE_X = "especialista"        # Jogador que usa X (começa)
AGENTE_O = "especialista"             # Jogador que usa O

# Configurações de visualização
VISUALIZAR = False                # True para exibir cada partida, False para apenas simular
TEMPO_ENTRE_JOGADAS = 0.5        # segundos (se VISUALIZAR for True)
LIMPAR_TELA = True               # limpa a tela a cada jogada (se VISUALIZAR for True)

# ================================================================
# Constantes do jogo
# ================================================================

X = 1
O = -1
VAZIO = 0
SIMBOLO = {X: 'X', O: 'O', VAZIO: ' '}

# ================================================================
# Classe Tabuleiro
# ================================================================

class Tabuleiro:
    def __init__(self):
        self.v = [VAZIO] * 9
        self.jogadas = 0

    def reset(self):
        self.v = [VAZIO] * 9
        self.jogadas = 0

    def fazer_jogada(self, posicao: int, jogador: int) -> bool:
        if posicao < 0 or posicao > 8 or self.v[posicao] != VAZIO:
            return False
        self.v[posicao] = jogador
        self.jogadas += 1
        return True

    def tabuleiro_cheio(self) -> bool:
        return self.jogadas == 9

    def verificar_vitoria(self) -> Optional[int]:
        combinacoes = [
            (0,1,2), (3,4,5), (6,7,8),          #Linhas
            (0,3,6), (1,4,7), (2,5,8),          #Colunas
            (0,4,8), (2,4,6)                    #Diagonais
        ]
        for a,b,c in combinacoes:
            soma = self.v[a] + self.v[b] + self.v[c]
            if soma == 3:
                return X
            if soma == -3:
                return O
        if self.tabuleiro_cheio():
            return 0
        return None

    def posicoes_vazias(self) -> List[int]:
        return [i for i, val in enumerate(self.v) if val == VAZIO]

    def exibir(self) -> str:
        sep = "\n---+---+---\n"
        linhas = []
        for i in range(0, 9, 3):
            linha = f" {SIMBOLO[self.v[i]]} | {SIMBOLO[self.v[i+1]]} | {SIMBOLO[self.v[i+2]]} "
            linhas.append(linha)
        return sep.join(linhas)

# ================================================================
# Classes de Jogadores (Agentes)
# ================================================================

class Jogador:
    def __init__(self, nome: str):
        self.nome = nome

    def escolher_jogada(self, tabuleiro: Tabuleiro, simbolo: int) -> int:
        raise NotImplementedError

class JogadorIngenuo(Jogador):
    def escolher_jogada(self, tabuleiro: Tabuleiro, simbolo: int) -> int:
        vazias = tabuleiro.posicoes_vazias()
        return random.choice(vazias) if vazias else -1

class JogadorEspecialista(Jogador):
    def escolher_jogada(self, tabuleiro: Tabuleiro, simbolo: int) -> int:
        vazias = tabuleiro.posicoes_vazias()
        if not vazias:
            return -1
        oponente = -simbolo
        # Tentar ganhar
        for pos in vazias:
            tabuleiro.v[pos] = simbolo
            if tabuleiro.verificar_vitoria() == simbolo:
                tabuleiro.v[pos] = VAZIO
                return pos
            tabuleiro.v[pos] = VAZIO
        # Bloquear
        for pos in vazias:
            tabuleiro.v[pos] = oponente
            if tabuleiro.verificar_vitoria() == oponente:
                tabuleiro.v[pos] = VAZIO
                return pos
            tabuleiro.v[pos] = VAZIO
        # Prioridades: centro, cantos, laterais
        prioridades = [4, 0, 2, 6, 8, 1, 3, 5, 7]
        for pos in prioridades:
            if pos in vazias:
                return pos
        return vazias[0]

# ================================================================
# Classe Partida
# ================================================================

class Partida:
    def __init__(self, jogador_x: Jogador, jogador_o: Jogador):
        self.jogador_x = jogador_x
        self.jogador_o = jogador_o
        self.tabuleiro = Tabuleiro()
        self.resultado = None

    def jogar(self, visivel: bool = False, tempo_espera: float = 0.5,
              limpar_tela: bool = True) -> int:
        self.tabuleiro.reset()
        self.resultado = None
        vez = X

        while True:
            if visivel:
                if limpar_tela:
                    os.system('cls' if os.name == 'nt' else 'clear')
                print("\n--- JOGO DA VELHA ---\n")
                print(self.tabuleiro.exibir())
                print(f"\nVez de: {self.jogador_x.nome if vez == X else self.jogador_o.nome} ({SIMBOLO[vez]})")
                time.sleep(tempo_espera)

            jogador_atual = self.jogador_x if vez == X else self.jogador_o
            posicao = jogador_atual.escolher_jogada(self.tabuleiro, vez)

            if posicao == -1 or not self.tabuleiro.fazer_jogada(posicao, vez):
                vazias = self.tabuleiro.posicoes_vazias()
                if vazias:
                    self.tabuleiro.fazer_jogada(vazias[0], vez)
                else:
                    self.resultado = 0
                    break

            if visivel:
                time.sleep(tempo_espera)

            fim = self.tabuleiro.verificar_vitoria()
            if fim is not None:
                self.resultado = fim
                if visivel:
                    if limpar_tela:
                        os.system('cls' if os.name == 'nt' else 'clear')
                    print("\n--- JOGO DA VELHA ---\n")
                    print(self.tabuleiro.exibir())
                    if fim == X:
                        print(f"\n{self.jogador_x.nome} (X) venceu!")
                    elif fim == O:
                        print(f"\n{self.jogador_o.nome} (O) venceu!")
                    else:
                        print("\nEmpate!")
                    time.sleep(1.5)
                break

            vez = O if vez == X else X

        return self.resultado

    def registrar_resultado(self, numero: int) -> Tuple[int, int, int, int]:
        vx = 1 if self.resultado == X else 0
        vo = 1 if self.resultado == O else 0
        emp = 1 if self.resultado == 0 else 0
        return (numero, vx, vo, emp)

# ================================================================
# Função de simulação
# ================================================================

def simular(jogador_x, jogador_o, num_partidas, arquivo_saida,
            visualizar=False, tempo=0.5, limpar_tela=True):
    print(f"Iniciando simulação de {num_partidas} partidas...")
    if visualizar:
        print("Modo visual ativado. Pressione Ctrl+C para interromper a qualquer momento.\n")
    else:
        print("Modo silencioso (sem exibição).\n")

    with open(arquivo_saida, "w", encoding="utf-8") as f:
        f.write("Partida\tVitoria_J1\tVitoria_J2\tEmpate\n")
        for i in range(1, num_partidas + 1):
            partida = Partida(jogador_x, jogador_o)
            partida.jogar(visivel=visualizar, tempo_espera=tempo,
                          limpar_tela=limpar_tela)
            dados = partida.registrar_resultado(i)
            f.write(f"{dados[0]}\t{dados[1]}\t{dados[2]}\t{dados[3]}\n")
            if not visualizar and i % 1000 == 0:
                print(f"  {i} partidas concluídas...")
    print(f"\nSimulação finalizada. Resultados salvos em '{arquivo_saida}'.")

# ================================================================
# Função principal
# ================================================================

def main():
    # Cria os agentes com base nas configurações
    def criar_agente(tipo, nome):
        if tipo.lower() == "especialista":
            return JogadorEspecialista(nome)
        elif tipo.lower() == "ingenuo":
            return JogadorIngenuo(nome)
        else:
            raise ValueError(f"Tipo de agente desconhecido: {tipo}")

    jogador_x = criar_agente(AGENTE_X, f"Agente_{AGENTE_X}_X")
    jogador_o = criar_agente(AGENTE_O, f"Agente_{AGENTE_O}_O")

    # Executa a simulação
    simular(jogador_x, jogador_o, NUM_PARTIDAS, ARQUIVO_RESULTADOS,
            visualizar=VISUALIZAR, tempo=TEMPO_ENTRE_JOGADAS,
            limpar_tela=LIMPAR_TELA)

if __name__ == "__main__":
    main()