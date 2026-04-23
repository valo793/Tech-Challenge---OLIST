# Fórmulas DAX do Report Atual

Este documento lista por extenso as fórmulas DAX do escopo usado pelo dashboard atual: measures visuais, measures auxiliares, colunas calculadas e tabelas calculadas que alimentam o report.

Resumo do escopo:

- `50` measures diretas
- `14` measures auxiliares
- `8` colunas calculadas
- `4` tabelas calculadas

## Measures diretas

### Página `Ganhos e Crescimento`

#### `Crescimento Receita % Card`

- Tabela: `Mectrics`
- Páginas: `Ganhos e Crescimento`
- Dependências: `Receita Último Mês`, `Receita Mês Anterior Card`

```DAX
DIVIDE(
    [Receita Último Mês] - [Receita Mês Anterior Card],
    [Receita Mês Anterior Card]
)
```

Leitura técnica: executa uma divisão protegida contra erro de denominador zero ou nulo.

#### `Parcelas Médias`

- Tabela: `Mectrics`
- Páginas: `Ganhos e Crescimento`
- Dependências: nenhuma

```DAX
AVERAGEX(
    VALUES('Order Payments'[order_id]),
    CALCULATE(MAX('Order Payments'[payment_installments]))
)
```

Leitura técnica: calcula a média de parcelas das transações visíveis no contexto atual.

#### `Pedidos`

- Tabela: `Mectrics`
- Páginas: `Ganhos e Crescimento`, `Logistica e Satisfação`
- Dependências: nenhuma

```DAX
DISTINCTCOUNT(Orders[order_id])
```

Leitura técnica: conta pedidos distintos visíveis no contexto atual.

#### `Receita Produtos (Data Entrega)`

- Tabela: `Mectrics`
- Páginas: `Ganhos e Crescimento`, `Clientes e Produtos`
- Dependências: `Receita Produtos`

```DAX
CALCULATE(
    [Receita Produtos],
    USERELATIONSHIP(Orders[DateId_Delivered_Customer], Calendario[DateId])
)
```

Leitura técnica: recalcula a receita usando a relação entre `Orders[DateId_Delivered_Customer]` e `Calendario[DateId]`, deslocando o contexto para a data de entrega.

#### `Receita Último Mês`

- Tabela: `Mectrics`
- Páginas: `Ganhos e Crescimento`
- Dependências: `Receita Produtos (Data Entrega)`

```DAX
VAR UltimaData = MAX(Calendario[Date])
VAR InicioMes = DATE(YEAR(UltimaData), MONTH(UltimaData), 1)
VAR FimMes = EOMONTH(UltimaData, 0)
RETURN
CALCULATE(
    [Receita Produtos (Data Entrega)],
    DATESBETWEEN(Calendario[Date], InicioMes, FimMes)
)
```

Leitura técnica: calcula a receita do último mês visível construindo o intervalo entre o primeiro e o último dia do mês corrente.

#### `Ticket Médio`

- Tabela: `Mectrics`
- Páginas: `Ganhos e Crescimento`
- Dependências: `Receita Produtos`, `Pedidos`

```DAX
DIVIDE([Receita Produtos], [Pedidos])
```

Leitura técnica: divide a receita de produtos pela quantidade de pedidos para obter o ticket médio.

### Página `Logistica e Satisfação`

#### `% Impacto Atraso`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: `Nota Média Pedidos no Prazo`, `Nota Média Pedidos Atrasados`

```DAX
DIVIDE(
    [Nota Média Pedidos no Prazo] - [Nota Média Pedidos Atrasados],
    [Nota Média Pedidos no Prazo]
)
```

Leitura técnica: mede a perda relativa de nota entre pedidos no prazo e pedidos atrasados, usando a diferença entre as notas médias dividida pela nota dos pedidos no prazo.

#### `% Pedidos Atrasados`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`, `Forecast e Simulação`
- Dependências: `Pedidos Atrasados`, `Pedidos Entregues`

```DAX
DIVIDE([Pedidos Atrasados], [Pedidos Entregues])
```

Leitura técnica: divide `Pedidos Atrasados` por `Pedidos Entregues` para expressar a métrica em percentual.

#### `% Pedidos Atrasados por Seller`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: `Pedidos Atrasados por Seller`, `Pedidos por Seller`

```DAX
DIVIDE(
    [Pedidos Atrasados por Seller],
    [Pedidos por Seller]
)
```

Leitura técnica: divide `Pedidos Atrasados por Seller` por `Pedidos por Seller` para expressar a métrica em percentual.

#### `% Pedidos no Prazo`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: `Pedidos no Prazo`, `Pedidos Entregues`

```DAX
DIVIDE([Pedidos no Prazo], [Pedidos Entregues])
```

Leitura técnica: divide `Pedidos no Prazo` por `Pedidos Entregues` para expressar a métrica em percentual.

#### `% Reviews Negativas`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: nenhuma

```DAX
DIVIDE(
    CALCULATE(
        DISTINCTCOUNT('Order Reviews'[order_id]),
        'Order Reviews'[review_score] < 4
    ),
    DISTINCTCOUNT('Order Reviews'[order_id])
)
```

Leitura técnica: transforma a métrica base em percentual a partir de uma razão DAX calculada no contexto atual.

#### `Atraso Médio Entrega`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: nenhuma

```DAX
AVERAGEX(
    FILTER(
        Orders,
        NOT ISBLANK(Orders[order_delivered_customer_date]) &&
        NOT ISBLANK(Orders[order_estimated_delivery_date])
    ),
    VAR DiasAtraso =
        DATEDIFF(
            Orders[order_estimated_delivery_date],
            Orders[order_delivered_customer_date],
            DAY
        )
    RETURN
        IF(DiasAtraso > 0, DiasAtraso, 0)
)
```

Leitura técnica: itera uma tabela temporária com `AVERAGEX` para calcular a média do resultado linha a linha.

#### `Estrelas Nota Média`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Alias no visual: `Estrelas nota média`
- Dependências: `Nota Média`

```DAX
VAR Nota = MIN(5, MAX(0, INT([Nota Média])))
RETURN REPT("★", Nota) & REPT("☆", 5 - Nota)
```

Leitura técnica: converte a nota média em uma representação textual por estrelas a partir da medida base correspondente.

#### `Estrelas Nota Média Pedidos Atrasados`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: `Nota Média Pedidos Atrasados`

