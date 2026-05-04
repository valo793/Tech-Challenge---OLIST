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
├── analitycs/   Script principal da análise em Python
├── bases/       Bases CSV de entrada
├── output/      Tabelas, gráficos e relatórios gerados pelo pipeline
└── docs/
    ├── power-bi/      Arquivos do dashboard, documentação DAX e assets visuais
    ├── presentation/  Materiais da apresentação
    ├── regression/    Apoio estatístico validado em Excel
    └── reports/       Relatórios executivos finais
```

Observação: a pasta `analitycs/` foi mantida com esse nome para preservar compatibilidade com a estrutura já usada no projeto.

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

- gráficos usados na narrativa executiva e no apêndice técnico;
- tabelas consolidadas para suporte analítico;
- relatório estatístico revisado em Markdown e DOCX.

## Leitura Recomendada

Se você estiver entrando no projeto agora, a melhor ordem é:

1. Ler este `README.md` para entender a estrutura.
2. Abrir `docs/power-bi/README.md` para a lógica do dashboard.
3. Consultar `output/report/analise_estatistica_olist.md` para a narrativa estatística gerada pelo Python.
