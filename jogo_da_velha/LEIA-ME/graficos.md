# Guia dos Gráficos — Analisador de Resultados

Este documento explica **para que serve cada gráfico** gerado pelo
`analise_resultados.py`, **como ler** e **o que observar**.

Os gráficos são gerados automaticamente dentro da pasta `resultados/`,
em uma subpasta com o nome do arquivo de resultados (ex:
`resultados/resultado_ingenuo_vs_inteligente/`).

---

## Visão geral

Cada pasta de resultados contém:

- Um **resumo em texto** (`resumo.txt`) com os números finais.
- Dois **CSVs** com os dados brutos por recorte.
- Um **TXT formatado** (`recortes.txt`) com as tabelas legíveis.
- **Sete gráficos** organizados em duas famílias:
  - **Séries temporais contínuas** (acumuladas ao longo de todas as partidas).
  - **Gráficos de recorte** (por janelas e por cortes).

---

## Ordem recomendada de leitura

Quando abrir uma pasta nova de resultados, olhe **nesta ordem**:

1. `resumo.txt` — o retrato geral. Se as taxas finais já estão boas, siga.
2. `grafico_inteligente.png` — a prova de que o agente aprendeu.
3. `recortes_nao_derrota_janela.png` — **quando** ele aprendeu.
4. `recortes_taxas_janela.png` — **como** ele mudou de comportamento.
5. `grafico_acumulado_percentual.png` — confirmação de convergência.

Os demais gráficos são complementares — use quando precisar defender um
ponto específico ou investigar um comportamento estranho.

---

## 1. `grafico_acumulado_absoluto.png`

### O que mostra

Três linhas contínuas ao longo de todas as partidas:

- **Vitórias de X acumuladas** (azul).
- **Vitórias de O acumuladas** (vermelho).
- **Empates acumulados** (verde).

Cada ponto no eixo X mostra o **total acumulado até ali**, do início
até aquela partida.

### Para que serve

Ver a dinâmica geral ao longo do tempo. Como as linhas só sobem, a
**inclinação** de cada linha mostra quantas partidas daquele tipo
aconteceram naquele trecho.

### Como ler

- Linha subindo rápido → muitas partidas daquele tipo no período.
- Linha subindo devagar → poucas partidas daquele tipo.
- Linha quase horizontal → praticamente nenhuma partida daquele tipo.

### O que observar

- No início, as três linhas sobem em ritmos diferentes (exploração).
- No meio, a linha mais inclinada é o resultado mais comum.
- No final, a inclinação se estabiliza — reflete a política convergida.

**Útil para**: ver quando o comportamento do jogo muda. Um "joelho"
numa curva indica mudança de regime.

---

## 2. `grafico_acumulado_percentual.png`

### O que mostra

As mesmas três categorias, mas em **porcentagem acumulada**. Cada ponto
é "de todas as partidas até aqui, qual % foi vitória de X / vitória de O
/ empate".

### Para que serve

Ver convergência. É o gráfico que responde: **"o agente parou de mudar
de comportamento?"**.

### Como ler

- Linhas oscilando muito no início → ainda está descobrindo o que funciona.
- Linhas convergindo para valores estáveis → estabilizou.
- Uma linha se aproximando de 100% → o resultado é dominante.

### O que observar

- **Contra o ingênuo**: verde (empates) ou vermelha (vitórias do inteligente)
  subindo, azul (vitórias do ingênuo) caindo.
- **Contra o especialista**: verde subindo para perto de 100%.
- **Auto-jogo**: verde chegando perto de 100%.

**Útil para**: confirmar que o aprendizado parou de mudar. Se as curvas
ainda estão inclinadas no final, mais treino ajuda.

---

## 3. `grafico_inteligente.png`

### O que mostra

Três linhas acumuladas, específicas para o jogador inteligente:

- **Não-derrota do inteligente** (verde) — vitória + empate.
- **Vitória do inteligente** (azul tracejada).
- **Empate** (laranja pontilhada).

Se o inteligente é J2 (O), a "vitória" é `vitoria_o`. Se é J1 (X),
é `vitoria_x`. O código detecta automaticamente.

### Para que serve

**O gráfico mais importante para o objetivo de "nunca perder".**
A linha verde é literalmente "o quanto o agente está evitando perder".
Se ela chega a 100%, ele é imbatível.

### Como ler

- Verde subindo → o agente está aprendendo a não perder.
- Verde estabilizando em 100% → política perfeita.
- Verde estabilizando abaixo de 100% → ainda há derrotas residuais.
- Azul e laranja se dividindo → o agente prefere empatar ou arriscar.

### O que observar

- **Verde muito próximo de 100%** → sucesso. O agente atinge o teto.
- **Verde abaixo de 90%** → problema. Mais treino, ou recompensa mal
  calibrada.

**Útil para**: colocar no relatório quando quiser dizer *"meu agente
aprendeu a não perder"*.