```DAX
VAR Nota = MIN(5, MAX(0, INT([Nota Média Pedidos Atrasados])))
RETURN REPT("★", Nota) & REPT("☆", 5 - Nota)
```

Leitura técnica: converte a nota média em uma representação textual por estrelas a partir da medida base correspondente.

#### `Estrelas Nota Média Pedidos no Prazo`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: `Nota Média Pedidos no Prazo`

```DAX
VAR Nota = MIN(5, MAX(0, INT([Nota Média Pedidos no Prazo])))
RETURN REPT("★", Nota) & REPT("☆", 5 - Nota)
```

Leitura técnica: converte a nota média em uma representação textual por estrelas a partir da medida base correspondente.

#### `Lead Time Aprovação até Entrega Transportadora (dias)`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: nenhuma

```DAX
AVERAGEX(
    FILTER(
        Orders,
        NOT(ISBLANK(Orders[DateId_Approved])) &&
        NOT(ISBLANK(Orders[DateId_Delivered_Carrier]))
    ),
    DATEDIFF(
        Orders[DateId_Approved],
        Orders[DateId_Delivered_Carrier],
        DAY
    )
)
```

Leitura técnica: calcula o intervalo médio em dias entre eventos logísticos, normalmente filtrando apenas pedidos entregues e usando diferença entre datas.

#### `Lead Time Compra até Aprovação (dias)`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: nenhuma

```DAX
AVERAGEX(
    FILTER(
        Orders,
        NOT(ISBLANK(Orders[DateId_Purchase])) &&
        NOT(ISBLANK(Orders[DateId_Approved]))
    ),
    DATEDIFF(
        Orders[DateId_Purchase],
        Orders[DateId_Approved],
        DAY
    )
)
```

Leitura técnica: calcula o intervalo médio em dias entre eventos logísticos, normalmente filtrando apenas pedidos entregues e usando diferença entre datas.

#### `Lead Time Compra até Entrega (dias)`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: nenhuma

```DAX
AVERAGEX(
    FILTER(
        Orders,
        Orders[order_status] = "delivered" &&
        NOT(ISBLANK(Orders[DateId_Purchase])) &&
        NOT(ISBLANK(Orders[DateId_Delivered_Customer]))
    ),
    DATEDIFF(
        Orders[DateId_Purchase],
        Orders[DateId_Delivered_Customer],
        DAY
    )
)
```

Leitura técnica: calcula o intervalo médio em dias entre eventos logísticos, normalmente filtrando apenas pedidos entregues e usando diferença entre datas.

#### `Lead Time Transportadora até Entrega Cliente (dias)`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: nenhuma

```DAX
AVERAGEX(
    FILTER(
        Orders,
        NOT(ISBLANK(Orders[DateId_Delivered_Carrier])) &&
        NOT(ISBLANK(Orders[DateId_Delivered_Customer]))
    ),
    DATEDIFF(
        Orders[DateId_Delivered_Carrier],
        Orders[DateId_Delivered_Customer],
        DAY
    )
)
```

Leitura técnica: calcula o intervalo médio em dias entre eventos logísticos, normalmente filtrando apenas pedidos entregues e usando diferença entre datas.

#### `Nota Média`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: nenhuma

```DAX
AVERAGEX(
    VALUES('Orders'[order_id]),
    CALCULATE(AVERAGE('Order Reviews'[review_score]))
)
```

Leitura técnica: calcula a média de avaliação dos pedidos no contexto filtrado, com filtros adicionais quando separa atraso e prazo.

#### `Nota Média Pedidos Atrasados`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: `Nota Média`

```DAX
CALCULATE(
    [Nota Média],
    FILTER(
        Orders,
        Orders[order_status] = "delivered" &&
        NOT(ISBLANK(Orders[DateId_Delivered_Customer])) &&
        NOT(ISBLANK(Orders[DateId_Estimated])) &&
        Orders[DateId_Delivered_Customer] > Orders[DateId_Estimated]
    )
)
```

Leitura técnica: calcula a média de avaliação dos pedidos no contexto filtrado, com filtros adicionais quando separa atraso e prazo.

#### `Nota Média Pedidos Atrasados por Seller`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: `Nota Média por Seller`

```DAX
CALCULATE(
    [Nota Média por Seller],
    FILTER(
        Orders,
        Orders[order_status] = "delivered" &&
        NOT(ISBLANK(Orders[DateId_Delivered_Customer])) &&
        NOT(ISBLANK(Orders[DateId_Estimated])) &&
        Orders[DateId_Delivered_Customer] > Orders[DateId_Estimated]
    )
)
```

Leitura técnica: calcula a média de avaliação dos pedidos no contexto filtrado, com filtros adicionais quando separa atraso e prazo.

#### `Nota Média Pedidos no Prazo`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: `Nota Média`

```DAX
CALCULATE(
    [Nota Média],
    FILTER(
        Orders,
        Orders[order_status] = "delivered" &&
        NOT(ISBLANK(Orders[DateId_Delivered_Customer])) &&
        NOT(ISBLANK(Orders[DateId_Estimated])) &&
        Orders[DateId_Delivered_Customer] <= Orders[DateId_Estimated]
    )
)
```

Leitura técnica: calcula a média de avaliação dos pedidos no contexto filtrado, com filtros adicionais quando separa atraso e prazo.

#### `Nota Média por Seller`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: nenhuma

```DAX
VAR PedidosDoSeller =
    VALUES('Order Items'[order_id])
RETURN
    AVERAGEX(
        PedidosDoSeller,
        CALCULATE(
            AVERAGE('Order Reviews'[review_score]),
            TREATAS(PedidosDoSeller, 'Order Reviews'[order_id])
        )
    )
```

Leitura técnica: calcula a média de avaliação dos pedidos no contexto filtrado, com filtros adicionais quando separa atraso e prazo.

#### `Pedidos`

- Tabela: `Mectrics`
- Páginas: `Ganhos e Crescimento`, `Logistica e Satisfação`
- Dependências: nenhuma

```DAX
DISTINCTCOUNT(Orders[order_id])
```

Leitura técnica: conta pedidos distintos visíveis no contexto atual.

#### `Pedidos Atrasados`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: nenhuma

