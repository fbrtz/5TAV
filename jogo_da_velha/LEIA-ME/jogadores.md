# Guia dos Jogadores — Como cada agente funciona

Este documento explica **os três tipos de jogadores** do simulador de
jogo da velha, **como cada um decide suas jogadas** e, em especial,
**como o `JogadorInteligente` aprende**.

---

## Sumário

1. [Visão geral](#1-visão-geral)
2. [JogadorIngenuo — o aleatório](#2-jogadoringenuo--o-aleatório)
3. [JogadorEspecialista — a heurística](#3-jogadorespecialista--a-heurística)
4. [JogadorInteligente — o que aprende](#4-jogadorinteligente--o-que-aprende)
5. [Como os três se relacionam](#5-como-os-três-se-relacionam)
6. [Como executar combinações diferentes](#6-como-executar-combinações-diferentes)
7. [Resumo em uma tabela](#7-resumo-em-uma-tabela)
8. [Onde olhar para entender o aprendizado](#8-onde-olhar-para-entender-o-aprendizado)
9. [Observações finais](#9-observações-finais)

---

## 1. Visão geral

O simulador tem três agentes intercambiáveis:

| Agente | Estratégia | Aprende? | Determinístico? |
|---|---|---|---|
| `JogadorIngenuo` | Aleatório puro | Não | Não |
| `JogadorEspecialista` | Regras fixas (heurística) | Não | Sim |
| `JogadorInteligente` | Aprendizado por reforço | Sim | Após convergir |

Todos herdam da classe `Jogador`, que define a interface:

```python
class Jogador:
    def escolher_jogada(self, tabuleiro, simbolo) -> int: ...
    def notificar_fim_de_partida(self, resultado, jogadas): ...
```

O `escolher_jogada` é chamado **antes de cada jogada**. O
`notificar_fim_de_partida` é chamado **uma única vez ao final de
cada partida**, para que o jogador possa aprender com o resultado.

---

## 2. `JogadorIngenuo` — o aleatório

### Como decide

```python
def escolher_jogada(self, tabuleiro, simbolo):
    vazias = tabuleiro.posicoes_vazias()
    return random.choice(vazias) if vazias else -1
```

Uma linha. Escolhe **uniformemente ao acaso** entre as casas vazias.
Não considera nada: nem ameaças, nem oportunidades, nem o estado
atual.

### Para que serve

É o **adversário de referência**. Serve para:

- Medir se os outros agentes **realmente aprenderam** a vencer alguém.
- Estabelecer a **linha base** do jogo — sem estratégia, qual é a
  distribuição de resultados?
- Dar **ruído controlado** ao treino do inteligente — o ingênuo erra
  de formas imprevisíveis, expondo o agente a estados diversos.

### O que esperar

- **Contra ele mesmo**: vitórias de X ~58%, vitórias de O ~29%,
  empates ~13%. O X tem vantagem estrutural (começa, joga 5 vezes).
- **Contra o especialista**: o especialista ganha quase sempre e
  quase nunca perde.
- **Contra o inteligente treinado**: o inteligente ganha com
  frequência, e nunca (ou quase nunca) perde.

---

## 3. `JogadorEspecialista` — a heurística

### Como decide

Aplica uma **cascata de regras**, na seguinte ordem de prioridade:

1. **Vitória imediata**: se alguma casa dá vitória agora, joga lá.
2. **Bloqueio imediato**: se o adversário ganharia na próxima jogada
   em alguma casa, joga lá para bloquear.
3. **Anti-fork explícito**: seis regras "se o oponente tem dois
   cantos opostos/adjacentes específicos, jogue na lateral que
   quebra o fork". Essas regras cobrem os forks clássicos do jogo
   da velha.
4. **Prioridades fixas**: joga na casa de maior prioridade entre as
   vazias, na ordem `[4, 0, 2, 6, 8, 1, 3, 5, 7]` (centro → cantos
   → laterais).

Se nenhuma das regras disparar, joga na **primeira casa vazia**.

### Para que serve

É o **adversário forte determinístico**. Serve para:

- Testar o inteligente contra jogo **consistente** — sem a variação
  do ingênuo.
- Servir como **referência de teto**: se o inteligente empata com o
  especialista, está no teto.
- Medir se o inteligente **generaliza** — aprender contra aleatório
  pode não bastar; contra especialista, ele precisa jogar bem.

### O que esperar

- **Como X**: vence quase sempre o ingênuo, perde raríssimas vezes.
- **Como O**: ainda vence muito, mas perde uma fração (o especialista
  é míope para alguns forks não clássicos — as regras anti-fork
  explícitas cobrem só os casos mais comuns).
- **Contra o inteligente treinado**: **empates quase 100%**. Se
  houver vitórias do especialista, são o resíduo da exploração do
  inteligente.
- **Contra ele mesmo**: 100% de empates.

### Limitação conhecida

A heurística **não detecta forks dinamicamente**. Ela só reconhece
os seis padrões de cantos opostos/adjacentes que enumeramos no
código. Existem configurações de fork que escapam. Por isso o
especialista **não é ótimo** — apenas muito bom.

---

## 4. `JogadorInteligente` — o que aprende

Este é o coração do projeto. Vou dividir em **como decide**, **como
aprende** e **quais parâmetros controlam o aprendizado**.

### 4.1. Como decide

A decisão tem três passos.

**Passo 1 — Olha cada casa vazia e consulta a tabela.**

Para cada casa vazia, monta a chave:

```python
chave = (estado_do_tabuleiro, casa, simbolo_do_jogador)
```

E busca na tabela:

```python
pontuacao, visitas = self.tabela.get(chave, (0.0, 0))
```

Se a chave **nunca foi vista**, o valor padrão é `(0.0, 0)` — ou
seja, pontuação neutra e zero visitas.

**Passo 2 — Ordena as casas por dois critérios.**

```python
candidatas.sort(key=lambda x: (-x[1], x[2]))
```

- **Primeiro critério**: maior **pontuação** (o que a chave
  aprendeu).
- **Segundo critério**: em caso de empate de pontuação, menor
  número de **visitas**.

**Passo 3 — Escolhe a primeira da lista** e registra essa jogada
para a atualização no final da partida.

**Por que esse critério de desempate é importante**: em estados
onde duas ou mais casas têm a mesma pontuação estimada, o agente
**prefere testar as menos visitadas**. Isso dá **exploração
automática** sem precisar de aleatoriedade. É a "política
gananciosa com exploração por menor N" que discutimos.

### 4.2. Como aprende

O aprendizado acontece **ao final de cada partida**, no método
`notificar_fim_de_partida`. O algoritmo é **diferença temporal
(TD)** com propagação reversa.

**Passo 1 — Determina a recompensa final.**

```python
if resultado == 0:
    recompensa_final = RECOMPENSA_EMPATE   # 1.0
elif resultado == simbolo_inteligente:
    recompensa_final = RECOMPENSA_VITORIA  # 2.0
else:
    recompensa_final = RECOMPENSA_DERROTA  # -1.0
```

- **Vitória** do inteligente → `+2.0`.
- **Empate** → `+1.0`.
- **Derrota** → `-1.0`.

Esses três números **expressam a preferência**:
`vitória > empate > derrota`, com **derrota fortemente
penalizada**. A escolha específica (`2, 1, -1`) foi calibrada para:

- Fazer o agente **evitar perder** com prioridade.
- Fazer o agente **preferir vencer**, mas **aceitar empate** como
  resultado bom.
- Não deixar o agente **covarde** (empate = vitória) nem
  **kamikaze** (derrota = vitória).

**Passo 2 — Propaga a recompensa de trás para frente.**

```python
valor_futuro = recompensa_final
for chave in reversed(self._jogadas_da_partida):
    pontuacao, visitas = self.tabela.get(chave, (0.0, 0))
    alvo = valor_futuro
    pontuacao_nova = pontuacao + self.TAXA_APRENDIZADO * (alvo - pontuacao)
    visitas_novas = visitas + 1
    self.tabela[chave] = (pontuacao_nova, visitas_novas)
    valor_futuro = pontuacao_nova
```

A **última jogada** recebe a recompensa final diretamente. A
**penúltima** recebe o valor atualizado da última. E assim por
diante, até a primeira jogada. Isso faz com que **jogadas que
levaram ao resultado final sejam reforçadas**, e jogadas que
levaram a derrota sejam penalizadas.

**Por que do último para o primeiro, e não o contrário?**

A recompensa é conhecida **só no final**. Se propagássemos do
primeiro para o último, não saberíamos o alvo. Fazendo de trás
para frente, o valor "flui" naturalmente: o último estado é o único
que tem uma recompensa **direta**; os anteriores herdam o valor
**propagado**.

**Passo 3 — Persiste no disco e limpa o buffer da partida.**

A persistência é **append em JSONL**: cada chave alterada é gravada
como uma linha nova. Ao carregar o arquivo, a **última linha de
cada chave vence** — é assim que o conhecimento acumula entre
execuções.

### 4.3. Como armazena

A tabela é um dicionário em memória, com chave e valor:

```
chave  = (estado_do_tabuleiro, casa, simbolo)
valor  = (pontuacao, visitas)
```

- **`estado_do_tabuleiro`**: tupla de 9 posições, com valores
  `1` (X), `-1` (O) ou `0` (vazio).
- **`casa`**: índice da jogada escolhida (0 a 8).
- **`simbolo`**: quem jogou (`1` ou `-1`).
- **`pontuacao`**: valor estimado da jogada naquele estado, para
  aquele jogador. Float.
- **`visitas`**: quantas vezes essa chave foi jogada. Int.

O arquivo `conhecimento.jsonl` guarda o **estado atual da tabela**.
Cada linha é um registro:

```json
{"e":[0,0,0,0,1,0,0,0,0],"j":4,"s":1,"p":1.842,"v":12}
```

Significado: no estado `[0,0,0,0,1,0,0,0,0]`, o jogador `X` (s=1)
jogou na casa 4 doze vezes, e a pontuação estimada dessa jogada é
1.842.

### 4.4. Parâmetros

Todos ficam como atributos de classe, ajustáveis no topo do código:

```python
class JogadorInteligente(Jogador):
    TAXA_APRENDIZADO = 0.3
    RECOMPENSA_VITORIA = 2.0
    RECOMPENSA_DERROTA = -1.0
    RECOMPENSA_EMPATE = 1.0
```

#### `TAXA_APRENDIZADO` (α)

**O que faz**: controla quanto a pontuação de uma jogada se ajusta
a cada partida. A fórmula é:

```
pontuacao_nova = pontuacao + α × (alvo − pontuacao)
```

**Efeito de valores diferentes**:

- **α próximo de 0** (ex: 0.01): aprendizado **lento**, mas
  **muito estável**. A pontuação muda pouco a cada partida. Bom
  quando se quer convergência cuidadosa.
- **α próximo de 1** (ex: 0.9): aprendizado **rápido**, mas
  **instável**. A pontuação pula para o alvo quase direto, então
  sofre com o ruído das partidas individuais.
- **α = 0.3** (valor atual): equilíbrio. Move 30% do caminho até
  o alvo a cada partida.

**Quando ajustar**:

- Se o aprendizado está **oscilando demais**, baixe (ex: 0.1).
- Se o aprendizado está **demorando demais** para convergir,
  aumente (ex: 0.5).

**Exemplo numérico**: suponha `pontuacao = 0.5`, `alvo = 2.0`,
`α = 0.3`:

```
pontuacao_nova = 0.5 + 0.3 × (2.0 − 0.5)
               = 0.5 + 0.3 × 1.5
               = 0.5 + 0.45
               = 0.95
```

A pontuação subiu de 0.5 para 0.95 — 30% do caminho até 2.0. Numa
próxima partida com o mesmo alvo, subiria mais um pouco, e assim
por diante, aproximando-se de 2.0 gradualmente.

#### `RECOMPENSA_VITORIA`

**O que faz**: define o valor final quando o inteligente vence.

**Efeito de valores diferentes**:

- **Maior** (ex: 5.0): o agente fica **mais agressivo** — arrisca
  mais em busca de vitória, aceita mais derrota em troca.
- **Menor** (ex: 1.0): o agente fica **mais conservador** — prefere
  empate garantido a vitória incerta.

**Valor atual (2.0)**: equilibrado. Prefere vitória, mas não a ponto
de arriscar perder sempre.

#### `RECOMPENSA_EMPATE`

**O que faz**: define o valor final quando o jogo empata.

**Efeito de valores diferentes**:

- **Positivo** (1.0): o agente **valoriza empate**. Aprende a
  preferir empate garantido a tentar arriscar por vitória.
- **Zero**: o agente é **indiferente** entre empate e estados
  desconhecidos. Aprende a não perder, mas também não evita
  empates "por inércia".
- **Negativo**: o agente **odeia empatar**. Fica agressivo demais —
  arrisca perder para evitar empate. **Não use.**

**Valor atual (1.0)**: empate vale metade de uma vitória (2.0) e é
positivo. Isso faz o agente **buscar ativamente o empate** quando
não pode vencer, o que é exatamente o objetivo do projeto.

#### `RECOMPENSA_DERROTA`

**O que faz**: define o valor final quando o inteligente perde.

**Efeito de valores diferentes**:

- **Mais negativo** (ex: -5.0): o agente fica **paranoico** —
  evita qualquer risco, joga defensivamente, aceita empate sempre.
- **Menos negativo** (ex: -0.5): o agente fica **relapso** — aceita
  derrota por vitória ocasional.

**Valor atual (-1.0)**: fortemente negativo, mas não paranoico.
Faz o agente **evitar derrota com prioridade**, sem virar covarde.

### 4.5. Por que essa configuração de recompensas

Vamos ver o **raciocínio** por trás da configuração atual
(`2.0, 1.0, -1.0`).

**Objetivo declarado**: *"nunca perder, empate é bom, vitória é
melhor ainda"*.

**Traduzindo para recompensas**:

- **"vitória é melhor ainda"** →
  `RECOMPENSA_VITORIA > RECOMPENSA_EMPATE`.
- **"empate é bom"** → `RECOMPENSA_EMPATE > 0`.
- **"nunca perder"** → `RECOMPENSA_DERROTA << 0`, e a diferença
  empate − derrota deve ser grande.

**A configuração (2, 1, -1)** satisfaz:

- `2 > 1` → vitória > empate. ✔
- `1 > 0` → empate é bom. ✔
- `1 − (−1) = 2` → a distância empate→derrota é 2× a distância
  vitória→empate. Ou seja, **evitar derrota é mais importante que
  buscar vitória**. ✔

**Alternativas testadas e por que foram rejeitadas**:

| Configuração | Efeito | Problema |
|---|---|---|
| `(1, 0, -1)` | Empate neutro | Empate não é "bom", é "nada" — não atende ao objetivo |
| `(1, 1, -1)` | Empate = vitória | Agente fica indiferente entre vencer e empatar — perde oportunidade de vencer quando dá |
| `(1, 0.5, -1)` | Empate vale metade | A distância empate→derrota é 3× a de vitória→empate — agente fica covarde |
| `(2, 1, -1)` | **Equilibrado** | **Escolhido** |
| `(3, 1, -1)` | Vitória muito valorizada | Agente arrisca demais, perde mais |

### 4.6. O que o agente aprende, na prática

Depois de treinado, o Q-table converge para uma política que:

- **Nunca perde** contra o ingênuo (a não ser por exploração
  residual — <1%).
- **Empata ~100%** contra o especialista (não vence porque o
  especialista não erra).
- **Vence quando o adversário dá espaço** — tipicamente 30–60% das
  partidas contra o ingênuo.

O agente **não vence 100%** porque o ingênuo, por sorte, às vezes
monta defesas que evitam vitória. Isso é o **teto do jogo** contra
aleatório — não é limitação do agente.

---

## 5. Como os três se relacionam

### Matriz de partidas recomendada

Para caracterizar completamente o comportamento dos agentes, rode a
matriz:

| X \ O | Ingênuo | Especialista | Inteligente |
|---|---|---|---|
| **Ingênuo** | linha base | especialista domina | inteligente domina |
| **Especialista** | especialista domina | 100% empates | ~100% empates |
| **Inteligente** | inteligente domina | ~100% empates | 100% empates |

### O que cada célula revela

- **Ingênuo vs Ingênuo**: piso do jogo — qual é a distribuição sem
  nenhuma estratégia?
- **Especialista vs Ingênuo**: teto humano. Um agente heurístico
  bom vence aleatório com que frequência?
- **Inteligente vs Especialista**: teto do jogo. Dois agentes que
  jogam bem empatam com que frequência?
- **Inteligente vs Inteligente**: consistência. Dois aprendizes
  convergem para o mesmo resultado?

### Como usar essa matriz para avaliar

- Se o **inteligente** vence o ingênuo **tão bem quanto** o
  especialista, ele aprendeu.
- Se o **inteligente** empata **quase 100%** contra o especialista,
  ele generalizou (não apenas decorou o ingênuo).
- Se dois **inteligentes** empatam 100% entre si, o aprendizado é
  **consistente**.

---

## 6. Como executar combinações diferentes

Basta editar as duas variáveis no topo do arquivo:

```python
AGENTE_X = "especialista"
AGENTE_O = "inteligente"
```

Valores válidos: `"ingenuo"`, `"especialista"`, `"inteligente"`.

O nome do arquivo de resultado é montado automaticamente:

```
resultado_especialista_vs_inteligente.txt
```

O analisador extrai os nomes **do próprio nome do arquivo**, e usa
nos títulos dos gráficos e no resumo. Não precisa mudar nada nele.

### Sobre `REMOVER_ARQUIVOS_ANTIGOS`

```python
REMOVER_ARQUIVOS_ANTIGOS = True
```

- **`True`**: apaga `resultado_*.txt` e `conhecimento.jsonl` antes
  de rodar. Use quando quiser **começar o treino do zero**.
- **`False`**: mantém os arquivos. Use quando quiser **continuar o
  treino** de onde parou, acumulando o conhecimento entre sessões.

**Cuidado**: apagar `conhecimento.jsonl` joga fora **todo** o
aprendizado acumulado. Use `True` só quando quiser um recomeço
limpo.

---

## 7. Resumo em uma tabela

| Aspecto | Ingênuo | Especialista | Inteligente |
|---|---|---|---|
| **Decisão** | Aleatória | Cascata de regras | Maior pontuação na tabela |
| **Memória** | Nenhuma | Nenhuma | Tabela persistida em JSONL |
| **Aprendizado** | Não | Não | Sim, por diferença temporal |
| **Determinístico** | Não | Sim | Sim após convergir |
| **Parâmetros ajustáveis** | Nenhum | Nenhum | Taxa de aprendizado e recompensas |
| **Convergência** | N/A | N/A | ~100k partidas |
| **Uso principal** | Adversário de referência | Adversário forte, teto humano | Objeto de estudo do aprendizado |

---

## 8. Onde olhar para entender o aprendizado

Depois de rodar um treino do inteligente:

- **`conhecimento.jsonl`** — o "cérebro" do agente, em texto puro.
  Você pode abrir, ver as chaves, ordenar por pontuação.
- **`resultado_*.txt`** — o histórico bruto das partidas.
- **`resultados/resultado_*/`** — todos os gráficos e resumos
  gerados pelo analisador. Consulte o `LEIA-ME.md` para saber o que
  cada gráfico significa.

O `conhecimento.jsonl` é o artefato mais interessante para inspeção
manual. Por exemplo, você pode rodar um pequeno script Python para
listar as chaves com maior pontuação:

```python
import json
from collections import defaultdict

por_estado = defaultdict(list)
with open("conhecimento.jsonl") as f:
    for linha in f:
        r = json.loads(linha)
        por_estado[tuple(r["e"])].append((r["j"], r["s"], r["p"], r["v"]))

# Exibe as jogadas preferidas do agente em alguns estados
for estado, jogadas in list(por_estado.items())[:5]:
    print("Estado:", estado)
    for j, s, p, v in sorted(jogadas, key=lambda x: -x[2]):
        print(f"  casa {j}, símbolo {s}: pontuação={p:.3f}, visitas={v}")
```

Isso mostra, para cada estado visitado, **qual jogada o agente
prefere** e **quanto ele já testou aquela jogada**. É o retrato
direto do que ele aprendeu.

### Interpretando a pontuação

O sinal da pontuação diz muito:

- **`p > 0`**: o agente acredita que essa jogada leva a um
  resultado **bom** (vitória ou empate).
- **`p = 0`**: o agente **não sabe** — pode ser uma chave nova, ou
  uma chave cujo histórico foi neutro.
- **`p < 0`**: o agente acredita que essa jogada leva a um
  resultado **ruim** (derrota).

### Interpretando as visitas

- **`v` baixo** (1–5): a pontuação é **ruidosa**. Foram poucas
  amostras, e a estimativa pode estar longe da verdade.
- **`v` alto** (50+): a pontuação é **confiável**. Convergiu.

### Ordenação útil

Para ver os estados onde o agente tem **mais confiança**, filtre
por `v >= 50` e ordene por `|p|` decrescente. Esses são os estados
onde a política do agente está mais bem estabelecida.

Para ver os estados onde o agente **ainda está incerto**, filtre
por `v <= 3`. Esses são os estados que aparecem raramente nas
partidas, e onde a exploração continua acontecendo.

---

## 9. Observações finais

### Sobre o determinismo

O `JogadorInteligente` é **determinístico após convergir**. Isso
significa que, dado o mesmo estado, ele sempre escolhe a mesma
jogada. Não há aleatoriedade na decisão final — a única fonte de
variação é o **desempate por menor número de visitas**, que é
determinístico também.

O `JogadorIngenuo` é **não-determinístico** — usa `random.choice`.
Isso significa que duas execuções com o mesmo ingênuo produzem
resultados diferentes.

O `JogadorEspecialista` é **totalmente determinístico**.

### Sobre a reprodutibilidade

Se você quiser **reproduzir** exatamente uma sequência de partidas,
use uma **semente fixa**:

```python
import random
random.seed(42)
```

Coloque isso no início do `main`. O `random.choice` do ingênuo vai
produzir a mesma sequência toda vez.

### Sobre o custo de memória

O `conhecimento.jsonl` cresce com o número de chaves **únicas**
visitadas. No jogo da velha, o espaço total de estados é de
**~5.478 posições legais**. Cada estado tem 9 casas possíveis e 2
símbolos, então o número máximo de chaves distintas é da ordem de
`5478 × 9 × 2 ≈ 100.000`.

Na prática, o número de chaves visitadas fica **abaixo de 50.000**
para um treino típico. Isso significa que o arquivo final tem
alguns milhares de linhas — não é grande.

### Sobre o crescimento do arquivo

O arquivo é **append-only**, então ele cresce linearmente com o
número de **partidas**, não com o número de chaves. Se você rodar
1 milhão de partidas, o arquivo terá **milhões de linhas**
(uma por chave alterada em cada partida).

Para manter o arquivo gerenciável, você pode:

- **Apagar e recomeçar** com `REMOVER_ARQUIVOS_ANTIGOS = True`.
- **Consolidar periodicamente**: ler o arquivo, manter apenas a
  última linha de cada chave, gravar de volta. Isso reduz o arquivo
  ao número de chaves únicas.