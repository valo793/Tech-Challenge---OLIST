# Fórmulas DAX do Report Atual

Este documento lista por extenso as fórmulas DAX do escopo usado pelo dashboard atual: measures visuais, measures auxiliares, colunas calculadas e tabelas calculadas que alimentam o report.

Resumo do escopo:

- `51` measures diretas
- `13` measures auxiliares
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

Leitura técnica: compara a receita do último mês visível com a do mês imediatamente anterior, usando a receita recalculada pela data de entrega.

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
    USERELATIONSHIP(Orders[DateId_Delivered_Customer], Calendario[DateId]),
    Orders[order_status] = "delivered"
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

Leitura técnica: divide a quantidade de pedidos avaliados com `review_score < 4` pelo total de pedidos avaliados no contexto.

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

Leitura técnica: calcula a média de dias de atraso entre a data estimada e a data efetiva de entrega, convertendo entregas no prazo ou adiantadas em `0`.

#### `Estrelas Nota Média`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Alias no visual: `Estrelas nota média`
- Dependências: `Nota Média`

```DAX
VAR Nota = MIN(5, MAX(0, INT([Nota Média])))
RETURN REPT("★", Nota) & REPT("☆", 5 - Nota)
```

Leitura técnica: converte a medida base em 0 a 5 estrelas inteiras, truncando casas decimais com `INT` e completando o restante com estrelas vazias.

#### `Estrelas Nota Média Pedidos Atrasados`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: `Nota Média Pedidos Atrasados`

```DAX
VAR Nota = MIN(5, MAX(0, INT([Nota Média Pedidos Atrasados])))
RETURN REPT("★", Nota) & REPT("☆", 5 - Nota)
```

Leitura técnica: converte a medida base em 0 a 5 estrelas inteiras, truncando casas decimais com `INT` e completando o restante com estrelas vazias.

#### `Estrelas Nota Média Pedidos no Prazo`

- Tabela: `Mectrics`
- Páginas: `Logistica e Satisfação`
- Dependências: `Nota Média Pedidos no Prazo`

```DAX
VAR Nota = MIN(5, MAX(0, INT([Nota Média Pedidos no Prazo])))
RETURN REPT("★", Nota) & REPT("☆", 5 - Nota)
```

Leitura técnica: converte a medida base em 0 a 5 estrelas inteiras, truncando casas decimais com `INT` e completando o restante com estrelas vazias.

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

Leitura técnica: calcula a média de dias entre aprovação e entrega à transportadora para pedidos com ambas as datas preenchidas.

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

Leitura técnica: calcula a média de dias entre compra e aprovação para pedidos com ambas as datas preenchidas.

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

Leitura técnica: calcula a média de dias entre compra e entrega ao cliente apenas para pedidos `delivered` com ambas as datas preenchidas.

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

Leitura técnica: calcula a média de dias entre entrega à transportadora e entrega ao cliente para pedidos com ambas as datas preenchidas.

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

Leitura técnica: calcula a média da nota média de review por pedido no contexto atual, iterando `Orders[order_id]`.

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

Leitura técnica: reaplica `Nota Média` apenas sobre pedidos `delivered` entregues depois da data estimada.

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

Leitura técnica: reaplica `Nota Média por Seller` apenas sobre pedidos `delivered` atrasados do seller no contexto atual.

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

Leitura técnica: reaplica `Nota Média` apenas sobre pedidos `delivered` entregues até a data estimada.

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

Leitura técnica: calcula a média das notas dos pedidos do seller usando o conjunto de `order_id` visível em `Order Items` e `TREATAS` para levar esse conjunto a `Order Reviews`.

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

Leitura técnica: conta pedidos distintos `delivered` cuja entrega ao cliente ocorreu após a data estimada.

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

Leitura técnica: conta pedidos distintos `delivered` cuja entrega ao cliente ocorreu até a data estimada.

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

Leitura técnica: conta pedidos distintos do seller no contexto atual a partir do conjunto de `order_id` visível em `Order Items`.

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

Leitura técnica: ranqueia apenas sellers com `Score Atraso Seller` positivo dentro do contexto selecionado usando `RANKX` sobre `ALLSELECTED('Sellers'[Seller_Alias])`.

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

Leitura técnica: conta clientes que já haviam comprado antes do mês corrente e voltaram a comprar no mês atual dentro da categoria e do contexto visível.

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

Leitura técnica: conta clientes cuja primeira compra histórica caiu dentro do mês corrente do contexto.

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

Leitura técnica: conta itens vendidos para clientes que têm pelo menos dois pedidos distintos no contexto, removendo o filtro de `Products` na identificação da recorrência.

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

Leitura técnica: compara a receita dos últimos 3 meses com a janela imediatamente anterior de 3 meses.

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

Leitura técnica: monta um ranking composto pela soma das posições em receita, pedidos e itens, e retorna a receita formatada do seller em 1º lugar.

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

Leitura técnica: monta um ranking composto pela soma das posições em receita, pedidos e itens, e retorna o alias do seller em 1º lugar.

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