```DAX
CALCULATE(
    DISTINCTCOUNT(Orders[order_id]),
    FILTER(
        Orders,
        Orders[order_status] = "delivered" &&
        NOT(ISBLANK(Orders[DateId_Delivered_Customer])) &&
        NOT(ISBLANK(Orders[DateId_Estimated])) &&
        Orders[DateId_Delivered_Customer] > Orders[DateId_Estimated]
    )
)
```

Leitura técnica: consolida volume de pedidos no contexto atual, com filtros adicionais quando segmenta prazo, atraso ou seller.

#### `Pedidos no Prazo`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: nenhuma

```DAX
CALCULATE(
    DISTINCTCOUNT(Orders[order_id]),
    FILTER(
        Orders,
        Orders[order_status] = "delivered" &&
        NOT(ISBLANK(Orders[DateId_Delivered_Customer])) &&
        NOT(ISBLANK(Orders[DateId_Estimated])) &&
        Orders[DateId_Delivered_Customer] <= Orders[DateId_Estimated]
    )
)
```

Leitura técnica: consolida volume de pedidos no contexto atual, com filtros adicionais quando segmenta prazo, atraso ou seller.

#### `Pedidos por Seller`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: nenhuma

```DAX
--DISTINCTCOUNT('Order Items'[order_id])

VAR PedidosDoSeller =
    VALUES('Order Items'[order_id])
RETURN
        CALCULATE(
            DISTINCTCOUNT('Order Items'[order_id]),
            TREATAS(PedidosDoSeller, 'Order Reviews'[order_id])
        )
```

Leitura técnica: consolida volume de pedidos no contexto atual, com filtros adicionais quando segmenta prazo, atraso ou seller.

#### `Rank Atraso Seller`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Alias no visual: `Rank Detrator Seller`
- Dependências: `Score Atraso Seller`

```DAX
VAR ScoreAtual = [Score Atraso Seller]
VAR BaseRank =
    ADDCOLUMNS(
        ALLSELECTED('Sellers'[Seller_Alias]),
        "@Score", CALCULATE([Score Atraso Seller])
    )
RETURN
    IF(
        NOT ISINSCOPE('Sellers'[Seller_Alias]) ||
        ISBLANK(ScoreAtual) ||
        ScoreAtual <= 0,
        BLANK(),
        RANKX(
            FILTER(BaseRank, [@Score] > 0),
            [@Score],
            ScoreAtual,
            DESC,
            DENSE
        )
    )
```

Leitura técnica: gera um ranking sobre a base comparativa no contexto atual, normalmente com `RANKX` e filtros para remover valores inválidos.

### Página `Clientes e Produtos`

#### `% Clientes com Recompra`

- Tabela: `Mectrics`
- Páginas: `Clientes e Produtos`, `Forecast e Simulação`
- Dependências: `Clientes com Recompra por Categoria`, `Clientes Únicos`

```DAX
DIVIDE([Clientes com Recompra por Categoria], [Clientes Únicos])
```

Leitura técnica: divide `Clientes com Recompra por Categoria` por `Clientes Únicos` para expressar a métrica em percentual.

#### `Clientes com Recompra por Categoria`

- Tabela: `Mectrics`
- Páginas: `Clientes e Produtos`
- Alias no visual: `Clientes Recorrentes`
- Dependências: nenhuma

```DAX
VAR InicioMesAtual =
    DATE(YEAR(MAX(Calendario[Date])), MONTH(MAX(Calendario[Date])), 1)
VAR InicioProxMes =
    EDATE(InicioMesAtual, 1)

VAR PedidosDaCategoriaNoContexto =
    VALUES('Order Items'[order_id])

RETURN
COUNTROWS(
    FILTER(
        VALUES(Customers[customer_unique_id]),
        VAR PedidosAntesMesAtual =
            CALCULATE(
                DISTINCTCOUNT(Orders[order_id]),
                REMOVEFILTERS(Products),
                FILTER(
                    ALL(Calendario),
                    Calendario[Date] < InicioMesAtual
                )
            )
        VAR PedidosCategoriaNoMesAtual =
            CALCULATE(
                DISTINCTCOUNT(Orders[order_id]),
                TREATAS(PedidosDaCategoriaNoContexto, Orders[order_id]),
                FILTER(
                    ALL(Calendario),
                    Calendario[Date] >= InicioMesAtual &&
                    Calendario[Date] < InicioProxMes
                )
            )
        RETURN
            PedidosAntesMesAtual > 0 &&
            PedidosCategoriaNoMesAtual > 0
    )
)
```

Leitura técnica: segmenta a base de clientes entre novos, recorrentes ou compradores com recompra conforme o contexto temporal e de produto.

#### `Clientes Novos`

- Tabela: `Mectrics`
- Páginas: `Clientes e Produtos`
- Dependências: nenhuma

```DAX
VAR InicioMesAtual =
    DATE(YEAR(MIN(Calendario[Date])), MONTH(MIN(Calendario[Date])), 1)
VAR InicioProxMes =
    EOMONTH(InicioMesAtual, 0) + 1
RETURN
COUNTROWS(
    FILTER(
        VALUES(Customers[customer_unique_id]),
        VAR PrimeiraCompra =
            CALCULATE(
                MIN(Orders[order_purchase_timestamp]),
                REMOVEFILTERS(Calendario)
            )
        RETURN
            NOT ISBLANK(PrimeiraCompra) &&
            PrimeiraCompra >= InicioMesAtual &&
            PrimeiraCompra < InicioProxMes
    )
)
```

Leitura técnica: segmenta a base de clientes entre novos, recorrentes ou compradores com recompra conforme o contexto temporal e de produto.

#### `Clientes Únicos`

- Tabela: `Mectrics`
- Páginas: `Clientes e Produtos`
- Dependências: nenhuma

```DAX
DISTINCTCOUNT(Customers[customer_unique_id])
```

Leitura técnica: conta clientes únicos no contexto atual usando a chave `customer_unique_id`.

#### `Frequência Média de Compra`

- Tabela: `Mectrics`
- Páginas: `Clientes e Produtos`
- Dependências: nenhuma

```DAX
AVERAGEX(
    VALUES('Customers'[customer_unique_id]),
    CALCULATE(DISTINCTCOUNT('Orders'[order_id]))
)
```

Leitura técnica: mede a frequência média de compra do cliente dentro da janela analisada.

#### `Itens Vendidos`

- Tabela: `Mectrics`
- Páginas: `Clientes e Produtos`
- Dependências: nenhuma

