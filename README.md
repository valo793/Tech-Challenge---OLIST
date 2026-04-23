# Olist Dashboard

## DAX usada no report atual

Este documento foi refeito a partir do `Olist Dashboard.pbix` atual e considera apenas os objetos DAX efetivamente usados no dashboard.

Resumo do escopo:

- `50` measures usadas diretamente em visuais
- `14` measures auxiliares chamadas por essas measures
- `8` colunas calculadas DAX usadas no report
- `4` tabelas calculadas DAX usadas no report
- fórmulas completas por extenso em `DAX_FORMULAS.md`

## Convenções

- O inventário abaixo exclui `LocalDateTable_*` automáticas do Power BI porque elas não alimentam os visuais atuais.
- Alguns visuais exibem aliases diferentes do nome real da measure no modelo.
- Aliases identificados: `Clientes Recorrentes` = `Clientes com Recompra por Categoria`; `Itens Vendidos Clientes Recorrentes` = `Itens Vendidos Clientes Recorrentes (Período)`; `Rank Detrator Seller` = `Rank Atraso Seller`; `Estrelas nota média` = `Estrelas Nota Média`.

## Measures DAX usadas diretamente nos visuais

### Página `Ganhos e Crescimento`

- `Crescimento Receita % Card`: páginas `Ganhos e Crescimento`. Regra: executa uma divisão protegida contra erro de denominador zero ou nulo. Dependências: `Receita Último Mês`, `Receita Mês Anterior Card`.
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
- `% Reviews Negativas`: páginas `Logistica e Satisfação`. Regra: transforma a métrica base em percentual a partir de uma razão DAX calculada no contexto atual. Dependências: nenhuma.
- `Atraso Médio Entrega`: páginas `Logistica e Satisfação`. Regra: itera uma tabela temporária com `AVERAGEX` para calcular a média do resultado linha a linha. Dependências: nenhuma.
- `Estrelas Nota Média`: páginas `Logistica e Satisfação`. Alias no visual: `Estrelas nota média`. Regra: converte a nota média em uma representação textual por estrelas a partir da medida base correspondente. Dependências: `Nota Média`.
- `Estrelas Nota Média Pedidos Atrasados`: páginas `Logistica e Satisfação`. Regra: converte a nota média em uma representação textual por estrelas a partir da medida base correspondente. Dependências: `Nota Média Pedidos Atrasados`.
- `Estrelas Nota Média Pedidos no Prazo`: páginas `Logistica e Satisfação`. Regra: converte a nota média em uma representação textual por estrelas a partir da medida base correspondente. Dependências: `Nota Média Pedidos no Prazo`.
- `Lead Time Aprovação até Entrega Transportadora (dias)`: páginas `Logistica e Satisfação`. Regra: calcula o intervalo médio em dias entre eventos logísticos, normalmente filtrando apenas pedidos entregues e usando diferença entre datas. Dependências: nenhuma.
- `Lead Time Compra até Aprovação (dias)`: páginas `Logistica e Satisfação`. Regra: calcula o intervalo médio em dias entre eventos logísticos, normalmente filtrando apenas pedidos entregues e usando diferença entre datas. Dependências: nenhuma.
- `Lead Time Compra até Entrega (dias)`: páginas `Logistica e Satisfação`. Regra: calcula o intervalo médio em dias entre eventos logísticos, normalmente filtrando apenas pedidos entregues e usando diferença entre datas. Dependências: nenhuma.
- `Lead Time Transportadora até Entrega Cliente (dias)`: páginas `Logistica e Satisfação`. Regra: calcula o intervalo médio em dias entre eventos logísticos, normalmente filtrando apenas pedidos entregues e usando diferença entre datas. Dependências: nenhuma.
- `Nota Média`: páginas `Logistica e Satisfação`. Regra: calcula a média de avaliação dos pedidos no contexto filtrado, com filtros adicionais quando separa atraso e prazo. Dependências: nenhuma.
- `Nota Média Pedidos Atrasados`: páginas `Logistica e Satisfação`. Regra: calcula a média de avaliação dos pedidos no contexto filtrado, com filtros adicionais quando separa atraso e prazo. Dependências: `Nota Média`.
- `Nota Média Pedidos Atrasados por Seller`: páginas `Logistica e Satisfação`. Regra: calcula a média de avaliação dos pedidos no contexto filtrado, com filtros adicionais quando separa atraso e prazo. Dependências: `Nota Média por Seller`.
- `Nota Média Pedidos no Prazo`: páginas `Logistica e Satisfação`. Regra: calcula a média de avaliação dos pedidos no contexto filtrado, com filtros adicionais quando separa atraso e prazo. Dependências: `Nota Média`.
- `Nota Média por Seller`: páginas `Logistica e Satisfação`. Regra: calcula a média de avaliação dos pedidos no contexto filtrado, com filtros adicionais quando separa atraso e prazo. Dependências: nenhuma.
- `Pedidos`: páginas `Ganhos e Crescimento`, `Logistica e Satisfação`. Regra: conta pedidos distintos visíveis no contexto atual. Dependências: nenhuma.
- `Pedidos Atrasados`: páginas `Logistica e Satisfação`. Regra: consolida volume de pedidos no contexto atual, com filtros adicionais quando segmenta prazo, atraso ou seller. Dependências: nenhuma.
- `Pedidos no Prazo`: páginas `Logistica e Satisfação`. Regra: consolida volume de pedidos no contexto atual, com filtros adicionais quando segmenta prazo, atraso ou seller. Dependências: nenhuma.
- `Pedidos por Seller`: páginas `Logistica e Satisfação`. Regra: consolida volume de pedidos no contexto atual, com filtros adicionais quando segmenta prazo, atraso ou seller. Dependências: nenhuma.
- `Rank Atraso Seller`: páginas `Logistica e Satisfação`. Alias no visual: `Rank Detrator Seller`. Regra: gera um ranking sobre a base comparativa no contexto atual, normalmente com `RANKX` e filtros para remover valores inválidos. Dependências: `Score Atraso Seller`.

