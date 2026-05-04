# Tech Challenge | Olist Analytics

Repositório do Tech Challenge focado na análise da base Olist, na documentação do dashboard em Power BI e na organização dos entregáveis finais do projeto.

## Visão Geral

O projeto está organizado em três frentes principais:

- análise estatística em Python para gerar tabelas, gráficos e relatório executivo;
- dashboard e documentação analítica do Power BI;
- materiais finais de apresentação e apoio executivo.

## Estrutura do Repositório

```text
.
├── analitycs/   Código-fonte da análise em Python
├── bases/       Bases CSV de entrada
├── output/      Tabelas, gráficos e relatórios gerados pelo pipeline
└── docs/
    ├── power-bi/      Arquivos do dashboard, documentação DAX e assets visuais
    ├── presentation/  Materiais da apresentação
    ├── regression/    Apoio estatístico validado em Excel
    └── reports/       Relatórios executivos finais
```

Observação: a pasta `analitycs/` foi mantida com esse nome para preservar compatibilidade com a estrutura já usada no projeto.

## Código Python

O código Python do projeto fica em `analitycs/`, com o arquivo principal em `analitycs/analise.py`.

Esse script concentra a parte de desenvolvimento analítico do repositório:

- leitura e padronização dos CSVs de `bases/`;
- preparação das bases derivadas em nível de pedido, seller e série temporal;
- geração de tabelas consolidadas em `output/tables/`;
- geração de gráficos analíticos e estatísticos em `output/charts/`;
- geração dos relatórios em `output/report/`.

Em outras palavras, o Power BI documenta a camada final de consumo, enquanto o Python concentra a etapa de exploração, validação estatística e produção dos artefatos analíticos auxiliares.

## Como Executar a Análise

1. Garanta que os arquivos CSV estejam em `bases/` na raiz do projeto.
2. Instale as dependências usadas pelo script (`pandas`, `numpy`, `matplotlib`, `scipy`, `statsmodels` e `plotly`, quando aplicável).
3. Execute:

```powershell
python analitycs/analise.py
```

O pipeline salva as saídas automaticamente em:

- `output/charts/`
- `output/tables/`
- `output/report/`

## Onde Encontrar Cada Entregável

- Dashboard Power BI: `docs/power-bi/Olist Dashboard.pbix`
- Export do dashboard em PDF: `docs/power-bi/Olist Dashboard.pdf`
- Documentação detalhada do report e inventário DAX: `docs/power-bi/README.md`
- Fórmulas DAX completas: `docs/power-bi/DAX_FORMULAS.md`
- Extração técnica do PBIX: `docs/power-bi/pbix-extract/`
- Apresentação HTML e vídeo de apoio: `docs/presentation/`
- Estudo estatístico em Excel: `docs/regression/Regressions.xlsx`
- Relatórios executivos finais: `docs/reports/`

## Saídas Versionadas

O diretório `output/` continua versionado porque faz parte da entrega do projeto. Nele ficam:

- gráficos usados na narrativa executiva, no apêndice técnico e em validações estatísticas complementares;
- tabelas consolidadas para suporte analítico e checagens anteriores à curadoria final;
- relatório estatístico revisado em Markdown e DOCX.

### Detalhamento de `output/`

- `output/charts/` reúne não só os gráficos finais aproveitados na apresentação, mas também análises complementares feitas ao longo do projeto para validar hipóteses, confrontar métricas e sustentar decisões de curadoria. Entram aqui, por exemplo, boxplots, dispersões, controles estatísticos, séries mensais e paretos exploratórios.
- `output/tables/` concentra os CSVs auxiliares usados para suporte analítico, validação das leituras estatísticas e consolidação das bases derivadas que alimentam os gráficos e relatórios.
- `output/report/` guarda a síntese textual do pipeline Python, incluindo o relatório estatístico em Markdown e a versão DOCX gerada a partir dele.

## Leitura Recomendada

Se você estiver entrando no projeto agora, a melhor ordem é:

1. Ler este `README.md` para entender a estrutura.
2. Abrir `analitycs/analise.py` para entender a lógica do pipeline analítico em Python.
3. Consultar `output/report/analise_estatistica_olist.md` para a narrativa estatística gerada pelo Python.
4. Abrir `docs/power-bi/README.md` para a lógica final do dashboard.