```DAX
COUNTROWS('Order Items')
```

Leitura técnica: conta linhas da tabela de itens para representar o volume de itens vendidos.

#### `Itens Vendidos Clientes Recorrentes (Período)`

- Tabela: `Mectrics`
- Páginas: `Clientes e Produtos`
- Alias no visual: `Itens Vendidos Clientes Recorrentes`
- Dependências: nenhuma

```DAX
VAR ClientesRecorrentes =
    FILTER(
        VALUES(Customers[customer_unique_id]),
        CALCULATE(
            DISTINCTCOUNT('Order Items'[order_id]),
            REMOVEFILTERS(Products)
        ) >= 2
    )
RETURN
CALCULATE(
    COUNTROWS('Order Items'),
    ClientesRecorrentes
)
```

Leitura técnica: segmenta a base de clientes entre novos, recorrentes ou compradores com recompra conforme o contexto temporal e de produto.

#### `Receita 3 Meses Anteriores`

- Tabela: `Mectrics`
- Páginas: `Clientes e Produtos`
- Dependências: `Receita Produtos`

```DAX
VAR DataRef = MAX(Calendario[Date])
RETURN
CALCULATE(
    [Receita Produtos],
    DATESBETWEEN(
        Calendario[Date],
        EDATE(DataRef, -6) + 1,
        EDATE(DataRef, -3)
    )
)
```

Leitura técnica: soma a receita da janela imediatamente anterior de três meses para comparar com a janela atual.

#### `Receita Produtos (Data Entrega)`

- Tabela: `Mectrics`
- Páginas: `Ganhos e Crescimento`, `Clientes e Produtos`
- Dependências: `Receita Produtos`

```DAX
CALCULATE(
    [Receita Produtos],
    USERELATIONSHIP(Orders[DateId_Delivered_Customer], Calendario[DateId])
)
```

Leitura técnica: recalcula a receita usando a relação entre `Orders[DateId_Delivered_Customer]` e `Calendario[DateId]`, deslocando o contexto para a data de entrega.

#### `Receita Últimos 3 Meses`

- Tabela: `Mectrics`
- Páginas: `Clientes e Produtos`
- Dependências: `Receita Produtos`

```DAX
VAR DataRef = MAX(Calendario[Date])
RETURN
CALCULATE(
    [Receita Produtos],
    DATESBETWEEN(
        Calendario[Date],
        EDATE(DataRef, -3) + 1,
        DataRef
    )
)
```

Leitura técnica: soma a receita dos três meses mais recentes dentro do contexto temporal visível.

#### `Tendência Receita %`

- Tabela: `Mectrics`
- Páginas: `Clientes e Produtos`
- Dependências: `Receita Últimos 3 Meses`, `Receita 3 Meses Anteriores`

```DAX
DIVIDE(
    [Receita Últimos 3 Meses] - [Receita 3 Meses Anteriores],
    [Receita 3 Meses Anteriores]
)
```

Leitura técnica: executa uma divisão protegida contra erro de denominador zero ou nulo.

#### `Top 1 Receita`

- Tabela: `Mectrics`
- Páginas: `Clientes e Produtos`
- Dependências: nenhuma

```DAX
VAR Base =
    ADDCOLUMNS(
        SUMMARIZE(
            ALLSELECTED('Sellers'),
            'Sellers'[seller_id],
            'Sellers'[Seller_Alias]
        ),
        "@Receita", CALCULATE(SUM('Order Items'[price])),
        "@Pedidos", CALCULATE(DISTINCTCOUNT('Order Items'[order_id])),
        "@Itens", CALCULATE(COUNTROWS('Order Items'))
    )
VAR ComScore =
    ADDCOLUMNS(
        Base,
        "@Score",
            RANKX(Base, [@Receita], , DESC, DENSE) +
            RANKX(Base, [@Pedidos], , DESC, DENSE) +
            RANKX(Base, [@Itens], , DESC, DENSE)
    )
VAR Top1 =
    TOPN(1, ComScore, [@Score], ASC, [@Receita], DESC)
VAR ReceitaTop = MAXX(Top1, [@Receita])
RETURN
    FORMAT(ReceitaTop, "R$ #,##0")
```

Leitura técnica: recupera a posição correspondente do ranking montado para sellers, usando ordenação e seleção do item desejado.

#### `Top 1 Seller`

- Tabela: `Mectrics`
- Páginas: `Clientes e Produtos`
- Dependências: nenhuma

```DAX
VAR Base =
    ADDCOLUMNS(
        SUMMARIZE(
            ALLSELECTED('Sellers'),
            'Sellers'[seller_id],
            'Sellers'[Seller_Alias]
        ),
        "@Receita", CALCULATE(SUM('Order Items'[price])),
        "@Pedidos", CALCULATE(DISTINCTCOUNT('Order Items'[order_id])),
        "@Itens", CALCULATE(COUNTROWS('Order Items'))
    )
VAR ComScore =
    ADDCOLUMNS(
        Base,
        "@Score",
            RANKX(Base, [@Receita], , DESC, DENSE) +
            RANKX(Base, [@Pedidos], , DESC, DENSE) +
            RANKX(Base, [@Itens], , DESC, DENSE)
    )
VAR Top1 =
    TOPN(1, ComScore, [@Score], ASC, [@Receita], DESC)
VAR SellerTop = MAXX(Top1, [Seller_Alias])
RETURN
    SellerTop
```

Leitura técnica: recupera a posição correspondente do ranking montado para sellers, usando ordenação e seleção do item desejado.

#### `Top 2 Receita`

- Tabela: `Mectrics`
- Páginas: `Clientes e Produtos`
- Dependências: nenhuma

```DAX
VAR Base =
    ADDCOLUMNS(
        SUMMARIZE(
            ALLSELECTED('Sellers'),
            'Sellers'[seller_id],
            'Sellers'[Seller_Alias]
        ),
        "@Receita", CALCULATE(SUM('Order Items'[price])),
        "@Pedidos", CALCULATE(DISTINCTCOUNT('Order Items'[order_id])),
        "@Itens", CALCULATE(COUNTROWS('Order Items'))
    )
VAR ComScore =
    ADDCOLUMNS(
        Base,
        "@Score",
            RANKX(Base, [@Receita], , DESC, DENSE) +
            RANKX(Base, [@Pedidos], , DESC, DENSE) +
            RANKX(Base, [@Itens], , DESC, DENSE)
    )
VAR Top2 =
    EXCEPT(
        TOPN(2, ComScore, [@Score], ASC, [@Receita], DESC),
        TOPN(1, ComScore, [@Score], ASC, [@Receita], DESC)
    )
VAR ReceitaTop = MAXX(Top2, [@Receita])
RETURN
     FORMAT(ReceitaTop, "R$ #,##0")
```