### Página `Clientes e Produtos`

- `% Clientes com Recompra`: páginas `Clientes e Produtos`, `Forecast e Simulação`. Regra: divide `Clientes com Recompra por Categoria` por `Clientes Únicos` para expressar a métrica em percentual. Dependências: `Clientes com Recompra por Categoria`, `Clientes Únicos`.
- `Clientes com Recompra por Categoria`: páginas `Clientes e Produtos`. Alias no visual: `Clientes Recorrentes`. Regra: segmenta a base de clientes entre novos, recorrentes ou compradores com recompra conforme o contexto temporal e de produto. Dependências: nenhuma.
- `Clientes Novos`: páginas `Clientes e Produtos`. Regra: segmenta a base de clientes entre novos, recorrentes ou compradores com recompra conforme o contexto temporal e de produto. Dependências: nenhuma.
- `Clientes Únicos`: páginas `Clientes e Produtos`. Regra: conta clientes únicos no contexto atual usando a chave `customer_unique_id`. Dependências: nenhuma.
- `Frequência Média de Compra`: páginas `Clientes e Produtos`. Regra: mede a frequência média de compra do cliente dentro da janela analisada. Dependências: nenhuma.
- `Itens Vendidos`: páginas `Clientes e Produtos`. Regra: conta linhas da tabela de itens para representar o volume de itens vendidos. Dependências: nenhuma.
- `Itens Vendidos Clientes Recorrentes (Período)`: páginas `Clientes e Produtos`. Alias no visual: `Itens Vendidos Clientes Recorrentes`. Regra: segmenta a base de clientes entre novos, recorrentes ou compradores com recompra conforme o contexto temporal e de produto. Dependências: nenhuma.
- `Receita 3 Meses Anteriores`: páginas `Clientes e Produtos`. Regra: soma a receita da janela imediatamente anterior de três meses para comparar com a janela atual. Dependências: `Receita Produtos`.
- `Receita Produtos (Data Entrega)`: páginas `Ganhos e Crescimento`, `Clientes e Produtos`. Regra: recalcula a receita usando a relação entre `Orders[DateId_Delivered_Customer]` e `Calendario[DateId]`, deslocando o contexto para a data de entrega. Dependências: `Receita Produtos`.
- `Receita Últimos 3 Meses`: páginas `Clientes e Produtos`. Regra: soma a receita dos três meses mais recentes dentro do contexto temporal visível. Dependências: `Receita Produtos`.
- `Tendência Receita %`: páginas `Clientes e Produtos`. Regra: executa uma divisão protegida contra erro de denominador zero ou nulo. Dependências: `Receita Últimos 3 Meses`, `Receita 3 Meses Anteriores`.
- `Top 1 Receita`: páginas `Clientes e Produtos`. Regra: recupera a posição correspondente do ranking montado para sellers, usando ordenação e seleção do item desejado. Dependências: nenhuma.
- `Top 1 Seller`: páginas `Clientes e Produtos`. Regra: recupera a posição correspondente do ranking montado para sellers, usando ordenação e seleção do item desejado. Dependências: nenhuma.
- `Top 2 Receita`: páginas `Clientes e Produtos`. Regra: recupera a posição correspondente do ranking montado para sellers, usando ordenação e seleção do item desejado. Dependências: nenhuma.
- `Top 2 Seller`: páginas `Clientes e Produtos`. Regra: recupera a posição correspondente do ranking montado para sellers, usando ordenação e seleção do item desejado. Dependências: nenhuma.
- `Top 3 Receita`: páginas `Clientes e Produtos`. Regra: recupera a posição correspondente do ranking montado para sellers, usando ordenação e seleção do item desejado. Dependências: nenhuma.
- `Top 3 Seller`: páginas `Clientes e Produtos`. Regra: recupera a posição correspondente do ranking montado para sellers, usando ordenação e seleção do item desejado. Dependências: nenhuma.

