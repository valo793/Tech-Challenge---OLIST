# Olist Dashboard

> Documentação detalhada do report Power BI, separada do `README.md` raiz para deixar o repositório mais organizado.

## DAX usada no report atual

Este documento foi refeito a partir do `Olist Dashboard.pbix` atual e considera apenas os objetos DAX efetivamente usados no dashboard.

Além de registrar o cálculo de cada objeto, a documentação também explica a intenção analítica por trás da modelagem, isto é, por que cada DAX foi construída dessa forma dentro do report.

Resumo do escopo:

- `51` measures usadas diretamente em visuais
- `13` measures auxiliares chamadas por essas measures
- `8` colunas calculadas DAX usadas no report
- `4` tabelas calculadas DAX usadas no report
- fórmulas completas por extenso em `DAX_FORMULAS.md`

## Convenções

- O inventário abaixo exclui `LocalDateTable_*` automáticas do Power BI porque elas não alimentam os visuais atuais.
- Alguns visuais exibem aliases diferentes do nome real da measure no modelo.
- O inventário inclui measures usadas em texto dinâmico de visuais, como `Insight Simulação` no `actionButton` da página de forecast.
- Aliases identificados: `Clientes Recorrentes` = `Clientes com Recompra por Categoria`; `Itens Vendidos Clientes Recorrentes` = `Itens Vendidos Clientes Recorrentes (Período)`; `Rank Detrator Seller` = `Rank Atraso Seller`; `Estrelas nota média` = `Estrelas Nota Média`; `Receita Histórica` = `Receita Histórica Exibida`.

## Measures DAX usadas diretamente nos visuais

### Página `Ganhos e Crescimento`

- `Crescimento Receita % Card`: páginas `Ganhos e Crescimento`. Regra: compara a receita do último mês visível com a do mês imediatamente anterior, usando a receita recalculada pela data de entrega. Dependências: `Receita Último Mês`, `Receita Mês Anterior Card`.
- `Parcelas Médias`: páginas `Ganhos e Crescimento`. Regra: calcula a média de parcelas das transações visíveis no contexto atual. Dependências: nenhuma.
- `Pedidos`: páginas `Ganhos e Crescimento`, `Logistica e Satisfação`. Regra: conta pedidos distintos visíveis no contexto atual. Dependências: nenhuma.
- `Receita Produtos (Data Entrega)`: páginas `Ganhos e Crescimento`, `Clientes e Produtos`. Regra: recalcula a receita usando a relação entre `Orders[DateId_Delivered_Customer]` e `Calendario[DateId]`, deslocando o contexto para a data de entrega. Dependências: `Receita Produtos`.
- `Receita Último Mês`: páginas `Ganhos e Crescimento`. Regra: calcula a receita do último mês visível construindo o intervalo entre o primeiro e o último dia do mês corrente. Dependências: `Receita Produtos (Data Entrega)`.
- `Ticket Médio`: páginas `Ganhos e Crescimento`. Regra: divide a receita de produtos pela quantidade de pedidos para obter o ticket médio. Dependências: `Receita Produtos`, `Pedidos`.

### Página `Logistica e Satisfação`