Leitura técnica: recupera a posição correspondente do ranking montado para sellers, usando ordenação e seleção do item desejado.

#### `Top 2 Seller`

- Tabela: `Mectrics`
- Páginas: `Clientes e Produtos`
- Dependências: nenhuma

```DAX
VAR Base =
    ADDCOLUMNS(
        SUMMARIZE(
            ALLSELECTED('Sellers'),
            'Sellers'[seller_id],
            'Sellers'[Seller_Alias]
        ),
        "@Receita", CALCULATE(SUM('Order Items'[price])),
        "@Pedidos", CALCULATE(DISTINCTCOUNT('Order Items'[order_id])),
        "@Itens", CALCULATE(COUNTROWS('Order Items'))
    )
VAR ComScore =
    ADDCOLUMNS(
        Base,
        "@Score",
            RANKX(Base, [@Receita], , DESC, DENSE) +
            RANKX(Base, [@Pedidos], , DESC, DENSE) +
            RANKX(Base, [@Itens], , DESC, DENSE)
    )
VAR Top2 =
    EXCEPT(
        TOPN(2, ComScore, [@Score], ASC, [@Receita], DESC),
        TOPN(1, ComScore, [@Score], ASC, [@Receita], DESC)
    )
VAR SellerTop = MAXX(Top2, [Seller_Alias])
RETURN
    SellerTop
```

Leitura técnica: recupera a posição correspondente do ranking montado para sellers, usando ordenação e seleção do item desejado.

#### `Top 3 Receita`

- Tabela: `Mectrics`
- Páginas: `Clientes e Produtos`
- Dependências: nenhuma

```DAX
VAR Base =
    ADDCOLUMNS(
        SUMMARIZE(
            ALLSELECTED('Sellers'),
            'Sellers'[seller_id],
            'Sellers'[Seller_Alias]
        ),
        "@Receita", CALCULATE(SUM('Order Items'[price])),
        "@Pedidos", CALCULATE(DISTINCTCOUNT('Order Items'[order_id])),
        "@Itens", CALCULATE(COUNTROWS('Order Items'))
    )
VAR ComScore =
    ADDCOLUMNS(
        Base,
        "@Score",
            RANKX(Base, [@Receita], , DESC, DENSE) +
            RANKX(Base, [@Pedidos], , DESC, DENSE) +
            RANKX(Base, [@Itens], , DESC, DENSE)
    )
VAR Top3 =
    EXCEPT(
        TOPN(3, ComScore, [@Score], ASC, [@Receita], DESC),
        TOPN(2, ComScore, [@Score], ASC, [@Receita], DESC)
    )
VAR ReceitaTop = MAXX(Top3, [@Receita])
RETURN
FORMAT(ReceitaTop, "R$ #,##0")
```

Leitura técnica: recupera a posição correspondente do ranking montado para sellers, usando ordenação e seleção do item desejado.

#### `Top 3 Seller`

- Tabela: `Mectrics`
- Páginas: `Clientes e Produtos`
- Dependências: nenhuma

```DAX
VAR Base =
    ADDCOLUMNS(
        SUMMARIZE(
            ALLSELECTED('Sellers'),
            'Sellers'[seller_id],
            'Sellers'[Seller_Alias]
        ),
        "@Receita", CALCULATE(SUM('Order Items'[price])),
        "@Pedidos", CALCULATE(DISTINCTCOUNT('Order Items'[order_id])),
        "@Itens", CALCULATE(COUNTROWS('Order Items'))
    )
VAR ComScore =
    ADDCOLUMNS(
        Base,
        "@Score",
            RANKX(Base, [@Receita], , DESC, DENSE) +
            RANKX(Base, [@Pedidos], , DESC, DENSE) +
            RANKX(Base, [@Itens], , DESC, DENSE)
    )
VAR Top3 =
    EXCEPT(
        TOPN(3, ComScore, [@Score], ASC, [@Receita], DESC),
        TOPN(2, ComScore, [@Score], ASC, [@Receita], DESC)
    )
VAR SellerTop = MAXX(Top3, [Seller_Alias])
RETURN
    SellerTop
```

Leitura técnica: recupera a posição correspondente do ranking montado para sellers, usando ordenação e seleção do item desejado.

### Página `Forecast e Simulação`

#### `% Clientes com Recompra`

- Tabela: `Mectrics`
- Páginas: `Clientes e Produtos`, `Forecast e Simulação`
- Dependências: `Clientes com Recompra por Categoria`, `Clientes Únicos`

```DAX
DIVIDE([Clientes com Recompra por Categoria], [Clientes Únicos])
```

Leitura técnica: divide `Clientes com Recompra por Categoria` por `Clientes Únicos` para expressar a métrica em percentual.

#### `% Pedidos Atrasados`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`, `Forecast e Simulação`
- Dependências: `Pedidos Atrasados`, `Pedidos Entregues`

```DAX
DIVIDE([Pedidos Atrasados], [Pedidos Entregues])
```

Leitura técnica: divide `Pedidos Atrasados` por `Pedidos Entregues` para expressar a métrica em percentual.

#### `% Receita Sellers Estratégicos`

- Tabela: `Mectrics`
- Páginas: `Forecast e Simulação`
- Dependências: `Receita Sellers Estratégicos`, `Receita Produtos`

```DAX
DIVIDE(
    [Receita Sellers Estratégicos],
    CALCULATE(
        [Receita Produtos],
        REMOVEFILTERS('Sellers')
    )
)
```

Leitura técnica: divide `Receita Sellers Estratégicos` por `Receita Produtos` para expressar a métrica em percentual.

#### `Ganho Projetado %`

- Tabela: `Mectrics`
- Páginas: `Forecast e Simulação`
- Dependências: `Ganho Projetado 3 Meses`, `Receita Baseline 3 Meses`

```DAX
DIVIDE(
    [Ganho Projetado 3 Meses],
    [Receita Baseline 3 Meses]
)
```