### Página `Forecast e Simulação`

- `% Clientes com Recompra`: páginas `Clientes e Produtos`, `Forecast e Simulação`. Regra: divide `Clientes com Recompra por Categoria` por `Clientes Únicos` para expressar a métrica em percentual. Dependências: `Clientes com Recompra por Categoria`, `Clientes Únicos`.
- `% Pedidos Atrasados`: páginas `Logistica e Satisfação`, `Forecast e Simulação`. Regra: divide `Pedidos Atrasados` por `Pedidos Entregues` para expressar a métrica em percentual. Dependências: `Pedidos Atrasados`, `Pedidos Entregues`.
- `% Receita Sellers Estratégicos`: páginas `Forecast e Simulação`. Regra: divide `Receita Sellers Estratégicos` por `Receita Produtos` para expressar a métrica em percentual. Dependências: `Receita Sellers Estratégicos`, `Receita Produtos`.
- `Ganho Projetado %`: páginas `Forecast e Simulação`. Regra: divide o ganho absoluto projetado pela receita baseline dos três meses futuros para transformar o cenário em percentual. Dependências: `Ganho Projetado 3 Meses`, `Receita Baseline 3 Meses`.
- `Receita Forecast Baseline`: páginas `Forecast e Simulação`. Regra: projeta o baseline dos meses futuros a partir da média-base e restringe a exibição à janela válida de forecast. Dependências: `Último Mês Válido`, `Receita Média Base 3M`.
- `Receita Forecast Simulada`: páginas `Forecast e Simulação`. Regra: aplica o impacto da simulação sobre o baseline do forecast; quando existe baseline, retorna `Baseline * (1 + Impacto)` e, fora da janela projetada, devolve `BLANK()`. Dependências: `Receita Forecast Baseline`, `Impacto Total Simulação %`.
- `Receita Histórica Exibida`: páginas `Forecast e Simulação`. Regra: mostra a receita histórica apenas até o último mês considerado válido, devolvendo `BLANK()` fora dessa janela. Dependências: `Último Mês Válido`, `Receita Produtos`.
- `Receita Projetada 3 Meses`: páginas `Forecast e Simulação`. Regra: soma a projeção simulada dos três meses seguintes por meio de uma tabela temporária de meses e `SUMX`. Dependências: `Receita Forecast Simulada`.

## Measures auxiliares chamadas pelas medidas acima

