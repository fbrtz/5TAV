import random
import time
import os
import json
from typing import List, Optional, Tuple, Dict
import jogo_da_velha.analise_resultados as analise_resultados 
import analise_resultados

# ================================================================
# CONFIGURAÇÕES
# ================================================================
REMOVER_ARQUIVOS_ANTIGOS = True  # Se True, remove arquivos de resultados e conhecimento antes de iniciar


NUM_PARTIDAS = 100000
ARQUIVO_RESULTADOS = "resultados.txt"
MODO_ESCRITA = "sobrescrever"  # opções: "sobrescrever", "anexar"

# Arquivo de conhecimento do jogador inteligente (JSONL)
BASE_CONHECIMENTO = "conhecimento.jsonl"

# Escolha os agentes:
# opções: "especialista", "ingenuo", "inteligente"
AGENTE_X = "inteligente"
AGENTE_O = "inteligente"

VISUALIZAR = False
TEMPO_ENTRE_JOGADAS = 0.5
LIMPAR_TELA = True

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
            (0,1,2), (3,4,5), (6,7,8),
            (0,3,6), (1,4,7), (2,5,8),
            (0,4,8), (2,4,6)
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

    def get_estado_posicoes(self) -> List[int]:
        return self.v.copy()

# ================================================================
# Classes de Jogadores (Agentes)
# ================================================================

class Jogador:
    def __init__(self, nome: str):
        self.nome = nome

    def escolher_jogada(self, tabuleiro: Tabuleiro, simbolo: int) -> int:
        raise NotImplementedError

    def notificar_fim_de_partida(self, resultado: int, jogadas: List[Tuple[Tuple[int, ...], int, int]]):
        """
        Chamado ao final da partida com o resultado e a lista de jogadas feitas.
        - resultado: X (1), O (-1) ou 0 (empate) — visão global do tabuleiro
        - jogadas: lista de (estado_do_tabuleiro_antes, jogada_escolhida, simbolo_do_jogador)
        """
        pass

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

        for pos in vazias:
            tabuleiro.v[pos] = simbolo
            if tabuleiro.verificar_vitoria() == simbolo:
                tabuleiro.v[pos] = VAZIO
                return pos
            tabuleiro.v[pos] = VAZIO

        for pos in vazias:
            tabuleiro.v[pos] = oponente
            if tabuleiro.verificar_vitoria() == oponente:
                tabuleiro.v[pos] = VAZIO
                return pos
            tabuleiro.v[pos] = VAZIO

        if (tabuleiro.v[0] == oponente and tabuleiro.v[8] == oponente
                and tabuleiro.v[3] == VAZIO):
            return 3
        if (tabuleiro.v[0] == oponente and tabuleiro.v[7] == oponente
                and tabuleiro.v[6] == VAZIO):
            return 6
        if (tabuleiro.v[2] == oponente and tabuleiro.v[6] == oponente
                and tabuleiro.v[5] == VAZIO):
            return 5
        if (tabuleiro.v[2] == oponente and tabuleiro.v[7] == oponente
                and tabuleiro.v[8] == VAZIO):
            return 8
        if (tabuleiro.v[6] == oponente and tabuleiro.v[1] == oponente
                and tabuleiro.v[0] == VAZIO):
            return 0
        if (tabuleiro.v[8] == oponente and tabuleiro.v[1] == oponente
                and tabuleiro.v[2] == VAZIO):
            return 2

        prioridades = [4, 0, 2, 6, 8, 1, 3, 5, 7]
        for pos in prioridades:
            if pos in vazias:
                return pos
        return vazias[0]