Leitura técnica: divide o ganho absoluto projetado pela receita baseline dos três meses futuros para transformar o cenário em percentual.

#### `Receita Forecast Baseline`

- Tabela: `Mectrics`
- Páginas: `Forecast e Simulação`
- Dependências: `Último Mês Válido`, `Receita Média Base 3M`

```DAX
VAR MesContexto = EOMONTH(MAX(Calendario[Date]), 0)
VAR UltimoMes = [Último Mês Válido]
VAR MesesAFrente = DATEDIFF(UltimoMes, MesContexto, MONTH)
RETURN
IF(
    MesesAFrente >= 1 && MesesAFrente <= 3,
    [Receita Média Base 3M],
    BLANK()
)
```

Leitura técnica: projeta o baseline dos meses futuros a partir da média-base e restringe a exibição à janela válida de forecast.

#### `Receita Forecast Simulada`

- Tabela: `Mectrics`
- Páginas: `Forecast e Simulação`
- Dependências: `Receita Forecast Baseline`, `Impacto Total Simulação %`

```DAX
VAR Baseline = [Receita Forecast Baseline]
VAR Impacto  = [Impacto Total Simulação %]
RETURN
IF(
    NOT ISBLANK(Baseline),
    Baseline * (1 + Impacto),
    BLANK()
)
```

Leitura técnica: aplica o impacto da simulação sobre o baseline do forecast; quando existe baseline, retorna `Baseline * (1 + Impacto)` e, fora da janela projetada, devolve `BLANK()`.

#### `Receita Histórica Exibida`

- Tabela: `Mectrics`
- Páginas: `Forecast e Simulação`
- Dependências: `Último Mês Válido`, `Receita Produtos`

```DAX
VAR MesContexto = EOMONTH(MAX(Calendario[Date]), 0)
RETURN
IF(
    MesContexto <= [Último Mês Válido],
    [Receita Produtos],
    BLANK()
)
```

Leitura técnica: mostra a receita histórica apenas até o último mês considerado válido, devolvendo `BLANK()` fora dessa janela.

#### `Receita Projetada 3 Meses`

- Tabela: `Mectrics`
- Páginas: `Forecast e Simulação`
- Dependências: `Receita Forecast Simulada`

```DAX
VAR UltimoMes = [ultimo Mês Real]
VAR TabelaMeses =
    SUMMARIZE(
        FILTER(
            ALL(Calendario),
            EOMONTH(Calendario[Date], 0) > UltimoMes &&
            EOMONTH(Calendario[Date], 0) <= EOMONTH(UltimoMes, 3)
        ),
        Calendario[AnoMes]
    )
RETURN
SUMX(
    TabelaMeses,
    CALCULATE([Receita Forecast Simulada])
)
```

Leitura técnica: soma a projeção simulada dos três meses seguintes por meio de uma tabela temporária de meses e `SUMX`.

## Measures auxiliares

### `Ganho Projetado 3 Meses`

- Tabela: `Mectrics`
- Páginas impactadas: `Forecast e Simulação`
- Dependências: `Receita Projetada 3 Meses`, `Receita Baseline 3 Meses`

```DAX
[Receita Projetada 3 Meses] - [Receita Baseline 3 Meses]
```

Leitura técnica: subtrai a receita baseline da receita projetada para obter o ganho absoluto do cenário simulado.

### `Impacto Total Simulação %`

- Tabela: `Mectrics`
- Páginas impactadas: `Forecast e Simulação`
- Dependências: `Valor Param Redução Atraso`, `Valor Param Aumento Recompra`, `Valor Param Expansão Sellers`

```DAX
VAR ReducaoAtraso =
    DIVIDE('Param Redução Atraso'[Valor Param Redução Atraso], 100) * 0.1
VAR AumentoRecompra =
    DIVIDE('Param Aumento Recompra'[Valor Param Aumento Recompra], 100) * 0.1
VAR ExpansaoSellers =
    DIVIDE('Param Expansão Sellers'[Valor Param Expansão Sellers], 100) * 0.80
RETURN
    ((1 + ReducaoAtraso) * (1 + AumentoRecompra) * (1 + ExpansaoSellers)) - 1
```

Leitura técnica: consolida os três parâmetros de simulação em um impacto percentual único, convertendo cada parâmetro em fração, aplicando os fatores `0.1`, `0.1` e `0.8` e combinando os efeitos de forma multiplicativa.

### `Pedidos Atrasados por Seller`

- Tabela: `Mectrics`
- Páginas impactadas: `Logistica e Satisfação`
- Dependências: nenhuma

```DAX
VAR PedidosDoSeller =
    VALUES('Order Items'[order_id])
RETURN
    CALCULATE(
        DISTINCTCOUNT(Orders[order_id]),
        TREATAS(PedidosDoSeller, Orders[order_id]),
        FILTER(
            Orders,
            Orders[order_status] = "delivered" &&
            NOT(ISBLANK(Orders[DateId_Delivered_Customer])) &&
            NOT(ISBLANK(Orders[DateId_Estimated])) &&
            Orders[DateId_Delivered_Customer] > Orders[DateId_Estimated]
        )
    )
```

Leitura técnica: consolida volume de pedidos no contexto atual, com filtros adicionais quando segmenta prazo, atraso ou seller.

### `Pedidos Entregues`

- Tabela: `Mectrics`
- Páginas impactadas: `Logistica e Satisfação`, `Forecast e Simulação`
- Dependências: `Pedidos`

```DAX
CALCULATE(
    [Pedidos],
    Orders[order_status] = "delivered"
)
```

Leitura técnica: consolida volume de pedidos no contexto atual, com filtros adicionais quando segmenta prazo, atraso ou seller.

### `Receita Baseline 3 Meses`

- Tabela: `Mectrics`
- Páginas impactadas: `Forecast e Simulação`
- Dependências: `Receita Forecast Baseline`

```DAX
VAR UltimoMes = [ultimo Mês Real]
VAR TabelaMeses =
    SUMMARIZE(
        FILTER(
            ALL(Calendario),
            EOMONTH(Calendario[Date], 0) > UltimoMes &&
            EOMONTH(Calendario[Date], 0) <= EOMONTH(UltimoMes, 3)
        ),
        Calendario[AnoMes]
    )
RETURN
SUMX(
    TabelaMeses,
    CALCULATE([Receita Forecast Baseline])
)
```