- `% Impacto Atraso`: páginas `Logistica e Satisfação`. Regra: mede a perda relativa de nota entre pedidos no prazo e pedidos atrasados, usando a diferença entre as notas médias dividida pela nota dos pedidos no prazo. Dependências: `Nota Média Pedidos no Prazo`, `Nota Média Pedidos Atrasados`.
- `% Pedidos Atrasados`: páginas `Logistica e Satisfação`, `Forecast e Simulação`. Regra: divide `Pedidos Atrasados` por `Pedidos Entregues` para expressar a métrica em percentual. Dependências: `Pedidos Atrasados`, `Pedidos Entregues`.
- `% Pedidos Atrasados por Seller`: páginas `Logistica e Satisfação`. Regra: divide `Pedidos Atrasados por Seller` por `Pedidos por Seller` para expressar a métrica em percentual. Dependências: `Pedidos Atrasados por Seller`, `Pedidos por Seller`.
- `% Pedidos no Prazo`: páginas `Logistica e Satisfação`. Regra: divide `Pedidos no Prazo` por `Pedidos Entregues` para expressar a métrica em percentual. Dependências: `Pedidos no Prazo`, `Pedidos Entregues`.
- `% Reviews Negativas`: páginas `Logistica e Satisfação`. Regra: divide a quantidade de pedidos avaliados com `review_score < 4` pelo total de pedidos avaliados no contexto. Dependências: nenhuma.
- `Atraso Médio Entrega`: páginas `Logistica e Satisfação`. Regra: calcula a média de dias de atraso entre a data estimada e a data efetiva de entrega, convertendo entregas no prazo ou adiantadas em `0`. Dependências: nenhuma.
- `Estrelas Nota Média`: páginas `Logistica e Satisfação`. Alias no visual: `Estrelas nota média`. Regra: converte `Nota Média` em 0 a 5 estrelas inteiras, truncando casas decimais com `INT` e completando o restante com estrelas vazias. Dependências: `Nota Média`.
- `Estrelas Nota Média Pedidos Atrasados`: páginas `Logistica e Satisfação`. Regra: converte `Nota Média Pedidos Atrasados` em 0 a 5 estrelas inteiras, truncando casas decimais com `INT` e completando o restante com estrelas vazias. Dependências: `Nota Média Pedidos Atrasados`.
- `Estrelas Nota Média Pedidos no Prazo`: páginas `Logistica e Satisfação`. Regra: converte `Nota Média Pedidos no Prazo` em 0 a 5 estrelas inteiras, truncando casas decimais com `INT` e completando o restante com estrelas vazias. Dependências: `Nota Média Pedidos no Prazo`.
- `Lead Time Aprovação até Entrega Transportadora (dias)`: páginas `Logistica e Satisfação`. Regra: calcula a média de dias entre aprovação e entrega à transportadora para pedidos com ambas as datas preenchidas. Dependências: nenhuma.
- `Lead Time Compra até Aprovação (dias)`: páginas `Logistica e Satisfação`. Regra: calcula a média de dias entre compra e aprovação para pedidos com ambas as datas preenchidas. Dependências: nenhuma.
- `Lead Time Compra até Entrega (dias)`: páginas `Logistica e Satisfação`. Regra: calcula a média de dias entre compra e entrega ao cliente apenas para pedidos `delivered` com ambas as datas preenchidas. Dependências: nenhuma.
- `Lead Time Transportadora até Entrega Cliente (dias)`: páginas `Logistica e Satisfação`. Regra: calcula a média de dias entre entrega à transportadora e entrega ao cliente para pedidos com ambas as datas preenchidas. Dependências: nenhuma.
- `Nota Média`: páginas `Logistica e Satisfação`. Regra: calcula a média da nota média de review por pedido no contexto atual, iterando `Orders[order_id]`. Dependências: nenhuma.
- `Nota Média Pedidos Atrasados`: páginas `Logistica e Satisfação`. Regra: reaplica `Nota Média` apenas sobre pedidos `delivered` entregues depois da data estimada. Dependências: `Nota Média`.
- `Nota Média Pedidos Atrasados por Seller`: páginas `Logistica e Satisfação`. Regra: reaplica `Nota Média por Seller` apenas sobre pedidos `delivered` atrasados do seller no contexto atual. Dependências: `Nota Média por Seller`.
- `Nota Média Pedidos no Prazo`: páginas `Logistica e Satisfação`. Regra: reaplica `Nota Média` apenas sobre pedidos `delivered` entregues até a data estimada. Dependências: `Nota Média`.
- `Nota Média por Seller`: páginas `Logistica e Satisfação`. Regra: calcula a média das notas dos pedidos do seller usando o conjunto de `order_id` visível em `Order Items` e `TREATAS` para levar esse conjunto a `Order Reviews`. Dependências: nenhuma.
- `Pedidos`: páginas `Ganhos e Crescimento`, `Logistica e Satisfação`. Regra: conta pedidos distintos visíveis no contexto atual. Dependências: nenhuma.
- `Pedidos Atrasados`: páginas `Logistica e Satisfação`. Regra: conta pedidos distintos `delivered` cuja entrega ao cliente ocorreu após a data estimada. Dependências: nenhuma.
- `Pedidos no Prazo`: páginas `Logistica e Satisfação`. Regra: conta pedidos distintos `delivered` cuja entrega ao cliente ocorreu até a data estimada. Dependências: nenhuma.
- `Pedidos por Seller`: páginas `Logistica e Satisfação`. Regra: conta pedidos distintos do seller no contexto atual a partir do conjunto de `order_id` visível em `Order Items`. Dependências: nenhuma.
- `Rank Atraso Seller`: páginas `Logistica e Satisfação`. Alias no visual: `Rank Detrator Seller`. Regra: ranqueia apenas sellers com `Score Atraso Seller` positivo dentro do contexto selecionado usando `RANKX` sobre `ALLSELECTED('Sellers'[Seller_Alias])`. Dependências: `Score Atraso Seller`.