Leitura técnica: monta o mesmo ranking composto e retorna a receita formatada do seller em 2º lugar.

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

Leitura técnica: monta o mesmo ranking composto e retorna o alias do seller em 2º lugar.

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

Leitura técnica: monta o mesmo ranking composto e retorna a receita formatada do seller em 3º lugar.

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

Leitura técnica: monta o mesmo ranking composto e retorna o alias do seller em 3º lugar.

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

Leitura técnica: divide a receita dos sellers estratégicos pelo total de receita removendo filtros de seller do denominador.

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

Leitura técnica: retorna a média base apenas para meses entre 1 e 3 meses à frente do `Último Mês Válido`; fora dessa janela devolve `BLANK()`.

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
- Dependências: `Ultimo Mês Real`, `Receita Forecast Simulada`

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

#### `Insight Simulação`

- Tabela: `Mectrics`
- Páginas: `Forecast e Simulação`
- Dependências: `Receita Projetada 3 Meses`, `Ganho Projetado %`

```DAX
"Com redução de atraso de " &
FORMAT('Param Redução Atraso'[Valor Param Redução Atraso] / 100, "0%") &
", aumento de recompra de " &
FORMAT('Param Aumento Recompra'[Valor Param Aumento Recompra] / 100, "0%") &
" e expansão de sellers estratégicos de " &
FORMAT('Param Expansão Sellers'[Valor Param Expansão Sellers] / 100, "0%") &
", a receita projetada para os próximos 3 meses é de " &
FORMAT([Receita Projetada 3 Meses], "R$ #,##0") &
", representando uma variação de " &
FORMAT([Ganho Projetado %], "0.0%") &
" sobre o baseline."
```

Leitura técnica: monta um texto narrativo com os parâmetros selecionados e o resultado do cenário, exibindo a receita projetada e a variação sobre o baseline.

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
- Dependências: nenhuma

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

Leitura técnica: consolida os três parâmetros de simulação em um impacto percentual único, convertendo cada parâmetro em fração, aplicando os fatores `0.1`, `0.1` e `0.8` e combinando os efeitos de forma multiplicativa. A implementação lê diretamente as colunas das tabelas de parâmetro, sem passar pelas measures `Valor Param *`.

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

Leitura técnica: conta pedidos distintos do seller que foram entregues com atraso, reaplicando o conjunto de `order_id` do seller sobre `Orders` com `TREATAS`.

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

Leitura técnica: reaplica a measure `Pedidos` apenas sobre pedidos com `order_status = "delivered"`.

### `Receita Baseline 3 Meses`

- Tabela: `Mectrics`
- Páginas impactadas: `Forecast e Simulação`
- Dependências: `Ultimo Mês Real`, `Receita Forecast Baseline`

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

Leitura técnica: soma o baseline mensal projetado para os três meses imediatamente após o `Ultimo Mês Real`.

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

Leitura técnica: soma `Order Items[price]` no contexto de filtro atual.

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

Leitura técnica: monta o top 10 global de sellers por receita com `ALL('Sellers')` e soma a receita apenas desse grupo.

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

### `Ultima Data Real`

- Tabela: `Mectrics`
- Páginas impactadas: `Forecast e Simulação`
- Dependências: nenhuma

```DAX
CALCULATE(
    MAX(Orders[order_purchase_timestamp]),
    REMOVEFILTERS(Calendario)
)
```

Leitura técnica: captura a data máxima de compra ignorando filtros do calendário.

### `Ultimo Mês Real`

- Tabela: `Mectrics`
- Páginas impactadas: `Forecast e Simulação`
- Dependências: `Ultima Data Real`

```DAX
EOMONTH([Ultima Data Real], 0)
```

Leitura técnica: transforma `Ultima Data Real` no fechamento do respectivo mês com `EOMONTH`.

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

A lógica de `Impacto Total Simulação %` foi calibrada com apoio de `regression/Regressions.xlsx`, mas os valores citados antes não eram coeficientes: eles aparecem na coluna `P-value` da aba `Regressions`.

Pela ordem das variáveis da aba `Base`, os `p-values` são:

- `% Pedidos Atrasados`: `0,926411608915787`
- `% Clientes com Recompra`: `0,625031150981618`
- `% Receita Sellers Estratégicos`: `0,0146074473418258`

Isso sustenta a leitura de `% Receita Sellers Estratégicos` como o driver com evidência estatística mais forte no recorte usado, enquanto `% Pedidos Atrasados` e `% Clientes com Recompra` permanecem como alavancas mais experimentais.

Os coeficientes estimados na mesma regressão foram:

- `% Pedidos Atrasados`: `0,12405801074994748`
- `% Clientes com Recompra`: `-3,9414744448514445`
- `% Receita Sellers Estratégicos`: `4,1437796177616635`

A DAX final, portanto, deve ser interpretada como uma simplificação de cenário inspirada por esse estudo, e não como uma cópia literal da equação de regressão.