Leitura técnica: soma o baseline projetado dos três meses futuros a partir da medida `Receita Forecast Baseline`.

### `Receita Média Base 3M`

- Tabela: `Mectrics`
- Páginas impactadas: `Forecast e Simulação`
- Dependências: `Último Mês Válido`, `Receita Produtos`

```DAX
VAR UltimoMes = [Último Mês Válido]
VAR InicioJanela = EOMONTH(UltimoMes, -3) + 1
VAR MesesBase =
    SUMMARIZE(
        FILTER(
            ALL(Calendario),
            Calendario[Date] >= InicioJanela &&
            Calendario[Date] <= UltimoMes
        ),
        Calendario[AnoMes]
    )
RETURN
AVERAGEX(
    MesesBase,
    CALCULATE([Receita Produtos])
)
```

Leitura técnica: calcula a média mensal de receita dos três meses válidos anteriores, servindo de base para o forecast.

### `Receita Mês Anterior Card`

- Tabela: `Mectrics`
- Páginas impactadas: `Ganhos e Crescimento`
- Dependências: `Receita Produtos (Data Entrega)`

```DAX
VAR UltimaData = MAX(Calendario[Date])
VAR InicioMesAnterior = DATE(YEAR(EOMONTH(UltimaData, -1)), MONTH(EOMONTH(UltimaData, -1)), 1)
VAR FimMesAnterior = EOMONTH(UltimaData, -1)
RETURN
CALCULATE(
    [Receita Produtos (Data Entrega)],
    DATESBETWEEN(Calendario[Date], InicioMesAnterior, FimMesAnterior)
)
```

Leitura técnica: recalcula a receita do mês imediatamente anterior ao último mês visível usando a medida de receita por data de entrega.

### `Receita Produtos`

- Tabela: `Mectrics`
- Páginas impactadas: `Ganhos e Crescimento`, `Clientes e Produtos`, `Forecast e Simulação`
- Dependências: nenhuma

```DAX
SUM('Order Items'[price])
```

Leitura técnica: soma a coluna monetária relevante no contexto de filtro atual.

### `Receita Sellers Estratégicos`

- Tabela: `Mectrics`
- Páginas impactadas: `Forecast e Simulação`
- Dependências: `Receita Produtos`

```DAX
VAR Base =
    ADDCOLUMNS(
        SUMMARIZE(
            ALL('Sellers'),
            'Sellers'[seller_id]
        ),
        "@Receita", CALCULATE([Receita Produtos])
    )
VAR Top10 =
    TOPN(10, Base, [@Receita], DESC, 'Sellers'[seller_id], ASC)
VAR SellersTop =
    SELECTCOLUMNS(Top10, "seller_id", [seller_id])
RETURN
CALCULATE(
    [Receita Produtos],
    TREATAS(SellersTop, 'Sellers'[seller_id])
)
```

Leitura técnica: isola os sellers de maior receita e soma sua participação para compor a análise de sellers estratégicos.

### `Score Atraso Seller`

- Tabela: `Mectrics`
- Páginas impactadas: `Logistica e Satisfação`
- Dependências: nenhuma

```DAX
VAR PedidosSeller =
    DISTINCTCOUNT('Order Items'[order_id])

VAR PedidosDoSeller =
    VALUES('Order Items'[order_id])

VAR AtrasoMedioSeller =
    CALCULATE(
        AVERAGEX(
            FILTER(
                Orders,
                Orders[order_status] = "delivered" &&
                NOT ISBLANK(Orders[order_delivered_customer_date]) &&
                NOT ISBLANK(Orders[order_estimated_delivery_date])
            ),
            VAR DiasAtraso =
                DATEDIFF(
                    Orders[order_estimated_delivery_date],
                    Orders[order_delivered_customer_date],
                    DAY
                )
            RETURN
                IF(DiasAtraso > 0, DiasAtraso, 0)
        ),
        TREATAS(PedidosDoSeller, Orders[order_id])
    )
RETURN
    IF(
        PedidosSeller > 0 &&
        NOT ISBLANK(AtrasoMedioSeller),
        PedidosSeller * AtrasoMedioSeller,
        BLANK()
    )
```

Leitura técnica: monta um score de atraso por seller combinando volume de pedidos e atraso médio, para servir de base ao ranking de detratores.

### `Último Mês Válido`

- Tabela: `Mectrics`
- Páginas impactadas: `Forecast e Simulação`
- Dependências: nenhuma

```DAX
VAR Meses =
    ADDCOLUMNS(
        SUMMARIZE(
            ALL(Calendario),
            Calendario[AnoMes],
            "InicioMes", MIN(Calendario[Date]),
            "FimMes", MAX(Calendario[Date])
        ),
        "@DiasNoMes", DAY([FimMes]),
        "@DiasComPedido",
            CALCULATE(
                DISTINCTCOUNT(Orders[Data Compra]),
                FILTER(
                    ALL(Orders),
                    Orders[Data Compra] >= [InicioMes] &&
                    Orders[Data Compra] <= [FimMes]
                )
            )
    )
VAR MesesValidos =
    FILTER(
        Meses,
        [@DiasComPedido] >= [@DiasNoMes] * 0.8
    )
RETURN
    MAXX(MesesValidos, [FimMes])
```

Leitura técnica: identifica o último mês com cobertura suficiente de dias para sustentar o forecast, usando uma tabela temporária por mês e validação de cobertura mínima.

### `Valor Param Aumento Recompra`

- Tabela: `Param Aumento Recompra`
- Páginas impactadas: `Forecast e Simulação`
- Dependências: nenhuma

```DAX
SELECTEDVALUE('Param Aumento Recompra'[Param Aumento Recompra], 0)
```

Leitura técnica: lê o valor selecionado no parâmetro da simulação usando `SELECTEDVALUE` com padrão zero.

### `Valor Param Expansão Sellers`

- Tabela: `Param Expansão Sellers`
- Páginas impactadas: `Forecast e Simulação`
- Dependências: nenhuma

```DAX
SELECTEDVALUE('Param Expansão Sellers'[Param Expansão Sellers], 0)
```

Leitura técnica: lê o valor selecionado no parâmetro da simulação usando `SELECTEDVALUE` com padrão zero.

### `Valor Param Redução Atraso`

- Tabela: `Param Redução Atraso`
- Páginas impactadas: `Forecast e Simulação`
- Dependências: nenhuma