### Página `Clientes e Produtos`

- `% Clientes com Recompra`: páginas `Clientes e Produtos`, `Forecast e Simulação`. Regra: divide `Clientes com Recompra por Categoria` por `Clientes Únicos` para expressar a métrica em percentual. Dependências: `Clientes com Recompra por Categoria`, `Clientes Únicos`.
- `Clientes com Recompra por Categoria`: páginas `Clientes e Produtos`. Alias no visual: `Clientes Recorrentes`. Regra: conta clientes que já haviam comprado antes do mês corrente e voltaram a comprar no mês atual dentro da categoria e do contexto visível. Dependências: nenhuma.
- `Clientes Novos`: páginas `Clientes e Produtos`. Regra: conta clientes cuja primeira compra histórica caiu dentro do mês corrente do contexto. Dependências: nenhuma.
- `Clientes Únicos`: páginas `Clientes e Produtos`. Regra: conta clientes únicos no contexto atual usando a chave `customer_unique_id`. Dependências: nenhuma.
- `Frequência Média de Compra`: páginas `Clientes e Produtos`. Regra: mede a frequência média de compra do cliente dentro da janela analisada. Dependências: nenhuma.
- `Itens Vendidos`: páginas `Clientes e Produtos`. Regra: conta linhas da tabela de itens para representar o volume de itens vendidos. Dependências: nenhuma.
- `Itens Vendidos Clientes Recorrentes (Período)`: páginas `Clientes e Produtos`. Alias no visual: `Itens Vendidos Clientes Recorrentes`. Regra: conta itens vendidos para clientes que têm pelo menos dois pedidos distintos no contexto, removendo o filtro de `Products` na identificação da recorrência. Dependências: nenhuma.
- `Receita 3 Meses Anteriores`: páginas `Clientes e Produtos`. Regra: soma a receita da janela imediatamente anterior de três meses para comparar com a janela atual. Dependências: `Receita Produtos`.
- `Receita Produtos (Data Entrega)`: páginas `Ganhos e Crescimento`, `Clientes e Produtos`. Regra: recalcula a receita usando a relação entre `Orders[DateId_Delivered_Customer]` e `Calendario[DateId]`, deslocando o contexto para a data de entrega. Dependências: `Receita Produtos`.
- `Receita Últimos 3 Meses`: páginas `Clientes e Produtos`. Regra: soma a receita dos três meses mais recentes dentro do contexto temporal visível. Dependências: `Receita Produtos`.
- `Tendência Receita %`: páginas `Clientes e Produtos`. Regra: compara a receita dos últimos 3 meses com a janela imediatamente anterior de 3 meses. Dependências: `Receita Últimos 3 Meses`, `Receita 3 Meses Anteriores`.
- `Top 1 Receita`: páginas `Clientes e Produtos`. Regra: monta um ranking composto pela soma das posições em receita, pedidos e itens, e retorna a receita formatada do seller em 1º lugar. Dependências: nenhuma.
- `Top 1 Seller`: páginas `Clientes e Produtos`. Regra: monta um ranking composto pela soma das posições em receita, pedidos e itens, e retorna o alias do seller em 1º lugar. Dependências: nenhuma.
- `Top 2 Receita`: páginas `Clientes e Produtos`. Regra: monta o mesmo ranking composto e retorna a receita formatada do seller em 2º lugar. Dependências: nenhuma.
- `Top 2 Seller`: páginas `Clientes e Produtos`. Regra: monta o mesmo ranking composto e retorna o alias do seller em 2º lugar. Dependências: nenhuma.
- `Top 3 Receita`: páginas `Clientes e Produtos`. Regra: monta o mesmo ranking composto e retorna a receita formatada do seller em 3º lugar. Dependências: nenhuma.
- `Top 3 Seller`: páginas `Clientes e Produtos`. Regra: monta o mesmo ranking composto e retorna o alias do seller em 3º lugar. Dependências: nenhuma.