---

## 4. `recortes_taxas_janela.png`

### O que mostra

Três linhas (VitX%, VitO%, Emp%), com **um ponto por janela**, cada
ponto com o **valor anotado**. Eixo X rotulado como `0-5k`, `5k-10k`,
`10k-25k`, etc.

### Para que serve

Ver o desempenho em cada fase, isoladamente. Em vez de uma média
acumulada que dilui tudo, cada ponto é "de 5k a 10k, quais foram as
taxas?".

### Como ler

- **Ponto no eixo X** = a janela (leia o rótulo).
- **Valor em cima do ponto** = a taxa exata naquela janela.
- **Y** = % dentro daquela janela.

### O que observar

- Curvas oscilando muito entre janelas → comportamento instável.
- Curvas suavizando com o tempo → convergência.
- Uma janela específica com valores muito diferentes → outlier.

**Útil para**: identificar **quando** o agente aprendeu. Um "salto"
numa janela específica indica o ponto onde ele descobriu a política boa.

---

## 5. `recortes_nao_derrota_janela.png`

### O que mostra

Duas linhas: NãoDerrota X% e NãoDerrota O% **por janela**, com valores
anotados.

### Para que serve

Ver o aprendizado do ponto de vista do objetivo "não perder". É o
irmão do `grafico_inteligente.png`, mas por janela em vez de acumulado.

### Como ler

- Linha subindo entre janelas → o agente está aprendendo a não perder.
- Linha estabilizando em 100% → política perfeita.
- Linha caindo em alguma janela → regressão naquele trecho.

### O que observar

- Se a linha do **seu agente** sobe ao longo das janelas, ele está
  aprendendo.
- Se a linha do **adversário** cai, é a mesma coisa vista do outro lado.

**Útil para**: saber **em que fase** o agente atingiu o teto.

---

## 6. `recortes_taxas_acumulado.png`

### O que mostra

As mesmas três taxas, mas **acumuladas até cada corte**. Eixo X:
número absoluto da partida (`100`, `500`, `1000`, `5000`, ...).

### Para que serve

Comparar com o `recortes_taxas_janela.png`. O acumulado é uma média de
tudo até ali; a janela é só o trecho. Juntos, mostram **duas visões do
mesmo fenômeno**.

### Como ler

- Igual ao `grafico_acumulado_percentual.png`, mas restrito aos cortes
  de recorte, com valores anotados.

### O que observar

- Acumulado continua subindo, janela já estabilizou → **já convergiu**,
  e o acumulado só está arrastando o início ruim.
- Ambos sobem → **ainda está aprendendo**.

**Útil para**: comparar "média geral" com "desempenho atual".

---

## 7. `recortes_nao_derrota_acumulado.png`

### O que mostra

NãoDerrota X% e NãoDerrota O% **acumuladas** até cada corte, com
valores anotados.

### Para que serve

Ver a convergência da "não-derrota" de forma acumulada. Complementa o
`recortes_nao_derrota_janela.png`.

### Como ler

- Subindo → o agente está acumulando não-derrotas.
- Estabilizando em 100% → política perfeita.

**Útil para**: mostrar que, ao longo de todo o treino, a tendência da
não-derrota foi consistentemente de alta.

---

## Tabela resumo

| Gráfico | Tipo | Pergunta que responde |
|---|---|---|
| `grafico_acumulado_absoluto` | Contagem acumulada | Quando o jogo mudou de comportamento? |
| `grafico_acumulado_percentual` | % acumulada | O agente convergiu? |
| `grafico_inteligente` | % acumulada (foco) | O inteligente está evitando perder? |
| `recortes_taxas_janela` | % por janela | Como o comportamento mudou entre fases? |
| `recortes_nao_derrota_janela` | % por janela | Em que fase o agente atingiu o teto? |
| `recortes_taxas_acumulado` | % acumulada por corte | Como as taxas médias evoluíram? |
| `recortes_nao_derrota_acumulado` | % acumulada por corte | A tendência geral da não-derrota é consistente? |

---

## Regra prática

- **Está funcionando?** → `resumo.txt` + `grafico_inteligente.png`.
- **Quando aprendeu?** → `recortes_nao_derrota_janela.png`.
- **Ainda está aprendendo?** → compare `recortes_taxas_janela.png` com
  `recortes_taxas_acumulado.png`. Se a janela estabilizou e o acumulado
  continua subindo, convergiu.
- **O comportamento é estável?** → `recortes_taxas_janela.png`. Muita
  oscilação entre janelas = instável.

---

## Legenda de siglas

- **VitX%** — % de vitórias do jogador X.
- **VitO%** — % de vitórias do jogador O.
- **Emp%**  — % de empates.
- **NDerX%** — Não-derrota de X (VitX% + Emp%).
- **NDerO%** — Não-derrota de O (VitO% + Emp%).
- **N** — número de partidas no bloco (janela ou corte).