```DAX
SELECTEDVALUE('Param Redução Atraso'[Param Redução Atraso], 0)
```

Leitura técnica: lê o valor selecionado no parâmetro da simulação usando `SELECTEDVALUE` com padrão zero.

## Colunas calculadas

### `Customers[LocalizacaoMapa]`

- Tabela: `Customers`
- Páginas impactadas: `Ganhos e Crescimento`

```DAX
[customer_city] & ", " & [customer_state] 
```

Leitura técnica: concatena cidade e estado para formar a chave textual usada no mapa e em visuais geográficos.

### `Orders[Data Compra]`

- Tabela: `Orders`
- Páginas impactadas: `Forecast e Simulação`

```DAX
DATE(
    YEAR(Orders[order_purchase_timestamp]),
    MONTH(Orders[order_purchase_timestamp]),
    DAY(Orders[order_purchase_timestamp])
)
```

Leitura técnica: reconstrói a data de compra sem componente de hora a partir de ano, mês e dia do timestamp original.

### `Orders[DateId_Approved]`

- Tabela: `Orders`
- Páginas impactadas: `Logistica e Satisfação`

```DAX
TRUNC(Orders[order_approved_at])
```

Leitura técnica: trunca o datetime original para produzir uma chave de data compatível com relacionamentos e filtros por calendário.

### `Orders[DateId_Delivered_Carrier]`

- Tabela: `Orders`
- Páginas impactadas: `Logistica e Satisfação`

```DAX
TRUNC([order_delivered_carrier_date])
```

Leitura técnica: trunca o datetime original para produzir uma chave de data compatível com relacionamentos e filtros por calendário.

### `Orders[DateId_Delivered_Customer]`

- Tabela: `Orders`
- Páginas impactadas: `Ganhos e Crescimento`, `Logistica e Satisfação`, `Clientes e Produtos`, `Forecast e Simulação`

```DAX
TRUNC([order_delivered_customer_date])
```

Leitura técnica: trunca o datetime original para produzir uma chave de data compatível com relacionamentos e filtros por calendário.

### `Orders[DateId_Estimated]`

- Tabela: `Orders`
- Páginas impactadas: `Logistica e Satisfação`, `Forecast e Simulação`

```DAX
TRUNC([order_estimated_delivery_date])
```

Leitura técnica: trunca o datetime original para produzir uma chave de data compatível com relacionamentos e filtros por calendário.

### `Orders[DateId_Purchase]`

- Tabela: `Orders`
- Páginas impactadas: `Logistica e Satisfação`

```DAX
TRUNC([order_purchase_timestamp])
```

Leitura técnica: trunca o datetime original para produzir uma chave de data compatível com relacionamentos e filtros por calendário.

### `Sellers[Seller_Alias]`

- Tabela: `Sellers`
- Páginas impactadas: `Logistica e Satisfação`, `Clientes e Produtos`

```DAX
"Seller #" &
FORMAT(
    RANKX(
        ALL('Sellers'[seller_id]),
        'Sellers'[seller_id],
        ,
        ASC,
        DENSE
    ),
    "000"
)
```

Leitura técnica: gera um alias técnico e anonimizado para sellers usando `RANKX` sobre `seller_id` e formatação com três dígitos.

## Tabelas calculadas

### `Calendario`

- Páginas impactadas: `Ganhos e Crescimento`, `Logistica e Satisfação`, `Clientes e Produtos`, `Forecast e Simulação`
- Colunas disponibilizadas: `Date`, `Ano`, `MesNumero`, `Mes`, `MesAbreviado`, `AnoMes`, `Trimestre`, `DiaSemanaNumero`, `DiaSemana`, `SemanaAno`, `DateId`, `OrdemAnoMes`

```DAX
VAR DataInicial = DATE(2016, 1, 1)
VAR DataFinal =
    EOMONTH(
        MAXX(Orders, Orders[order_purchase_timestamp]),
        6
    )
RETURN
ADDCOLUMNS(
    CALENDAR(DataInicial, DataFinal),
    "DateId", FORMAT([Date], "YYYY-MM-DD"),
    "Ano", YEAR([Date]),
    "MesNumero", MONTH([Date]),
    "Mes", FORMAT([Date], "MMMM"),
    "MesAbreviado", FORMAT([Date], "MMM"),
    "AnoMes", FORMAT([Date], "YYYY-MM"),
    "OrdemAnoMes", YEAR([Date]) * 100 + MONTH([Date]),
    "Trimestre", "T" & FORMAT([Date], "Q"),
    "DiaSemanaNumero", WEEKDAY([Date], 2),
    "DiaSemana", FORMAT([Date], "dddd"),
    "SemanaAno", WEEKNUM([Date], 2)
)
```

Leitura técnica: cria a tabela calendário oficial do modelo a partir de `2016-01-01` até seis meses após a última compra, adicionando colunas derivadas para ordenação, exibição mensal, semana, trimestre e chave `DateId`.

### `Param Aumento Recompra`

- Páginas impactadas: `Forecast e Simulação`
- Colunas disponibilizadas: `Param Aumento Recompra`

```DAX
GENERATESERIES(0, 20, 1)
```

Leitura técnica: cria uma tabela de parâmetro via `GENERATESERIES` para alimentar os slicers da simulação e a leitura dos valores selecionados.

### `Param Expansão Sellers`

- Páginas impactadas: `Forecast e Simulação`
- Colunas disponibilizadas: `Param Expansão Sellers`

```DAX
GENERATESERIES(0, 20, 1)
```

Leitura técnica: cria uma tabela de parâmetro via `GENERATESERIES` para alimentar os slicers da simulação e a leitura dos valores selecionados.

### `Param Redução Atraso`

- Páginas impactadas: `Forecast e Simulação`
- Colunas disponibilizadas: `Param Redução Atraso`

```DAX
GENERATESERIES(0, 30, 1)
```

Leitura técnica: cria uma tabela de parâmetro via `GENERATESERIES` para alimentar os slicers da simulação e a leitura dos valores selecionados.

## Calibração da Simulação

A lógica de `Impacto Total Simulação %` foi calibrada com apoio de `Regressions.xlsx`. Coeficientes registrados no estudo: `Sellers = 0,0146074473418258`, `Pedidos atrasados = 0,625031150981618` e `Recompras = 0,926411608915787`.