### Página `Forecast e Simulação`

- `% Clientes com Recompra`: páginas `Clientes e Produtos`, `Forecast e Simulação`. Regra: divide `Clientes com Recompra por Categoria` por `Clientes Únicos` para expressar a métrica em percentual. Dependências: `Clientes com Recompra por Categoria`, `Clientes Únicos`.
- `% Pedidos Atrasados`: páginas `Logistica e Satisfação`, `Forecast e Simulação`. Regra: divide `Pedidos Atrasados` por `Pedidos Entregues` para expressar a métrica em percentual. Dependências: `Pedidos Atrasados`, `Pedidos Entregues`.
- `% Receita Sellers Estratégicos`: páginas `Forecast e Simulação`. Regra: divide a receita dos sellers estratégicos pelo total de receita removendo filtros de seller do denominador. Dependências: `Receita Sellers Estratégicos`, `Receita Produtos`.
- `Ganho Projetado %`: páginas `Forecast e Simulação`. Regra: divide o ganho absoluto projetado pela receita baseline dos três meses futuros para transformar o cenário em percentual. Dependências: `Ganho Projetado 3 Meses`, `Receita Baseline 3 Meses`.
- `Insight Simulação`: páginas `Forecast e Simulação`. Regra: monta um texto narrativo com os parâmetros selecionados e o resultado do cenário, exibindo a receita projetada e a variação sobre o baseline. Dependências: `Receita Projetada 3 Meses`, `Ganho Projetado %`.
- `Receita Forecast Baseline`: páginas `Forecast e Simulação`. Regra: retorna a média base apenas para meses entre 1 e 3 meses à frente do `Último Mês Válido`; fora dessa janela devolve `BLANK()`. Dependências: `Último Mês Válido`, `Receita Média Base 3M`.
- `Receita Forecast Simulada`: páginas `Forecast e Simulação`. Regra: aplica o impacto da simulação sobre o baseline do forecast; quando existe baseline, retorna `Baseline * (1 + Impacto)` e, fora da janela projetada, devolve `BLANK()`. Dependências: `Receita Forecast Baseline`, `Impacto Total Simulação %`.
- `Receita Histórica Exibida`: páginas `Forecast e Simulação`. Regra: mostra a receita histórica apenas até o último mês considerado válido, devolvendo `BLANK()` fora dessa janela. Dependências: `Último Mês Válido`, `Receita Produtos`.
- `Receita Projetada 3 Meses`: páginas `Forecast e Simulação`. Regra: soma a projeção simulada dos três meses seguintes por meio de uma tabela temporária de meses e `SUMX`. Dependências: `Ultimo Mês Real`, `Receita Forecast Simulada`.

## Measures auxiliares chamadas pelas medidas acima