class JogadorInteligente(Jogador):
    """
    Jogador com aprendizado por valor e atualização por
    diferença temporal (TD).

    Chave da tabela: (estado, jogada, simbolo)
    Valor: (pontuacao, visitas) — pontuação estimada e número de visitas.

    Aprende ao final de cada partida, propagando recompensa do último
    estado para os anteriores. A política é gananciosa: escolhe sempre
    a jogada de maior pontuação; em empate, a menos visitada.
    """

    # ------------------------------------------------------------------
    # Parâmetros
    # ------------------------------------------------------------------
    TAXA_APRENDIZADO = 0.3   # quão rápido a pontuação se ajusta
    FATOR_DESCONTO = 1.0     # peso do futuro (1.0 = sem desconto)
    RECOMPENSA_VITORIA = 1.0
    RECOMPENSA_DERROTA = -1.0
    RECOMPENSA_EMPATE = 0.0

    def __init__(self, nome: str, arquivo_conhecimento: str):
        super().__init__(nome)
        self.arquivo = arquivo_conhecimento
        # Tabela em memória: chave → (pontuacao, visitas)
        # pontuacao é float, visitas é int
        self.tabela: Dict[Tuple[Tuple[int, ...], int, int], Tuple[float, int]] = {}
        # Jogadas desta partida, para atualização no final
        self._jogadas_da_partida: List[Tuple[Tuple[int, ...], int, int]] = []
        self._carregar_conhecimento()

    # ------------------------------------------------------------------
    # Persistência
    # ------------------------------------------------------------------
    def _carregar_conhecimento(self):
        """Carrega o arquivo JSONL inteiro para a memória."""
        if not os.path.exists(self.arquivo):
            return
        with open(self.arquivo, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    registro = json.loads(linha)
                    estado = tuple(registro["e"])
                    jogada = registro["j"]
                    simbolo = registro["s"]
                    pontuacao = float(registro["p"])
                    visitas = int(registro["v"])
                    self.tabela[(estado, jogada, simbolo)] = (pontuacao, visitas)
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue

    def _salvar_jogadas_da_partida(self):
        """Faz append das entradas atualizadas ao arquivo."""
        if not self._jogadas_da_partida:
            return
        with open(self.arquivo, "a", encoding="utf-8") as f:
            vistas = set()
            for (estado, jogada, simbolo) in self._jogadas_da_partida:
                chave = (estado, jogada, simbolo)
                if chave in vistas:
                    continue
                vistas.add(chave)
                pontuacao, visitas = self.tabela.get(chave, (0.0, 0))
                registro = {
                    "e": list(estado),
                    "j": jogada,
                    "s": simbolo,
                    "p": round(pontuacao, 6),
                    "v": visitas,
                }
                f.write(json.dumps(registro, separators=(",", ":")) + "\n")

    # ------------------------------------------------------------------
    # Decisão — política gananciosa com desempate por menor número de visitas
    # ------------------------------------------------------------------
    def escolher_jogada(self, tabuleiro: Tabuleiro, simbolo: int) -> int:
        vazias = tabuleiro.posicoes_vazias()
        if not vazias:
            return -1

        estado = tuple(tabuleiro.v)

        # Coleta (casa, pontuacao, visitas) para cada casa vazia
        candidatas = []
        for casa in vazias:
            chave = (estado, casa, simbolo)
            pontuacao, visitas = self.tabela.get(chave, (0.0, 0))
            candidatas.append((casa, pontuacao, visitas))

        # Ordena por pontuação decrescente; em empate, escolhe a menos visitada.
        # Isso é a política gananciosa com exploração implícita.
        candidatas.sort(key=lambda x: (-x[1], x[2]))
        melhor_jogada = candidatas[0][0]

        # Registra a jogada para a atualização no fim da partida
        chave_nova = (estado, melhor_jogada, simbolo)
        if chave_nova not in self.tabela:
            self.tabela[chave_nova] = (0.0, 0)

        self._jogadas_da_partida.append(chave_nova)
        return melhor_jogada

    # ------------------------------------------------------------------
    # Aprendizado — diferença temporal, do último estado para o primeiro
    # ------------------------------------------------------------------
    def notificar_fim_de_partida(self, resultado: int, jogadas_globais=None):
        """
        Atualiza pontuações propagando a recompensa final de trás para frente.

        - resultado: X (1), O (-1) ou 0 (empate)
        - Recompensa final: +1 se o inteligente venceu, -1 se perdeu, 0 se empatou.
        """
        if not self._jogadas_da_partida:
            return

        simbolo_inteligente = self._jogadas_da_partida[0][2]

        # Recompensa final — só a última jogada recebe valor não-zero diretamente
        if resultado == 0:
            recompensa_final = self.RECOMPENSA_EMPATE
        elif resultado == simbolo_inteligente:
            recompensa_final = self.RECOMPENSA_VITORIA
        else:
            recompensa_final = self.RECOMPENSA_DERROTA

        # Propaga do último estado para o primeiro
        valor_futuro = recompensa_final

        for chave in reversed(self._jogadas_da_partida):
            pontuacao, visitas = self.tabela.get(chave, (0.0, 0))
            alvo = valor_futuro
            pontuacao_nova = pontuacao + self.TAXA_APRENDIZADO * (alvo - pontuacao)
            visitas_novas = visitas + 1
            self.tabela[chave] = (pontuacao_nova, visitas_novas)
            # O valor futuro para a jogada anterior é o valor atualizado
            valor_futuro = pontuacao_nova

        # Salva e limpa
        self._salvar_jogadas_da_partida()
        self._jogadas_da_partida = []

# ================================================================
# Classe Partida
# ================================================================

class Partida:
    def __init__(self, jogador_x: Jogador, jogador_o: Jogador):
        self.jogador_x = jogador_x
        self.jogador_o = jogador_o
        self.tabuleiro = Tabuleiro()
        self.resultado = None
        self.estado_final = None

    def jogar(self, visivel: bool = False, tempo_espera: float = 0.5,
              limpar_tela: bool = True) -> int:
        self.tabuleiro.reset()
        self.resultado = None
        self.estado_final = None
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
                self.estado_final = self.tabuleiro.get_estado_posicoes()
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

        # Notifica os jogadores que a partida acabou
        for jogador in (self.jogador_x, self.jogador_o):
            jogador.notificar_fim_de_partida(self.resultado, None)

        return self.resultado

    def registrar_resultado(self, numero: int) -> Tuple[int, int, int, int, int, List[int]]:
        vx = 1 if self.resultado == X else 0
        vo = 1 if self.resultado == O else 0
        emp = 1 if self.resultado == 0 else 0
        estado = self.estado_final if self.estado_final is not None else self.tabuleiro.get_estado_posicoes()
        return (numero, vx, vo, emp, self.tabuleiro.jogadas, estado)

# ================================================================
# Função de simulação
# ================================================================

def simular(jogador_x, jogador_o, num_partidas, arquivo_saida,
            visualizar=False, tempo=0.5, limpar_tela=True,
            modo_escrita="sobrescrever"):
    print(f"Iniciando simulação de {num_partidas} partidas...")
    if visualizar:
        print("Modo visual ativado. Pressione Ctrl+C para interromper a qualquer momento.\n")
    else:
        print("Modo silencioso (sem exibição).\n")

    modo_abertura = 'w' if modo_escrita.lower() == "sobrescrever" else 'a'
    arquivo_existe = os.path.isfile(arquivo_saida)
    escrever_cabecalho = not arquivo_existe or modo_escrita.lower() == "sobrescrever"

    with open(arquivo_saida, modo_abertura, encoding="utf-8") as f:
        if escrever_cabecalho:
            cabecalho = "Partida\tVitoria_J1\tVitoria_J2\tEmpate\tNum_Jogadas\tV0\tV1\tV2\tV3\tV4\tV5\tV6\tV7\tV8\n"
            f.write(cabecalho)
            print(f"Cabeçalho escrito no arquivo: {arquivo_saida}")
        else:
            print(f"Anexando dados ao arquivo existente: {arquivo_saida}")

        for i in range(1, num_partidas + 1):
            partida = Partida(jogador_x, jogador_o)
            partida.jogar(visivel=visualizar, tempo_espera=tempo,
                          limpar_tela=limpar_tela)
            dados = partida.registrar_resultado(i)

            linha = f"{dados[0]}\t{dados[1]}\t{dados[2]}\t{dados[3]}\t{dados[4]}"
            for pos in dados[5]:
                linha += f"\t{pos}"
            linha += "\n"
            f.write(linha)

            if not visualizar and i % 1000 == 0:
                print(f"  {i} partidas concluídas...")

    print(f"\nSimulação finalizada. Resultados salvos em '{arquivo_saida}'.")

# ================================================================
# Função principal
# ================================================================

def main():
    def criar_agente(tipo, nome):
        if tipo.lower() == "especialista":
            return JogadorEspecialista(nome)
        elif tipo.lower() == "ingenuo":
            return JogadorIngenuo(nome)
        elif tipo.lower() == "inteligente":
            return JogadorInteligente(nome, BASE_CONHECIMENTO)
        else:
            raise ValueError(f"Tipo de agente desconhecido: {tipo}")

    jogador_x = criar_agente(AGENTE_X, f"Agente_{AGENTE_X}_X")
    jogador_o = criar_agente(AGENTE_O, f"Agente_{AGENTE_O}_O")

    simular(jogador_x, jogador_o, NUM_PARTIDAS, ARQUIVO_RESULTADOS,
            visualizar=VISUALIZAR, tempo=TEMPO_ENTRE_JOGADAS,
            limpar_tela=LIMPAR_TELA, modo_escrita=MODO_ESCRITA)

if __name__ == "__main__":
    if REMOVER_ARQUIVOS_ANTIGOS:
        try:
            os.remove(ARQUIVO_RESULTADOS)
            print("Arquivos deletados com sucesso.")
        except FileNotFoundError:
            print("O arquivo não foi encontrado.")
        except PermissionError:
            print("Você não tem permissão para apagar este arquivo.")

        try:
            os.remove(BASE_CONHECIMENTO)
            print("Arquivos deletados com sucesso.")
        except FileNotFoundError:
            print("O arquivo não foi encontrado.")
        except PermissionError:
            print("Você não tem permissão para apagar este arquivo.")
    main()
    analise_resultados.main()
    