- `Ganho Projetado 3 Meses`: suporte para `Forecast e Simulação`. Regra: subtrai a receita baseline da receita projetada para obter o ganho absoluto do cenário simulado. Dependências: `Receita Projetada 3 Meses`, `Receita Baseline 3 Meses`.
- `Impacto Total Simulação %`: suporte para `Forecast e Simulação`. Regra: consolida os três parâmetros de simulação em um impacto percentual único, convertendo cada parâmetro em fração, aplicando os fatores `0.1`, `0.1` e `0.8` e combinando os efeitos de forma multiplicativa. Dependências: `Valor Param Redução Atraso`, `Valor Param Aumento Recompra`, `Valor Param Expansão Sellers`.
- `Pedidos Atrasados por Seller`: suporte para `Logistica e Satisfação`. Regra: consolida volume de pedidos no contexto atual, com filtros adicionais quando segmenta prazo, atraso ou seller. Dependências: nenhuma.
- `Pedidos Entregues`: suporte para `Logistica e Satisfação`, `Forecast e Simulação`. Regra: consolida volume de pedidos no contexto atual, com filtros adicionais quando segmenta prazo, atraso ou seller. Dependências: `Pedidos`.
- `Receita Baseline 3 Meses`: suporte para `Forecast e Simulação`. Regra: soma o baseline projetado dos três meses futuros a partir da medida `Receita Forecast Baseline`. Dependências: `Receita Forecast Baseline`.
- `Receita Média Base 3M`: suporte para `Forecast e Simulação`. Regra: calcula a média mensal de receita dos três meses válidos anteriores, servindo de base para o forecast. Dependências: `Último Mês Válido`, `Receita Produtos`.
- `Receita Mês Anterior Card`: suporte para `Ganhos e Crescimento`. Regra: recalcula a receita do mês imediatamente anterior ao último mês visível usando a medida de receita por data de entrega. Dependências: `Receita Produtos (Data Entrega)`.
- `Receita Produtos`: suporte para `Ganhos e Crescimento`, `Clientes e Produtos`, `Forecast e Simulação`. Regra: soma a coluna monetária relevante no contexto de filtro atual. Dependências: nenhuma.
- `Receita Sellers Estratégicos`: suporte para `Forecast e Simulação`. Regra: isola os sellers de maior receita e soma sua participação para compor a análise de sellers estratégicos. Dependências: `Receita Produtos`.
- `Score Atraso Seller`: suporte para `Logistica e Satisfação`. Regra: monta um score de atraso por seller combinando volume de pedidos e atraso médio, para servir de base ao ranking de detratores. Dependências: nenhuma.
- `Último Mês Válido`: suporte para `Forecast e Simulação`. Regra: identifica o último mês com cobertura suficiente de dias para sustentar o forecast, usando uma tabela temporária por mês e validação de cobertura mínima. Dependências: nenhuma.
- `Valor Param Aumento Recompra`: suporte para `Forecast e Simulação`. Regra: lê o valor selecionado no parâmetro da simulação usando `SELECTEDVALUE` com padrão zero. Dependências: nenhuma.
- `Valor Param Expansão Sellers`: suporte para `Forecast e Simulação`. Regra: lê o valor selecionado no parâmetro da simulação usando `SELECTEDVALUE` com padrão zero. Dependências: nenhuma.
- `Valor Param Redução Atraso`: suporte para `Forecast e Simulação`. Regra: lê o valor selecionado no parâmetro da simulação usando `SELECTEDVALUE` com padrão zero. Dependências: nenhuma.

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

A measure `Impacto Total Simulação %` usa na implementação DAX os fatores `0.1`, `0.1` e `0.8`, mas a base metodológica da calibração está registrada em `Regressions.xlsx`, na mesma pasta deste projeto.

A regressão foi montada com as colunas `AnoMes`, `% Pedidos`, `% Clientes`, `% Receita`, `Receita M` e `Crescimento Receita M+1`, gerando os seguintes coeficientes:

- `Sellers`: `0,0146074473418258`
- `Pedidos atrasados`: `0,625031150981618`
- `Recompras`: `0,926411608915787`

## Fórmulas completas

O arquivo complementar `DAX_FORMULAS.md` replica exatamente o mesmo escopo deste `README`, mas traz as fórmulas DAX completas por extenso para measures, colunas e tabelas calculadas usadas no report.