- `Ganho Projetado 3 Meses`: suporte para `Forecast e Simulação`. Regra: subtrai a receita baseline da receita projetada para obter o ganho absoluto do cenário simulado. Dependências: `Receita Projetada 3 Meses`, `Receita Baseline 3 Meses`.
- `Impacto Total Simulação %`: suporte para `Forecast e Simulação`. Regra: consolida os três parâmetros de simulação em um impacto percentual único, convertendo cada parâmetro em fração, aplicando os fatores `0.1`, `0.1` e `0.8` e combinando os efeitos de forma multiplicativa. A implementação lê diretamente as colunas das tabelas de parâmetro, sem passar pelas measures `Valor Param *`. Dependências: nenhuma.
- `Pedidos Atrasados por Seller`: suporte para `Logistica e Satisfação`. Regra: conta pedidos distintos do seller que foram entregues com atraso, reaplicando o conjunto de `order_id` do seller sobre `Orders` com `TREATAS`. Dependências: nenhuma.
- `Pedidos Entregues`: suporte para `Logistica e Satisfação`, `Forecast e Simulação`. Regra: reaplica a measure `Pedidos` apenas sobre pedidos com `order_status = "delivered"`. Dependências: `Pedidos`.
- `Receita Baseline 3 Meses`: suporte para `Forecast e Simulação`. Regra: soma o baseline mensal projetado para os três meses imediatamente após o `Ultimo Mês Real`. Dependências: `Ultimo Mês Real`, `Receita Forecast Baseline`.
- `Receita Média Base 3M`: suporte para `Forecast e Simulação`. Regra: calcula a média mensal de receita dos três meses válidos anteriores, servindo de base para o forecast. Dependências: `Último Mês Válido`, `Receita Produtos`.
- `Receita Mês Anterior Card`: suporte para `Ganhos e Crescimento`. Regra: recalcula a receita do mês imediatamente anterior ao último mês visível usando a medida de receita por data de entrega. Dependências: `Receita Produtos (Data Entrega)`.
- `Receita Produtos`: suporte para `Ganhos e Crescimento`, `Clientes e Produtos`, `Forecast e Simulação`. Regra: soma `Order Items[price]` no contexto de filtro atual. Dependências: nenhuma.
- `Receita Sellers Estratégicos`: suporte para `Forecast e Simulação`. Regra: monta o top 10 global de sellers por receita com `ALL('Sellers')` e soma a receita apenas desse grupo. Dependências: `Receita Produtos`.
- `Score Atraso Seller`: suporte para `Logistica e Satisfação`. Regra: monta um score de atraso por seller combinando volume de pedidos e atraso médio, para servir de base ao ranking de detratores. Dependências: nenhuma.
- `Último Mês Válido`: suporte para `Forecast e Simulação`. Regra: identifica o último mês com cobertura suficiente de dias para sustentar o forecast, usando uma tabela temporária por mês e validação de cobertura mínima. Dependências: nenhuma.
- `Ultima Data Real`: suporte para `Forecast e Simulação`. Regra: captura a data máxima de compra ignorando filtros do calendário. Dependências: nenhuma.
- `Ultimo Mês Real`: suporte para `Forecast e Simulação`. Regra: transforma `Ultima Data Real` no fechamento do respectivo mês com `EOMONTH`. Dependências: `Ultima Data Real`.

## Colunas calculadas DAX usadas no report

- `Customers[LocalizacaoMapa]`: suporte para `Ganhos e Crescimento`. Regra: concatena cidade e estado para formar a chave textual usada no mapa e em visuais geográficos.
- `Orders[Data Compra]`: suporte para `Forecast e Simulação`. Regra: reconstrói a data de compra sem componente de hora a partir de ano, mês e dia do timestamp original.
- `Orders[DateId_Approved]`: suporte para `Logistica e Satisfação`. Regra: trunca o datetime original para produzir uma chave de data compatível com relacionamentos e filtros por calendário.
- `Orders[DateId_Delivered_Carrier]`: suporte para `Logistica e Satisfação`. Regra: trunca o datetime original para produzir uma chave de data compatível com relacionamentos e filtros por calendário.
- `Orders[DateId_Delivered_Customer]`: suporte para `Ganhos e Crescimento`, `Logistica e Satisfação`, `Clientes e Produtos`, `Forecast e Simulação`. Regra: trunca o datetime original para produzir uma chave de data compatível com relacionamentos e filtros por calendário.
- `Orders[DateId_Estimated]`: suporte para `Logistica e Satisfação`, `Forecast e Simulação`. Regra: trunca o datetime original para produzir uma chave de data compatível com relacionamentos e filtros por calendário.
- `Orders[DateId_Purchase]`: suporte para `Logistica e Satisfação`. Regra: trunca o datetime original para produzir uma chave de data compatível com relacionamentos e filtros por calendário.
- `Sellers[Seller_Alias]`: suporte para `Logistica e Satisfação`, `Clientes e Produtos`. Regra: gera um alias técnico e anonimizado para sellers usando `RANKX` sobre `seller_id` e formatação com três dígitos.

## Tabelas calculadas DAX usadas no report

- `Calendario`: suporte para `Ganhos e Crescimento`, `Logistica e Satisfação`, `Clientes e Produtos`, `Forecast e Simulação`. Regra: cria a tabela calendário oficial do modelo a partir de `2016-01-01` até seis meses após a última compra, adicionando colunas derivadas para ordenação, exibição mensal, semana, trimestre e chave `DateId`. Colunas disponibilizadas: `Date`, `Ano`, `MesNumero`, `Mes`, `MesAbreviado`, `AnoMes`, `Trimestre`, `DiaSemanaNumero`, `DiaSemana`, `SemanaAno`, `DateId`, `OrdemAnoMes`.
- `Param Aumento Recompra`: suporte para `Forecast e Simulação`. Regra: cria uma tabela de parâmetro via `GENERATESERIES` para alimentar os slicers da simulação e a leitura dos valores selecionados. Colunas disponibilizadas: `Param Aumento Recompra`.
- `Param Expansão Sellers`: suporte para `Forecast e Simulação`. Regra: cria uma tabela de parâmetro via `GENERATESERIES` para alimentar os slicers da simulação e a leitura dos valores selecionados. Colunas disponibilizadas: `Param Expansão Sellers`.
- `Param Redução Atraso`: suporte para `Forecast e Simulação`. Regra: cria uma tabela de parâmetro via `GENERATESERIES` para alimentar os slicers da simulação e a leitura dos valores selecionados. Colunas disponibilizadas: `Param Redução Atraso`.

## Calibração Estatística da Simulação

A measure `Impacto Total Simulação %` usa na implementação DAX os fatores `0.1`, `0.1` e `0.8`, mas esses pesos não reproduzem literalmente a regressão. Eles operacionalizam, de forma simplificada, os drivers que foram testados no estudo salvo em `../regression/Regressions.xlsx`.

A regressão foi montada com as colunas `AnoMes`, `% Pedidos Atrasados`, `% Clientes com Recompra`, `% Receita Sellers Estratégicos`, `Receita M`, `Receita M+1` e `Crescimento Receita M+1`.

Na aba `Regressions`, os números citados anteriormente correspondem à coluna `P-value`, e não à coluna `Coefficients`. Pela ordem das variáveis na aba `Base`, os `p-values` são:

- `% Pedidos Atrasados`: `0,926411608915787`
- `% Clientes com Recompra`: `0,625031150981618`
- `% Receita Sellers Estratégicos`: `0,0146074473418258`

Dentro desse recorte e dessa amostra, isso indica que `% Receita Sellers Estratégicos` foi o driver com evidência estatística mais forte, enquanto `% Pedidos Atrasados` e `% Clientes com Recompra` entram no simulador como alavancas mais exploratórias/experimentais.

Os coeficientes estimados na mesma regressão foram:

- `% Pedidos Atrasados`: `0,12405801074994748`
- `% Clientes com Recompra`: `-3,9414744448514445`
- `% Receita Sellers Estratégicos`: `4,1437796177616635`

Por isso, a DAX `Impacto Total Simulação %` deve ser lida como uma camada de simulação de cenário guiada pelo estudo estatístico, e não como uma transcrição direta da equação de regressão.

## Fórmulas completas

O arquivo complementar `DAX_FORMULAS.md` replica exatamente o mesmo escopo deste `README`, mas traz as fórmulas DAX completas por extenso para measures, colunas e tabelas calculadas usadas no report.
