from __future__ import annotations

"""
Análise estatística complementar para a base Olist.

Arquitetura do script:
1. Ingestão robusta: detecta pasta de dados, arquivos CSV, encoding, separador,
   aliases de colunas e conversão de datas.
2. Camada analítica: cria bases derivadas em nível de pedido, seller-pedido e
   mensal para sustentar testes, gráficos de controle e regressões.
3. Camada executiva: salva tabelas, gráficos e um relatório em Markdown com
   interpretação em linguagem de negócio, sem afirmar causalidade absoluta.
"""

import csv
import math
import re
import sys
import unicodedata
import warnings
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from xml.sax.saxutils import escape as xml_escape

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, PercentFormatter
from pandas.tseries.offsets import MonthEnd

try:
    from scipy import stats
except Exception:  # pragma: no cover - dependência opcional
    stats = None

try:
    import statsmodels.api as sm
except Exception:  # pragma: no cover - dependência opcional
    sm = None

try:
    import plotly.graph_objects as go
    import plotly.io as pio
    from plotly.subplots import make_subplots
except Exception:  # pragma: no cover - dependência opcional
    go = None
    pio = None
    make_subplots = None

warnings.filterwarnings("ignore", category=RuntimeWarning)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIRS = [PROJECT_ROOT / "bases", PROJECT_ROOT / "data"]
OUTPUT_ROOT = PROJECT_ROOT / "output"
OUTPUT_CHARTS = OUTPUT_ROOT / "charts"
OUTPUT_TABLES = OUTPUT_ROOT / "tables"
OUTPUT_REPORT = OUTPUT_ROOT / "report"
DOCS_ROOT = PROJECT_ROOT / "docs"
DOCS_REPORTS = DOCS_ROOT / "reports"
EXECUTIVE_REPORT_DOCX = DOCS_REPORTS / "Relatorio_Executivo_Tech_Challenge_Olist_Data.docx"

SELLER_MIN_ORDERS_FOR_RISK = 20
MIN_SAMPLE_WARN = 20
PRIMARY_NEGATIVE_REVIEW_THRESHOLD = 2
ANALYSIS_START_DATE = pd.Timestamp("2017-01-01")
ANALYSIS_END_DATE = pd.Timestamp("2018-08-31")
SCENARIO_DELTAS = {
    "late_rate_pct": -3.0,
    "repurchase_customer_rate_pct": 3.0,
    "strategic_revenue_share_pct": 3.0,
}

RUNTIME_WARNINGS: List[str] = []
OBSOLETE_CHART_FILES = {
    "correlacao_drivers.png",
    "coeficientes_regressao.png",
    "receita_historica_vs_baseline.png",
    "comparacao_baseline_vs_cenario_m1.png",
}
OBSOLETE_TABLE_FILES = {
    "regression_results.csv",
    "regression_dataset.csv",
    "regression_dataset_ptbr.csv",
    "review_delay_ols_results.csv",
}


TABLE_SPECS: Dict[str, Dict[str, Any]] = {
    "customers": {
        "required_dataset": True,
        "include_tokens": ["customer"],
        "exclude_tokens": [],
        "required_columns": [
            "customer_id",
            "customer_unique_id",
            "customer_city",
            "customer_state",
        ],
        "date_columns": [],
        "numeric_columns": ["customer_zip_code_prefix"],
        "aliases": {
            "customer_id": ["customer_id", "id_cliente"],
            "customer_unique_id": ["customer_unique_id", "id_cliente_unico"],
            "customer_city": ["customer_city", "cidade_cliente"],
            "customer_state": ["customer_state", "estado_cliente"],
            "customer_zip_code_prefix": [
                "customer_zip_code_prefix",
                "customer_zip_code",
                "cep_cliente",
            ],
        },
    },
    "orders": {
        "required_dataset": True,
        "include_tokens": ["order"],
        "exclude_tokens": ["item", "payment", "review"],
        "required_columns": [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
        "date_columns": [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
        "numeric_columns": [],
        "aliases": {
            "order_id": ["order_id", "pedido_id"],
            "customer_id": ["customer_id", "id_cliente"],
            "order_status": ["order_status", "status_pedido"],
            "order_purchase_timestamp": [
                "order_purchase_timestamp",
                "purchase_timestamp",
                "order_purchase_date",
                "data_compra_pedido",
            ],
            "order_approved_at": ["order_approved_at", "data_aprovacao_pedido"],
            "order_delivered_carrier_date": [
                "order_delivered_carrier_date",
                "data_envio_transportadora",
            ],
            "order_delivered_customer_date": [
                "order_delivered_customer_date",
                "data_entrega_cliente",
            ],
            "order_estimated_delivery_date": [
                "order_estimated_delivery_date",
                "data_estimada_entrega",
            ],
        },
    },
    "order_items": {
        "required_dataset": True,
        "include_tokens": ["order", "item"],
        "exclude_tokens": ["payment", "review"],
        "required_columns": [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "price",
            "freight_value",
        ],
        "date_columns": ["shipping_limit_date"],
        "numeric_columns": ["order_item_id", "price", "freight_value"],
        "aliases": {
            "order_id": ["order_id", "pedido_id"],
            "order_item_id": ["order_item_id", "item_pedido_id"],
            "product_id": ["product_id", "produto_id"],
            "seller_id": ["seller_id", "vendedor_id"],
            "shipping_limit_date": ["shipping_limit_date", "data_limite_envio"],
            "price": ["price", "preco"],
            "freight_value": ["freight_value", "valor_frete"],
        },
    },
    "order_payments": {
        "required_dataset": False,
        "include_tokens": ["order", "payment"],
        "exclude_tokens": [],
        "required_columns": ["order_id", "payment_value"],
        "date_columns": [],
        "numeric_columns": [
            "payment_sequential",
            "payment_installments",
            "payment_value",
        ],
        "aliases": {
            "order_id": ["order_id", "pedido_id"],
            "payment_sequential": ["payment_sequential", "pagamento_sequencial"],
            "payment_type": ["payment_type", "tipo_pagamento"],
            "payment_installments": [
                "payment_installments",
                "parcelas_pagamento",
            ],
            "payment_value": ["payment_value", "valor_pagamento"],
        },
    },
    "order_reviews": {
        "required_dataset": True,
        "include_tokens": ["order", "review"],
        "exclude_tokens": [],
        "required_columns": ["order_id", "review_score"],
        "date_columns": ["review_creation_date", "review_answer_timestamp"],
        "numeric_columns": ["review_score"],
        "aliases": {
            "review_id": ["review_id", "avaliacao_id"],
            "order_id": ["order_id", "pedido_id"],
            "review_score": ["review_score", "nota_avaliacao"],
            "review_creation_date": ["review_creation_date", "data_criacao_avaliacao"],
            "review_answer_timestamp": [
                "review_answer_timestamp",
                "data_resposta_avaliacao",
            ],
        },
    },
    "products": {
        "required_dataset": True,
        "include_tokens": ["product"],
        "exclude_tokens": ["translation"],
        "required_columns": ["product_id", "product_category_name"],
        "date_columns": [],
        "numeric_columns": [
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ],
        "aliases": {
            "product_id": ["product_id", "produto_id"],
            "product_category_name": ["product_category_name", "categoria_produto"],
        },
    },
    "sellers": {
        "required_dataset": True,
        "include_tokens": ["seller"],
        "exclude_tokens": [],
        "required_columns": ["seller_id", "seller_city", "seller_state"],
        "date_columns": [],
        "numeric_columns": ["seller_zip_code_prefix"],
        "aliases": {
            "seller_id": ["seller_id", "vendedor_id"],
            "seller_city": ["seller_city", "cidade_vendedor"],
            "seller_state": ["seller_state", "estado_vendedor"],
            "seller_zip_code_prefix": ["seller_zip_code_prefix", "cep_vendedor"],
        },
    },
    "geolocation": {
        "required_dataset": False,
        "include_tokens": ["geolocation"],
        "exclude_tokens": [],
        "required_columns": [
            "geolocation_zip_code_prefix",
            "geolocation_city",
            "geolocation_state",
        ],
        "date_columns": [],
        "numeric_columns": ["geolocation_lat", "geolocation_lng"],
        "aliases": {
            "geolocation_zip_code_prefix": [
                "geolocation_zip_code_prefix",
                "cep_geolocalizacao",
            ],
            "geolocation_city": ["geolocation_city", "cidade_geolocalizacao"],
            "geolocation_state": ["geolocation_state", "estado_geolocalizacao"],
            "geolocation_lat": ["geolocation_lat", "latitude"],
            "geolocation_lng": ["geolocation_lng", "longitude"],
        },
    },
    "translation": {
        "required_dataset": False,
        "include_tokens": ["translation"],
        "exclude_tokens": [],
        "required_columns": [
            "product_category_name",
            "product_category_name_english",
        ],
        "date_columns": [],
        "numeric_columns": [],
        "aliases": {
            "product_category_name": [
                "product_category_name",
                "categoria_produto",
            ],
            "product_category_name_english": [
                "product_category_name_english",
                "categoria_produto_english",
                "categoria_produto_ingles",
            ],
        },
    },
}


@dataclass
class ControlChartResult:
    center_line: float
    upper_control_limit: float
    lower_control_limit: float
    out_of_control_periods: List[str]


def info(message: str) -> None:
    print(f"[INFO] {message}")


def warn(message: str) -> None:
    RUNTIME_WARNINGS.append(message)
    print(f"[ALERTA] {message}")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def format_br_number(value: Any, decimals: int = 2) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "n/d"
    formatted = f"{float(value):,.{decimals}f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def format_br_int(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "n/d"
    formatted = f"{int(round(float(value))):,}"
    return formatted.replace(",", ".")


def format_currency(value: Any, decimals: int = 2) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "n/d"
    return f"R$ {format_br_number(value, decimals)}"


def format_pct(value: Any, decimals: int = 2) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "n/d"
    return f"{format_br_number(value, decimals)}%"


def format_pvalue(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "n/d"
    if float(value) < 0.001:
        return "<0,001"
    return format_br_number(value, 4)


def currency_axis_formatter(value: float, _: int) -> str:
    if abs(value) >= 1_000_000:
        return f"R$ {value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"R$ {value / 1_000:.0f}k"
    return f"R$ {value:.0f}"


def ensure_output_dirs() -> Dict[str, Path]:
    for path in [OUTPUT_ROOT, OUTPUT_CHARTS, OUTPUT_TABLES, OUTPUT_REPORT, DOCS_REPORTS]:
        path.mkdir(parents=True, exist_ok=True)
    return {
        "root": OUTPUT_ROOT,
        "charts": OUTPUT_CHARTS,
        "tables": OUTPUT_TABLES,
        "report": OUTPUT_REPORT,
    }


def remove_obsolete_generated_files() -> None:
    for file_name in OBSOLETE_CHART_FILES:
        file_path = OUTPUT_CHARTS / file_name
        if file_path.exists():
            file_path.unlink()
            info(f"Chart obsoleto removido: {file_path}")

    for file_name in OBSOLETE_TABLE_FILES:
        file_path = OUTPUT_TABLES / file_name
        if file_path.exists():
            file_path.unlink()
            info(f"Tabela obsoleta removida: {file_path}")


def detect_data_dir() -> Path:
    for directory in DEFAULT_DATA_DIRS:
        if directory.exists() and any(directory.glob("*.csv")):
            info(f"Base de dados detectada em: {directory}")
            return directory
    raise FileNotFoundError(
        "Nenhuma pasta de dados com CSVs foi encontrada. "
        "Crie `./bases` ou `./data` na raiz do projeto."
    )


def detect_delimiter(file_path: Path, encoding: str) -> str:
    with file_path.open("r", encoding=encoding, newline="") as handle:
        sample = handle.read(4096)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except Exception:
        return ","


def match_file_for_spec(file_path: Path, include_tokens: List[str], exclude_tokens: List[str]) -> bool:
    normalized_name = normalize_text(file_path.stem)
    return all(token in normalized_name for token in include_tokens) and not any(
        token in normalized_name for token in exclude_tokens
    )


def detect_dataset_files(data_dir: Path) -> Dict[str, Path]:
    csv_files = sorted(data_dir.glob("*.csv"))
    remaining_files = list(csv_files)
    matches: Dict[str, Path] = {}

    for table_key, spec in TABLE_SPECS.items():
        candidates = [
            file_path
            for file_path in remaining_files
            if match_file_for_spec(
                file_path,
                spec["include_tokens"],
                spec["exclude_tokens"],
            )
        ]
        if candidates:
            chosen = sorted(candidates, key=lambda path: (len(path.name), path.name))[0]
            matches[table_key] = chosen
            remaining_files.remove(chosen)

    return matches


def load_csv_robust(file_path: Path) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    attempts: List[str] = []
    for encoding in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            delimiter = detect_delimiter(file_path, encoding)
            dataframe = pd.read_csv(
                file_path,
                sep=delimiter,
                encoding=encoding,
                low_memory=False,
            )
            return dataframe, {"encoding": encoding, "delimiter": delimiter}
        except Exception as exc:
            attempts.append(f"{encoding}: {exc}")

    raise ValueError(
        f"Falha ao ler {file_path.name}. Tentativas realizadas: {' | '.join(attempts)}"
    )


def standardize_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    standardized = dataframe.copy()
    standardized.columns = [normalize_text(column) for column in standardized.columns]
    return standardized


def apply_aliases(
    dataframe: pd.DataFrame,
    alias_map: Dict[str, List[str]],
) -> pd.DataFrame:
    renamed = dataframe.copy()
    rename_map: Dict[str, str] = {}
    current_columns = set(renamed.columns)

    for canonical_name, aliases in alias_map.items():
        if canonical_name in current_columns:
            continue
        normalized_aliases = [normalize_text(alias) for alias in aliases]
        match = next((alias for alias in normalized_aliases if alias in current_columns), None)
        if match:
            rename_map[match] = canonical_name
            current_columns.remove(match)
            current_columns.add(canonical_name)

    if rename_map:
        renamed = renamed.rename(columns=rename_map)
    return renamed


def parse_date_columns(dataframe: pd.DataFrame, explicit_date_columns: Iterable[str]) -> pd.DataFrame:
    parsed = dataframe.copy()
    automatic_date_columns = [
        column for column in parsed.columns if "date" in column or "timestamp" in column
    ]
    date_columns = sorted(set(explicit_date_columns).union(automatic_date_columns))

    for column in date_columns:
        if column in parsed.columns:
            parsed[column] = pd.to_datetime(parsed[column], errors="coerce", utc=False)

    return parsed


def coerce_numeric_columns(dataframe: pd.DataFrame, numeric_columns: Iterable[str]) -> pd.DataFrame:
    coerced = dataframe.copy()
    for column in numeric_columns:
        if column in coerced.columns:
            coerced[column] = pd.to_numeric(coerced[column], errors="coerce")
    return coerced


def validate_required_columns(
    dataframe: pd.DataFrame,
    table_name: str,
    required_columns: Iterable[str],
    source_file: Path,
) -> None:
    missing_columns = [column for column in required_columns if column not in dataframe.columns]
    if missing_columns:
        raise ValueError(
            f"O arquivo {source_file.name}, mapeado como `{table_name}`, está sem colunas "
            f"obrigatórias: {missing_columns}"
        )


def load_datasets(data_dir: Path) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Dict[str, Any]]]:
    detected_files = detect_dataset_files(data_dir)
    datasets: Dict[str, pd.DataFrame] = {}
    metadata: Dict[str, Dict[str, Any]] = {}
    required_missing: List[str] = []

    for table_key, spec in TABLE_SPECS.items():
        file_path = detected_files.get(table_key)
        if file_path is None:
            message = f"Arquivo para `{table_key}` não encontrado em {data_dir.name}."
            if spec["required_dataset"]:
                required_missing.append(table_key)
            else:
                warn(message)
            continue

        dataframe, file_meta = load_csv_robust(file_path)
        dataframe = standardize_columns(dataframe)
        dataframe = apply_aliases(dataframe, spec["aliases"])
        dataframe = parse_date_columns(dataframe, spec["date_columns"])
        dataframe = coerce_numeric_columns(dataframe, spec["numeric_columns"])
        validate_required_columns(dataframe, table_key, spec["required_columns"], file_path)

        datasets[table_key] = dataframe
        metadata[table_key] = {"path": file_path, **file_meta, "rows": len(dataframe)}
        info(
            f"{table_key}: {file_path.name} | linhas={len(dataframe)} | "
            f"separador='{file_meta['delimiter']}' | encoding={file_meta['encoding']}"
        )

    if required_missing:
        available_files = sorted(path.name for path in data_dir.glob("*.csv"))
        raise FileNotFoundError(
            "Arquivos essenciais ausentes para a análise: "
            f"{required_missing}. Arquivos disponíveis: {available_files}"
        )

    return datasets, metadata


def safe_divide(numerator: Any, denominator: Any) -> float:
    if denominator in [0, None] or (isinstance(denominator, float) and np.isnan(denominator)):
        return np.nan
    return float(numerator) / float(denominator)


def get_complete_month_bounds(date_series: pd.Series) -> Dict[str, Any]:
    valid_dates = pd.Series(date_series).dropna().sort_values()
    if valid_dates.empty:
        return {"start": None, "end": None, "dropped": []}

    start_period = valid_dates.iloc[0].to_period("M")
    end_period = valid_dates.iloc[-1].to_period("M")
    dropped: List[str] = []

    if valid_dates.iloc[0].day != 1:
        dropped.append(str(start_period))
        start_period = start_period + 1

    last_date = valid_dates.iloc[-1]
    month_end_date = (last_date + MonthEnd(0)).normalize()
    if last_date.normalize() != month_end_date:
        dropped.append(str(end_period))
        end_period = end_period - 1

    if start_period > end_period:
        warn("A filtragem de meses completos esgotaria toda a série. O script manterá todos os meses.")
        start_period = valid_dates.iloc[0].to_period("M")
        end_period = valid_dates.iloc[-1].to_period("M")
        dropped = []

    if dropped:
        info(f"Meses residuais removidos das análises mensais: {dropped}")

    return {"start": start_period, "end": end_period, "dropped": dropped}


def filter_complete_months(dataframe: pd.DataFrame, period_column: str, bounds: Dict[str, Any]) -> pd.DataFrame:
    if bounds["start"] is None or bounds["end"] is None:
        return dataframe.copy()
    filtered = dataframe.copy()
    if not isinstance(filtered[period_column].dtype, pd.PeriodDtype):
        filtered[period_column] = filtered[period_column].dt.to_period("M")
    mask = (filtered[period_column] >= bounds["start"]) & (filtered[period_column] <= bounds["end"])
    return filtered.loc[mask].copy()


def aggregate_reviews(reviews: pd.DataFrame) -> pd.DataFrame:
    review_counts = reviews.groupby("order_id").size().rename("review_count")
    review_scores = reviews.groupby("order_id")["review_score"].mean().rename("review_score")
    aggregated = pd.concat([review_scores, review_counts], axis=1).reset_index()
    return aggregated


def prepare_datasets(datasets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    customers = datasets["customers"].copy()
    orders = datasets["orders"].copy()
    order_items = datasets["order_items"].copy()
    reviews = aggregate_reviews(datasets["order_reviews"].copy())
    products = datasets["products"].copy()
    sellers = datasets["sellers"].copy()
    translation = datasets.get("translation")

    if translation is not None:
        translation = translation.copy()
        products = products.merge(
            translation[["product_category_name", "product_category_name_english"]],
            on="product_category_name",
            how="left",
        )
        products["product_category_final"] = (
            products["product_category_name_english"]
            .fillna(products["product_category_name"])
            .fillna("unknown")
        )
    else:
        warn("Tabela de tradução de categorias não encontrada. O script usará nomes originais das categorias.")
        products["product_category_final"] = products["product_category_name"].fillna("unknown")

    customers["customer_city"] = customers["customer_city"].fillna("unknown").astype(str).str.title()
    customers["customer_state"] = customers["customer_state"].fillna("unknown").astype(str).str.upper()
    sellers["seller_city"] = sellers["seller_city"].fillna("unknown").astype(str).str.title()
    sellers["seller_state"] = sellers["seller_state"].fillna("unknown").astype(str).str.upper()

    orders["order_status"] = orders["order_status"].fillna("unknown").astype(str).str.lower()

    orders = orders[
        orders["order_purchase_timestamp"].notna()
    ].copy()

    commercial_orders = orders.loc[
        (orders["order_status"] == "delivered")
        & orders["order_delivered_customer_date"].notna()
    ].copy()

    commercial_orders["reference_timestamp"] = commercial_orders["order_delivered_customer_date"]
    commercial_orders["reference_date"] = commercial_orders["reference_timestamp"].dt.floor("D")
    commercial_orders["year_month_period"] = commercial_orders["reference_timestamp"].dt.to_period("M")
    commercial_orders["year_month"] = commercial_orders["year_month_period"].astype(str)

    pre_period_rows = len(commercial_orders)

    commercial_orders = commercial_orders.loc[
        (commercial_orders["reference_timestamp"] >= ANALYSIS_START_DATE)
        & (
            commercial_orders["reference_timestamp"]
            < ANALYSIS_END_DATE + pd.Timedelta(days=1)
        )
    ].copy()

    excluded_pre_period = pre_period_rows - len(commercial_orders)
    if excluded_pre_period:
        info(
            "Pedidos fora do recorte principal por data de entrega foram excluídos: "
            f"{excluded_pre_period} linhas fora de "
            f"{ANALYSIS_START_DATE.date()} a {ANALYSIS_END_DATE.date()}"
        )

    item_level = order_items.merge(
        commercial_orders[
            [
                "order_id",
                "customer_id",
                "order_status",
                "order_purchase_timestamp",
                "order_approved_at",
                "order_delivered_carrier_date",
                "order_delivered_customer_date",
                "order_estimated_delivery_date",
                "reference_timestamp",
                "reference_date",
                "year_month_period",
                "year_month",
            ]
        ],
        on="order_id",
        how="inner",
    )
    item_level = item_level.merge(
        customers[
            [
                "customer_id",
                "customer_unique_id",
                "customer_city",
                "customer_state",
            ]
        ],
        on="customer_id",
        how="left",
    )
    item_level = item_level.merge(
        products[["product_id", "product_category_final"]],
        on="product_id",
        how="left",
    )
    item_level = item_level.merge(
        sellers[["seller_id", "seller_city", "seller_state"]],
        on="seller_id",
        how="left",
    )

    item_level["product_category_final"] = item_level["product_category_final"].fillna("unknown")
    item_level["price"] = item_level["price"].fillna(0)
    item_level["freight_value"] = item_level["freight_value"].fillna(0)
    item_level["item_revenue"] = item_level["price"]
    item_level["item_revenue_with_freight"] = item_level["price"] + item_level["freight_value"]

    item_level["purchase_date"] = item_level["reference_timestamp"].dt.floor("D")
    item_level["year_month_period"] = item_level["reference_timestamp"].dt.to_period("M")
    item_level["year_month"] = item_level["year_month_period"].astype(str)

    order_revenue = (
        item_level.groupby("order_id", as_index=False)
        .agg(
            order_revenue=("item_revenue", "sum"),
            item_count=("order_item_id", "count"),
            seller_count=("seller_id", "nunique"),
            product_count=("product_id", "nunique"),
        )
    )

    order_level = commercial_orders.merge(order_revenue, on="order_id", how="inner")
    order_level = order_level.merge(
        customers[
            [
                "customer_id",
                "customer_unique_id",
                "customer_city",
                "customer_state",
            ]
        ],
        on="customer_id",
        how="left",
    )
    order_level = order_level.merge(reviews, on="order_id", how="left")
    order_level["customer_city"] = order_level["customer_city"].fillna("unknown").astype(str).str.title()
    order_level["customer_state"] = order_level["customer_state"].fillna("unknown").astype(str).str.upper()
    order_level["purchase_date"] = order_level["reference_timestamp"].dt.floor("D")
    order_level["year_month_period"] = order_level["reference_timestamp"].dt.to_period("M")
    order_level["year_month"] = order_level["year_month_period"].astype(str)

    valid_delivery_mask = (
        (order_level["order_status"] == "delivered")
        & order_level["order_delivered_customer_date"].notna()
        & order_level["order_estimated_delivery_date"].notna()
    )
    order_level["delivered_with_valid_dates"] = valid_delivery_mask
    order_level["is_delayed"] = False
    order_level.loc[valid_delivery_mask, "is_delayed"] = (
        order_level.loc[valid_delivery_mask, "order_delivered_customer_date"]
        > order_level.loc[valid_delivery_mask, "order_estimated_delivery_date"]
    )
    delay_days = (
        order_level["order_delivered_customer_date"] - order_level["order_estimated_delivery_date"]
    ).dt.total_seconds() / 86400
    order_level["delay_days"] = np.where(valid_delivery_mask, np.clip(delay_days, 0, None), np.nan)
    lead_time_days = (
        order_level["order_delivered_customer_date"] - order_level["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400
    order_level["lead_time_days"] = np.where(valid_delivery_mask, np.clip(lead_time_days, 0, None), np.nan)

    customer_key = "customer_unique_id" if "customer_unique_id" in order_level.columns else "customer_id"
    order_level = order_level.sort_values([customer_key, "order_purchase_timestamp", "order_id"])
    order_level["customer_order_sequence"] = order_level.groupby(customer_key).cumcount() + 1
    order_level["is_repurchase_order"] = order_level["customer_order_sequence"] > 1
    order_level["customer_total_orders"] = order_level.groupby(customer_key)["order_id"].transform("count")
    order_level["customer_has_repurchase"] = order_level["customer_total_orders"] > 1

    negative_threshold = PRIMARY_NEGATIVE_REVIEW_THRESHOLD
    review_negative_flag = pd.Series(np.nan, index=order_level.index, dtype=float)
    reviewed_mask = order_level["review_score"].notna()
    negative_events = (order_level.loc[reviewed_mask, "review_score"] <= negative_threshold).sum()
    if negative_events < 30:
        warn(
            "Poucos reviews estritamente negativos (nota <= 2) para regressão logística. "
            "O script adotará nota <= 3 apenas para o modelo logístico."
        )
        negative_threshold = 3
    review_negative_flag.loc[reviewed_mask] = (
        order_level.loc[reviewed_mask, "review_score"] <= negative_threshold
    ).astype(int)
    order_level["negative_review_flag"] = review_negative_flag
    order_level["negative_review_threshold"] = negative_threshold

    seller_order = (
        item_level.groupby(["order_id", "seller_id"], as_index=False)
        .agg(
            seller_order_revenue=("item_revenue", "sum"),
            seller_item_count=("order_item_id", "count"),
            seller_product_count=("product_id", "nunique"),
        )
        .merge(
            sellers[["seller_id", "seller_city", "seller_state"]],
            on="seller_id",
            how="left",
        )
        .merge(
            order_level[
                [
                    "order_id",
                    "order_purchase_timestamp",
                    "year_month_period",
                    "year_month",
                    "delivered_with_valid_dates",
                    "is_delayed",
                    "delay_days",
                    "lead_time_days",
                    "review_score",
                    "negative_review_flag",
                ]
            ],
            on="order_id",
            how="left",
        )
    )

    daily_revenue = (
        order_level.groupby("purchase_date", as_index=False)
        .agg(
            daily_revenue=("order_revenue", "sum"),
            daily_orders=("order_id", "nunique"),
        )
        .sort_values("purchase_date")
    )

    complete_month_bounds = get_complete_month_bounds(order_level["reference_timestamp"])
    forced_start_period = ANALYSIS_START_DATE.to_period("M")
    if complete_month_bounds["start"] is not None and complete_month_bounds["start"] > forced_start_period:
        complete_month_bounds["start"] = forced_start_period
        complete_month_bounds["dropped"] = [
            month for month in complete_month_bounds["dropped"] if month != str(forced_start_period)
        ]
        info(
            f"Janeiro de 2017 foi preservado na serie mensal para manter o mesmo recorte principal do dashboard ({forced_start_period})."
        )
    monthly_metrics = build_monthly_metrics(order_level, customer_key, complete_month_bounds)

    return {
        "customers": customers,
        "orders": orders,
        "commercial_orders": commercial_orders,
        "item_level": item_level,
        "order_level": order_level,
        "seller_order": seller_order,
        "daily_revenue": daily_revenue,
        "monthly_metrics": monthly_metrics,
        "complete_month_bounds": complete_month_bounds,
        "customer_key": customer_key,
    }


def build_monthly_metrics(
    order_level: pd.DataFrame,
    customer_key: str,
    complete_month_bounds: Dict[str, Any],
) -> pd.DataFrame:
    base = (
        order_level.groupby("year_month_period", as_index=False)
        .agg(
            revenue_month=("order_revenue", "sum"),
            orders_month=("order_id", "nunique"),
            avg_ticket_month=("order_revenue", "mean"),
            unique_customers=(customer_key, "nunique"),
        )
        .sort_values("year_month_period")
    )

    delivered = order_level.loc[order_level["delivered_with_valid_dates"]].copy()
    delivered_stats = (
        delivered.groupby("year_month_period", as_index=False)
        .agg(
            delivered_orders_valid=("order_id", "nunique"),
            delayed_orders=("is_delayed", "sum"),
            avg_delay_days=("delay_days", "mean"),
            avg_lead_time_days=("lead_time_days", "mean"),
        )
    )

    reviewed = order_level.loc[order_level["review_score"].notna()].copy()
    review_stats = (
        reviewed.groupby("year_month_period", as_index=False)
        .agg(
            avg_review_score=("review_score", "mean"),
            negative_review_rate=("negative_review_flag", "mean"),
            review_count=("review_score", "count"),
        )
    )

    new_customers = (
        order_level.loc[order_level["customer_order_sequence"] == 1]
        .groupby("year_month_period")[customer_key]
        .nunique()
        .rename("new_customers")
        .reset_index()
    )

    repurchase_customers = (
        order_level.loc[order_level["is_repurchase_order"]]
        .groupby("year_month_period")[customer_key]
        .nunique()
        .rename("repurchase_customers")
        .reset_index()
    )

    repurchase_orders = (
        order_level.groupby("year_month_period")["is_repurchase_order"]
        .mean()
        .rename("repurchase_order_rate")
        .reset_index()
    )

    monthly = base.merge(delivered_stats, on="year_month_period", how="left")
    monthly = monthly.merge(review_stats, on="year_month_period", how="left")
    monthly = monthly.merge(new_customers, on="year_month_period", how="left")
    monthly = monthly.merge(repurchase_customers, on="year_month_period", how="left")
    monthly = monthly.merge(repurchase_orders, on="year_month_period", how="left")

    monthly["delivered_orders_valid"] = monthly["delivered_orders_valid"].fillna(0)
    monthly["delayed_orders"] = monthly["delayed_orders"].fillna(0)
    monthly["new_customers"] = monthly["new_customers"].fillna(0)
    monthly["repurchase_customers"] = monthly["repurchase_customers"].fillna(0)
    monthly["repurchase_order_rate"] = monthly["repurchase_order_rate"].fillna(0)
    monthly["late_rate"] = np.where(
        monthly["delivered_orders_valid"] > 0,
        monthly["delayed_orders"] / monthly["delivered_orders_valid"],
        np.nan,
    )
    monthly["repurchase_customer_rate"] = np.where(
        monthly["unique_customers"] > 0,
        monthly["repurchase_customers"] / monthly["unique_customers"],
        np.nan,
    )
    monthly["year_month"] = monthly["year_month_period"].astype(str)
    monthly = filter_complete_months(monthly, "year_month_period", complete_month_bounds)
    monthly = monthly.sort_values("year_month_period").reset_index(drop=True)
    monthly["revenue_mom_pct"] = monthly["revenue_month"].pct_change() * 100
    monthly["orders_mom_pct"] = monthly["orders_month"].pct_change() * 100
    monthly["ticket_mom_pct"] = monthly["avg_ticket_month"].pct_change() * 100
    return monthly


def save_dataframe(dataframe: pd.DataFrame, file_path: Path) -> None:
    output = dataframe.replace([np.inf, -np.inf], np.nan)
    output.to_csv(file_path, index=False, encoding="utf-8-sig")
    info(f"Tabela salva: {file_path}")


def plot_time_series(
    dataframe: pd.DataFrame,
    x_column: str,
    y_column: str,
    file_path: Path,
    title: str,
    ylabel: str,
    percent_axis: bool = False,
    currency_axis: bool = False,
) -> None:
    plot_df = dataframe.dropna(subset=[x_column, y_column]).copy()
    if plot_df.empty:
        warn(f"Sem dados para gerar gráfico: {title}")
        return

    fig, axis = plt.subplots(figsize=(12, 6))
    axis.plot(plot_df[x_column].astype(str), plot_df[y_column], marker="o", linewidth=2, color="#1f77b4")

    if len(plot_df) >= 3:
        x_numeric = np.arange(len(plot_df))
        coefficients = np.polyfit(x_numeric, plot_df[y_column], 1)
        trend = np.poly1d(coefficients)(x_numeric)
        axis.plot(plot_df[x_column].astype(str), trend, linestyle="--", color="#ff7f0e", label="Tendência linear")
        axis.legend()

    axis.set_title(title)
    axis.set_xlabel("Ano-Mês")
    axis.set_ylabel(ylabel)
    axis.grid(alpha=0.3)
    axis.tick_params(axis="x", rotation=45)

    if percent_axis:
        axis.yaxis.set_major_formatter(PercentFormatter(100))
    if currency_axis:
        axis.yaxis.set_major_formatter(FuncFormatter(currency_axis_formatter))

    plt.tight_layout()
    fig.savefig(file_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_control_chart_continuous(
    dataframe: pd.DataFrame,
    period_column: str,
    value_column: str,
    file_path: Path,
    title: str,
    ylabel: str,
    clamp_lower_zero: bool = False,
) -> Optional[ControlChartResult]:
    plot_df = dataframe.dropna(subset=[period_column, value_column]).copy()
    if len(plot_df) < 3:
        warn(f"Amostra insuficiente para gráfico de controle contínuo: {title}")
        return None

    center_line = float(plot_df[value_column].mean())
    std_dev = float(plot_df[value_column].std(ddof=1))
    upper_control_limit = center_line + 3 * std_dev
    lower_control_limit = center_line - 3 * std_dev
    if clamp_lower_zero:
        lower_control_limit = max(0.0, lower_control_limit)

    out_mask = (plot_df[value_column] > upper_control_limit) | (plot_df[value_column] < lower_control_limit)
    out_of_control_periods = plot_df.loc[out_mask, period_column].astype(str).tolist()

    fig, axis = plt.subplots(figsize=(12, 6))
    axis.plot(plot_df[period_column].astype(str), plot_df[value_column], marker="o", color="#1f77b4")
    axis.axhline(center_line, color="#2ca02c", linestyle="-", label="CL")
    axis.axhline(upper_control_limit, color="#d62728", linestyle="--", label="UCL")
    axis.axhline(lower_control_limit, color="#d62728", linestyle="--", label="LCL")
    if out_of_control_periods:
        axis.scatter(
            plot_df.loc[out_mask, period_column].astype(str),
            plot_df.loc[out_mask, value_column],
            color="#d62728",
            s=70,
            zorder=3,
            label="Fora de controle",
        )

    axis.set_title(title)
    axis.set_xlabel("Ano-Mês")
    axis.set_ylabel(ylabel)
    axis.grid(alpha=0.3)
    axis.tick_params(axis="x", rotation=45)
    axis.legend()
    plt.tight_layout()
    fig.savefig(file_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return ControlChartResult(
        center_line=center_line,
        upper_control_limit=upper_control_limit,
        lower_control_limit=lower_control_limit,
        out_of_control_periods=out_of_control_periods,
    )


def plot_p_chart(
    dataframe: pd.DataFrame,
    period_column: str,
    numerator_column: str,
    denominator_column: str,
    rate_column: str,
    file_path: Path,
    title: str,
    ylabel: str,
) -> Optional[ControlChartResult]:
    plot_df = dataframe.dropna(subset=[period_column, numerator_column, denominator_column, rate_column]).copy()
    plot_df = plot_df.loc[plot_df[denominator_column] > 0].copy()
    if len(plot_df) < 3:
        warn(f"Amostra insuficiente para p-chart: {title}")
        return None

    p_bar = safe_divide(plot_df[numerator_column].sum(), plot_df[denominator_column].sum())
    sigma = np.sqrt(p_bar * (1 - p_bar) / plot_df[denominator_column])
    plot_df["ucl"] = np.clip(p_bar + 3 * sigma, 0, 1)
    plot_df["lcl"] = np.clip(p_bar - 3 * sigma, 0, 1)
    out_mask = (plot_df[rate_column] > plot_df["ucl"]) | (plot_df[rate_column] < plot_df["lcl"])
    out_of_control_periods = plot_df.loc[out_mask, period_column].astype(str).tolist()

    fig, axis = plt.subplots(figsize=(12, 6))
    axis.plot(plot_df[period_column].astype(str), plot_df[rate_column], marker="o", color="#1f77b4", label="Taxa observada")
    axis.plot(plot_df[period_column].astype(str), [p_bar] * len(plot_df), color="#2ca02c", label="CL")
    axis.plot(plot_df[period_column].astype(str), plot_df["ucl"], color="#d62728", linestyle="--", label="UCL")
    axis.plot(plot_df[period_column].astype(str), plot_df["lcl"], color="#d62728", linestyle="--", label="LCL")
    if out_of_control_periods:
        axis.scatter(
            plot_df.loc[out_mask, period_column].astype(str),
            plot_df.loc[out_mask, rate_column],
            color="#d62728",
            s=70,
            zorder=3,
            label="Fora de controle",
        )
    axis.set_title(title)
    axis.set_xlabel("Ano-Mês")
    axis.set_ylabel(ylabel)
    axis.yaxis.set_major_formatter(PercentFormatter(1.0))
    axis.grid(alpha=0.3)
    axis.tick_params(axis="x", rotation=45)
    axis.legend()
    plt.tight_layout()
    fig.savefig(file_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return ControlChartResult(
        center_line=float(p_bar),
        upper_control_limit=float(plot_df["ucl"].max()),
        lower_control_limit=float(plot_df["lcl"].min()),
        out_of_control_periods=out_of_control_periods,
    )


def compute_concentration_table(
    dataframe: pd.DataFrame,
    group_column: str,
    value_column: str,
    label_fallback: str = "unknown",
) -> pd.DataFrame:
    concentration = dataframe.copy()
    concentration[group_column] = concentration[group_column].fillna(label_fallback).astype(str)
    concentration_table = (
        concentration.groupby(group_column, as_index=False)[value_column]
        .sum()
        .sort_values(value_column, ascending=False)
        .reset_index(drop=True)
    )
    total_value = concentration_table[value_column].sum()
    concentration_table["share"] = concentration_table[value_column] / total_value if total_value else np.nan
    concentration_table["cum_share"] = concentration_table["share"].cumsum()
    concentration_table["rank"] = np.arange(1, len(concentration_table) + 1)
    return concentration_table


def save_pareto_chart(
    concentration_table: pd.DataFrame,
    label_column: str,
    value_column: str,
    file_path: Path,
    title: str,
    top_n: int = 15,
) -> None:
    plot_df = concentration_table.head(top_n).copy()
    if plot_df.empty:
        warn(f"Sem dados para gráfico de Pareto: {title}")
        return

    fig, axis1 = plt.subplots(figsize=(13, 6))
    labels = plot_df[label_column].astype(str)
    axis1.bar(labels, plot_df[value_column], color="#1f77b4", alpha=0.85)
    axis1.set_ylabel("Receita")
    axis1.yaxis.set_major_formatter(FuncFormatter(currency_axis_formatter))
    axis1.tick_params(axis="x", rotation=45)
    axis1.grid(alpha=0.2, axis="y")

    axis2 = axis1.twinx()
    axis2.plot(labels, plot_df["cum_share"] * 100, color="#d62728", marker="o", linewidth=2)
    axis2.set_ylabel("Participação acumulada")
    axis2.yaxis.set_major_formatter(PercentFormatter(100))

    axis1.set_title(title)
    plt.tight_layout()
    fig.savefig(file_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_boxplot_delay_vs_review(dataframe: pd.DataFrame, file_path: Path) -> None:
    plot_df = dataframe.loc[dataframe["review_score"].notna()].copy()
    on_time = plot_df.loc[~plot_df["is_delayed"], "review_score"].dropna()
    delayed = plot_df.loc[plot_df["is_delayed"], "review_score"].dropna()
    if on_time.empty or delayed.empty:
        warn("Sem amostra suficiente para boxplot de review por atraso.")
        return

    fig, axis = plt.subplots(figsize=(8, 6))
    axis.boxplot([on_time, delayed], tick_labels=["No prazo", "Atrasado"], patch_artist=True)
    axis.set_title("Distribuição do review_score por status de atraso")
    axis.set_ylabel("Review Score")
    axis.grid(alpha=0.3)
    plt.tight_layout()
    fig.savefig(file_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_scatter_bubble(
    dataframe: pd.DataFrame,
    x_column: str,
    y_column: str,
    size_column: str,
    file_path: Path,
    title: str,
    xlabel: str,
    ylabel: str,
    x_percent: bool = False,
) -> None:
    plot_df = dataframe.dropna(subset=[x_column, y_column, size_column]).copy()
    if plot_df.empty:
        warn(f"Sem dados para dispersão: {title}")
        return

    sizes = (plot_df[size_column] - plot_df[size_column].min()) + 1
    sizes = (sizes / sizes.max()) * 800 if sizes.max() > 0 else np.full(len(plot_df), 200)

    fig, axis = plt.subplots(figsize=(12, 6))
    scatter = axis.scatter(
        plot_df[x_column],
        plot_df[y_column],
        s=sizes,
        alpha=0.6,
        c=plot_df[size_column],
        cmap="viridis",
        edgecolor="black",
        linewidth=0.5,
    )
    axis.set_title(title)
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    axis.grid(alpha=0.3)
    if x_percent:
        axis.xaxis.set_major_formatter(PercentFormatter(1.0))
    plt.colorbar(scatter, ax=axis, label=size_column)
    plt.tight_layout()
    fig.savefig(file_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_bar_chart(
    dataframe: pd.DataFrame,
    x_column: str,
    y_column: str,
    file_path: Path,
    title: str,
    xlabel: str,
    ylabel: str,
    top_n: int = 10,
    horizontal: bool = False,
    currency_axis: bool = False,
) -> None:
    plot_df = dataframe.head(top_n).copy()
    if plot_df.empty:
        warn(f"Sem dados para gráfico de barras: {title}")
        return

    fig, axis = plt.subplots(figsize=(12, 6))
    if horizontal:
        axis.barh(plot_df[x_column].astype(str), plot_df[y_column], color="#1f77b4")
        axis.invert_yaxis()
        axis.set_xlabel(ylabel)
        axis.set_ylabel(xlabel)
        if currency_axis:
            axis.xaxis.set_major_formatter(FuncFormatter(currency_axis_formatter))
    else:
        axis.bar(plot_df[x_column].astype(str), plot_df[y_column], color="#1f77b4")
        axis.set_xlabel(xlabel)
        axis.set_ylabel(ylabel)
        axis.tick_params(axis="x", rotation=45)
        if currency_axis:
            axis.yaxis.set_major_formatter(FuncFormatter(currency_axis_formatter))

    axis.set_title(title)
    axis.grid(alpha=0.3, axis="y" if not horizontal else "x")
    plt.tight_layout()
    fig.savefig(file_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_group_ticket_bar(
    values: Dict[str, float],
    file_path: Path,
    title: str,
) -> None:
    if not values:
        warn(f"Sem dados para gráfico: {title}")
        return

    labels = list(values.keys())
    numbers = list(values.values())

    fig, axis = plt.subplots(figsize=(8, 6))
    axis.bar(labels, numbers, color=["#1f77b4", "#ff7f0e"])
    axis.set_title(title)
    axis.set_ylabel("Ticket médio")
    axis.yaxis.set_major_formatter(FuncFormatter(currency_axis_formatter))
    axis.grid(alpha=0.3, axis="y")
    plt.tight_layout()
    fig.savefig(file_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_correlation_matrix(
    dataframe: pd.DataFrame,
    columns: List[str],
    labels: List[str],
    file_path: Path,
    title: str,
) -> None:
    plot_df = dataframe[columns].dropna().copy()
    if plot_df.empty:
        warn("Sem dados suficientes para matriz de correlação.")
        return

    corr = plot_df.corr()
    fig, axis = plt.subplots(figsize=(8, 6))
    im = axis.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
    axis.set_xticks(range(len(labels)))
    axis.set_yticks(range(len(labels)))
    axis.set_xticklabels(labels, rotation=45, ha="right")
    axis.set_yticklabels(labels)
    axis.set_title(title)

    for row in range(len(labels)):
        for col in range(len(labels)):
            axis.text(col, row, f"{corr.values[row, col]:.2f}", ha="center", va="center", color="black")

    fig.colorbar(im, ax=axis)
    plt.tight_layout()
    fig.savefig(file_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_regression_coefficients(regression_results: pd.DataFrame, file_path: Path) -> None:
    plot_df = regression_results.loc[regression_results["term"] != "const"].copy()
    if plot_df.empty:
        warn("Sem coeficientes para gráfico de regressão.")
        return

    colors = ["#2ca02c" if coefficient >= 0 else "#d62728" for coefficient in plot_df["coef"]]
    fig, axis = plt.subplots(figsize=(10, 6))
    axis.bar(plot_df["term"], plot_df["coef"], color=colors)
    axis.axhline(0, color="black", linewidth=1)
    axis.set_title("Coeficientes da regressão para crescimento de receita M+1")
    axis.set_ylabel("Coeficiente (p.p. de crescimento por 1 p.p. do driver)")
    axis.tick_params(axis="x", rotation=35)
    axis.grid(alpha=0.3, axis="y")
    plt.tight_layout()
    fig.savefig(file_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_historical_vs_baseline(
    regression_df: pd.DataFrame,
    file_path: Path,
) -> None:
    plot_df = regression_df.dropna(subset=["next_month_revenue", "predicted_next_month_revenue"]).copy()
    if plot_df.empty:
        warn("Sem dados suficientes para histórico vs baseline.")
        return

    fig, axis = plt.subplots(figsize=(12, 6))
    axis.plot(
        plot_df["next_month_label"],
        plot_df["next_month_revenue"],
        marker="o",
        linewidth=2,
        label="Receita observada M+1",
    )
    axis.plot(
        plot_df["next_month_label"],
        plot_df["predicted_next_month_revenue"],
        marker="o",
        linewidth=2,
        linestyle="--",
        label="Baseline estatístico M+1",
    )
    axis.set_title("Receita histórica observada vs baseline estatístico")
    axis.set_xlabel("Ano-Mês")
    axis.set_ylabel("Receita")
    axis.yaxis.set_major_formatter(FuncFormatter(currency_axis_formatter))
    axis.tick_params(axis="x", rotation=45)
    axis.grid(alpha=0.3)
    axis.legend()
    plt.tight_layout()
    fig.savefig(file_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_baseline_vs_scenario(
    baseline_revenue: float,
    scenario_revenue: float,
    label: str,
    file_path: Path,
) -> None:
    fig, axis = plt.subplots(figsize=(8, 6))
    axis.bar(["Baseline M+1", "Cenário simulado M+1"], [baseline_revenue, scenario_revenue], color=["#1f77b4", "#2ca02c"])
    axis.set_title(f"Comparação baseline vs cenário simulado ({label})")
    axis.set_ylabel("Receita prevista")
    axis.yaxis.set_major_formatter(FuncFormatter(currency_axis_formatter))
    axis.grid(alpha=0.3, axis="y")
    plt.tight_layout()
    fig.savefig(file_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def generate_candlestick(daily_revenue: pd.DataFrame, output_dir: Path, complete_bounds: Dict[str, Any]) -> None:
    if go is None or make_subplots is None:
        warn("Plotly não está disponível. O candlestick mensal será ignorado.")
        return

    plot_df = daily_revenue.dropna(subset=["purchase_date", "daily_revenue"]).copy()
    if plot_df.empty:
        warn("Sem dados diários para candlestick.")
        return

    plot_df["year_month_period"] = plot_df["purchase_date"].dt.to_period("M")
    plot_df = filter_complete_months(plot_df, "year_month_period", complete_bounds)
    plot_df = plot_df.sort_values("purchase_date")
    if plot_df.empty:
        warn("Sem meses completos para candlestick.")
        return

    monthly_candle = (
        plot_df.groupby("year_month_period", as_index=False)
        .agg(
            open=("daily_revenue", "first"),
            high=("daily_revenue", "max"),
            low=("daily_revenue", "min"),
            close=("daily_revenue", "last"),
            volume=("daily_orders", "sum"),
        )
    )
    monthly_candle["date"] = monthly_candle["year_month_period"].dt.to_timestamp()
    monthly_candle["label"] = monthly_candle["year_month_period"].astype(str)

    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.7, 0.3],
    )
    figure.add_trace(
        go.Candlestick(
            x=monthly_candle["date"],
            open=monthly_candle["open"],
            high=monthly_candle["high"],
            low=monthly_candle["low"],
            close=monthly_candle["close"],
            name="Receita mensal",
        ),
        row=1,
        col=1,
    )
    figure.add_trace(
        go.Bar(
            x=monthly_candle["date"],
            y=monthly_candle["volume"],
            name="Pedidos no mês",
            marker_color="#1f77b4",
        ),
        row=2,
        col=1,
    )
    figure.update_layout(
        title="Candlestick de receita mensal e volume de pedidos",
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        height=800,
    )

    html_path = output_dir / "candlestick_receita_mensal.html"
    figure.write_html(html_path)
    info(f"Candlestick salvo em: {html_path}")

    try:
        png_path = output_dir / "candlestick_receita_mensal.png"
        pio.write_image(figure, png_path, width=1400, height=800, scale=2)
        info(f"Imagem estática do candlestick salva em: {png_path}")
    except Exception as exc:  # pragma: no cover - depende de kaleido
        warn(
            "Não foi possível gerar imagem estática do candlestick. "
            f"O HTML interativo foi salvo normalmente. Motivo: {exc}"
        )


def run_two_group_tests(series_a: pd.Series, series_b: pd.Series, label: str) -> Dict[str, Any]:
    group_a = pd.Series(series_a).dropna()
    group_b = pd.Series(series_b).dropna()
    results = {
        "label": label,
        "n_group_a": int(group_a.shape[0]),
        "n_group_b": int(group_b.shape[0]),
        "mean_group_a": float(group_a.mean()) if not group_a.empty else np.nan,
        "mean_group_b": float(group_b.mean()) if not group_b.empty else np.nan,
        "ttest_pvalue": np.nan,
        "mannwhitney_pvalue": np.nan,
    }

    if len(group_a) < 2 or len(group_b) < 2:
        warn(f"Amostra insuficiente para testes em {label}.")
        return results

    if len(group_a) < MIN_SAMPLE_WARN or len(group_b) < MIN_SAMPLE_WARN:
        warn(f"Amostra pequena para testes em {label}. Interpretar p-values com cautela.")

    if stats is None:
        warn("SciPy não está disponível. Testes estatísticos de grupos serão omitidos.")
        return results

    try:
        ttest = stats.ttest_ind(group_a, group_b, equal_var=False, nan_policy="omit")
        results["ttest_pvalue"] = float(ttest.pvalue)
    except Exception as exc:
        warn(f"Falha no teste t para {label}: {exc}")

    try:
        mann_whitney = stats.mannwhitneyu(group_a, group_b, alternative="two-sided")
        results["mannwhitney_pvalue"] = float(mann_whitney.pvalue)
    except Exception as exc:
        warn(f"Falha no teste Mann-Whitney para {label}: {exc}")

    return results


def run_spearman_test(x_series: pd.Series, y_series: pd.Series, label: str) -> Dict[str, Any]:
    valid = pd.DataFrame({"x": x_series, "y": y_series}).dropna()
    if len(valid) < 3:
        warn(f"Amostra insuficiente para Spearman em {label}.")
        return {"label": label, "n": int(len(valid)), "rho": np.nan, "pvalue": np.nan}

    if stats is None:
        warn("SciPy não está disponível. Correlação de Spearman será omitida.")
        return {"label": label, "n": int(len(valid)), "rho": np.nan, "pvalue": np.nan}

    try:
        rho, pvalue = stats.spearmanr(valid["x"], valid["y"])
        return {"label": label, "n": int(len(valid)), "rho": float(rho), "pvalue": float(pvalue)}
    except Exception as exc:
        warn(f"Falha ao calcular Spearman em {label}: {exc}")
        return {"label": label, "n": int(len(valid)), "rho": np.nan, "pvalue": np.nan}


def fit_simple_ols(
    dataframe: pd.DataFrame,
    target_column: str,
    feature_columns: List[str],
) -> Tuple[Optional[Any], pd.DataFrame]:
    if sm is None:
        warn("statsmodels não está disponível. Modelos OLS não serão executados.")
        return None, pd.DataFrame()

    valid = dataframe[feature_columns + [target_column]].dropna().copy()
    if len(valid) <= len(feature_columns) + 2:
        warn("Amostra insuficiente para regressão OLS.")
        return None, pd.DataFrame()

    x_matrix = sm.add_constant(valid[feature_columns], has_constant="add")
    model = sm.OLS(valid[target_column], x_matrix).fit()

    results_df = pd.DataFrame(
        {
            "term": model.params.index,
            "coef": model.params.values,
            "pvalue": model.pvalues.values,
            "stderr": model.bse.values,
            "tvalue": model.tvalues.values,
            "r_squared": model.rsquared,
            "adj_r_squared": model.rsquared_adj,
            "n_obs": int(model.nobs),
        }
    )
    return model, results_df


def fit_logistic_model(
    dataframe: pd.DataFrame,
    target_column: str,
    feature_column: str,
) -> Dict[str, Any]:
    result = {
        "status": "not_run",
        "n_obs": 0,
        "coef": np.nan,
        "pvalue": np.nan,
        "odds_ratio": np.nan,
        "pseudo_r2": np.nan,
    }

    if sm is None:
        warn("statsmodels não está disponível. Regressão logística será omitida.")
        result["status"] = "statsmodels_unavailable"
        return result

    valid = dataframe[[target_column, feature_column]].dropna().copy()
    result["n_obs"] = int(len(valid))
    if valid.empty or valid[target_column].nunique() < 2:
        warn("Sem diversidade suficiente no target para regressão logística.")
        result["status"] = "insufficient_variance"
        return result

    event_count = int(valid[target_column].sum())
    non_event_count = int(len(valid) - event_count)
    if min(event_count, non_event_count) < 15:
        warn("Poucos eventos para regressão logística. Interprete os coeficientes com cautela.")

    try:
        x_matrix = sm.add_constant(valid[[feature_column]], has_constant="add")
        model = sm.Logit(valid[target_column], x_matrix).fit(disp=0)
        result.update(
            {
                "status": "ok",
                "coef": float(model.params[feature_column]),
                "pvalue": float(model.pvalues[feature_column]),
                "odds_ratio": float(np.exp(model.params[feature_column])),
                "pseudo_r2": float(model.prsquared),
            }
        )
    except Exception as exc:
        warn(f"Falha na regressão logística: {exc}")
        result["status"] = "failed"

    return result


def analyze_growth_and_concentration(prepared: Dict[str, Any], output_dirs: Dict[str, Path]) -> Dict[str, Any]:
    monthly = prepared["monthly_metrics"].copy()
    item_level = prepared["item_level"].copy()

    plot_time_series(
        monthly,
        "year_month",
        "revenue_month",
        output_dirs["charts"] / "receita_mensal.png",
        "Receita mensal",
        "Receita",
        currency_axis=True,
    )
    plot_time_series(
        monthly,
        "year_month",
        "orders_month",
        output_dirs["charts"] / "pedidos_mensais.png",
        "Pedidos mensais",
        "Pedidos",
    )
    plot_time_series(
        monthly,
        "year_month",
        "avg_ticket_month",
        output_dirs["charts"] / "ticket_medio_mensal.png",
        "Ticket médio mensal",
        "Ticket médio",
        currency_axis=True,
    )

    revenue_control = plot_control_chart_continuous(
        monthly,
        "year_month",
        "revenue_month",
        output_dirs["charts"] / "controle_receita_mensal.png",
        "Gráfico de controle da receita mensal",
        "Receita",
        clamp_lower_zero=True,
    )
    orders_control = plot_control_chart_continuous(
        monthly,
        "year_month",
        "orders_month",
        output_dirs["charts"] / "controle_pedidos_mensais.png",
        "Gráfico de controle do volume de pedidos",
        "Pedidos",
        clamp_lower_zero=True,
    )

    city_concentration = compute_concentration_table(item_level, "customer_city", "item_revenue")
    seller_concentration = compute_concentration_table(item_level, "seller_id", "item_revenue")
    category_concentration = compute_concentration_table(item_level, "product_category_final", "item_revenue")
    state_revenue = compute_concentration_table(item_level, "customer_state", "item_revenue")

    save_pareto_chart(
        city_concentration,
        "customer_city",
        "item_revenue",
        output_dirs["charts"] / "pareto_receita_cidade.png",
        "Pareto de receita por cidade",
    )
    save_pareto_chart(
        seller_concentration,
        "seller_id",
        "item_revenue",
        output_dirs["charts"] / "pareto_receita_seller.png",
        "Pareto de receita por seller",
    )
    save_pareto_chart(
        category_concentration,
        "product_category_final",
        "item_revenue",
        output_dirs["charts"] / "pareto_receita_categoria.png",
        "Pareto de receita por categoria",
    )

    save_dataframe(city_concentration, output_dirs["tables"] / "concentracao_receita_cidade.csv")
    save_dataframe(seller_concentration, output_dirs["tables"] / "concentracao_receita_seller.csv")
    save_dataframe(category_concentration, output_dirs["tables"] / "concentracao_receita_categoria.csv")
    save_dataframe(state_revenue, output_dirs["tables"] / "receita_por_estado.csv")

    return {
        "monthly": monthly,
        "revenue_control": revenue_control,
        "orders_control": orders_control,
        "city_concentration": city_concentration,
        "seller_concentration": seller_concentration,
        "category_concentration": category_concentration,
        "state_revenue": state_revenue,
    }


def analyze_logistics_and_satisfaction(prepared: Dict[str, Any], output_dirs: Dict[str, Path]) -> Dict[str, Any]:
    order_level = prepared["order_level"].copy()
    monthly = prepared["monthly_metrics"].copy()

    delivered_reviewed = order_level.loc[
        order_level["delivered_with_valid_dates"] & order_level["review_score"].notna()
    ].copy()
    if delivered_reviewed.empty:
        warn("Sem dados suficientes para análise de logística e satisfação.")
        return {}

    delayed_reviews = delivered_reviewed.loc[delivered_reviewed["is_delayed"], "review_score"]
    on_time_reviews = delivered_reviewed.loc[~delivered_reviewed["is_delayed"], "review_score"]

    score_gap_pct = (
        safe_divide(delayed_reviews.mean() - on_time_reviews.mean(), on_time_reviews.mean()) * 100
        if not on_time_reviews.empty
        else np.nan
    )

    group_tests = run_two_group_tests(on_time_reviews, delayed_reviews, "review_score por atraso")
    spearman_delay_vs_review = run_spearman_test(
        delivered_reviewed["delay_days"],
        delivered_reviewed["review_score"],
        "dias de atraso vs review_score",
    )

    plot_time_series(
        monthly,
        "year_month",
        "late_rate",
        output_dirs["charts"] / "taxa_atraso_mensal.png",
        "Taxa mensal de pedidos atrasados",
        "Taxa de atraso",
        percent_axis=True,
    )
    late_rate_control = plot_p_chart(
        monthly,
        "year_month",
        "delayed_orders",
        "delivered_orders_valid",
        "late_rate",
        output_dirs["charts"] / "controle_taxa_atraso.png",
        "Gráfico de controle da taxa de atraso",
        "Taxa de atraso",
    )
    plot_time_series(
        monthly,
        "year_month",
        "avg_review_score",
        output_dirs["charts"] / "nota_media_mensal.png",
        "Nota média mensal",
        "Review Score médio",
    )
    review_score_control = plot_control_chart_continuous(
        monthly,
        "year_month",
        "avg_review_score",
        output_dirs["charts"] / "controle_nota_media.png",
        "Gráfico de controle da nota média mensal",
        "Review Score médio",
    )
    plot_boxplot_delay_vs_review(
        delivered_reviewed,
        output_dirs["charts"] / "boxplot_review_por_atraso.png",
    )

    seller_delay_review = (
        prepared["seller_order"]
        .loc[
            prepared["seller_order"]["delivered_with_valid_dates"]
            & prepared["seller_order"]["review_score"].notna()
        ]
        .groupby("seller_id", as_index=False)
        .agg(
            seller_orders=("order_id", "nunique"),
            avg_delay_days=("delay_days", "mean"),
            avg_review_score=("review_score", "mean"),
        )
    )
    seller_delay_review = seller_delay_review.loc[seller_delay_review["seller_orders"] >= SELLER_MIN_ORDERS_FOR_RISK]
    plot_scatter_bubble(
        seller_delay_review,
        "avg_delay_days",
        "avg_review_score",
        "seller_orders",
        output_dirs["charts"] / "dispersao_atraso_nota_seller.png",
        "Dispersão entre atraso médio e nota média por seller",
        "Atraso médio (dias)",
        "Nota média",
        x_percent=False,
    )

    return {
        "delivered_reviewed": delivered_reviewed,
        "general_mean_review": float(delivered_reviewed["review_score"].mean()),
        "on_time_mean_review": float(on_time_reviews.mean()) if not on_time_reviews.empty else np.nan,
        "delayed_mean_review": float(delayed_reviews.mean()) if not delayed_reviews.empty else np.nan,
        "review_gap_pct": float(score_gap_pct) if not pd.isna(score_gap_pct) else np.nan,
        "review_gap_points": float(on_time_reviews.mean() - delayed_reviews.mean())
        if not on_time_reviews.empty and not delayed_reviews.empty
        else np.nan,
        "avg_delay_days": float(delivered_reviewed["delay_days"].mean()),
        "group_tests": group_tests,
        "spearman": spearman_delay_vs_review,
        "late_rate_control": late_rate_control,
        "review_score_control": review_score_control,
    }


def analyze_seller_risk(
    prepared: Dict[str, Any],
    logistics_results: Dict[str, Any],
    output_dirs: Dict[str, Path],
) -> Dict[str, Any]:
    seller_order = prepared["seller_order"].copy()
    delivered = seller_order.loc[seller_order["delivered_with_valid_dates"]].copy()
    if delivered.empty:
        warn("Sem dados suficientes para análise de risco por seller.")
        return {}

    base = (
        delivered.groupby("seller_id", as_index=False)
        .agg(
            seller_orders=("order_id", "nunique"),
            seller_revenue=("seller_order_revenue", "sum"),
            delayed_orders=("is_delayed", "sum"),
            avg_delay_days=("delay_days", "mean"),
            avg_lead_time_days=("lead_time_days", "mean"),
            avg_review_score=("review_score", "mean"),
        )
    )
    late_reviews = (
        delivered.loc[delivered["is_delayed"] & delivered["review_score"].notna()]
        .groupby("seller_id")["review_score"]
        .mean()
        .rename("avg_late_review_score")
    )
    on_time_reviews = (
        delivered.loc[~delivered["is_delayed"] & delivered["review_score"].notna()]
        .groupby("seller_id")["review_score"]
        .mean()
        .rename("avg_on_time_review_score")
    )

    seller_risk = base.merge(late_reviews, on="seller_id", how="left")
    seller_risk = seller_risk.merge(on_time_reviews, on="seller_id", how="left")
    seller_risk["late_rate"] = seller_risk["delayed_orders"] / seller_risk["seller_orders"]
    global_gap = np.nan
    if logistics_results:
        global_gap = logistics_results["on_time_mean_review"] - logistics_results["delayed_mean_review"]
    global_gap = float(global_gap) if not pd.isna(global_gap) else 0.0
    seller_risk["impact_on_review"] = (
        seller_risk["avg_on_time_review_score"] - seller_risk["avg_late_review_score"]
    )
    seller_risk["impact_on_review"] = seller_risk["impact_on_review"].where(
        seller_risk["impact_on_review"].notna(),
        global_gap,
    )
    seller_risk["impact_on_review"] = seller_risk["impact_on_review"].clip(lower=0)
    seller_risk["risk_score"] = (
        seller_risk["seller_orders"] * seller_risk["late_rate"] * seller_risk["impact_on_review"]
    )
    seller_risk["eligible_risk_ranking"] = seller_risk["seller_orders"] >= SELLER_MIN_ORDERS_FOR_RISK
    seller_risk = seller_risk.sort_values(["eligible_risk_ranking", "risk_score"], ascending=[False, False]).reset_index(drop=True)
    seller_risk["risk_rank"] = np.arange(1, len(seller_risk) + 1)

    save_dataframe(seller_risk, output_dirs["tables"] / "seller_risk_ranking.csv")

    eligible = seller_risk.loc[seller_risk["eligible_risk_ranking"]].copy()
    if eligible.empty:
        warn("Nenhum seller atingiu o volume mínimo para ranking detrator. O ranking mostrará todos os sellers.")
        eligible = seller_risk.copy()

    plot_bar_chart(
        eligible,
        "seller_id",
        "risk_score",
        output_dirs["charts"] / "top_10_sellers_detratores.png",
        "Top 10 sellers detratores",
        "Seller",
        "Score de risco",
        top_n=10,
    )
    seller_risk_pareto = compute_concentration_table(eligible, "seller_id", "risk_score")
    save_pareto_chart(
        seller_risk_pareto,
        "seller_id",
        "risk_score",
        output_dirs["charts"] / "pareto_sellers_detratores.png",
        "Pareto do score de risco dos sellers detratores",
        top_n=15,
    )
    plot_scatter_bubble(
        eligible,
        "late_rate",
        "seller_orders",
        "impact_on_review",
        output_dirs["charts"] / "dispersao_volume_vs_taxa_atraso_seller.png",
        "Volume de pedidos vs taxa de atraso por seller",
        "Taxa de atraso",
        "Volume de pedidos",
        x_percent=True,
    )

    return {"seller_risk": seller_risk, "eligible": eligible}


def analyze_repurchase(prepared: Dict[str, Any], output_dirs: Dict[str, Path]) -> Dict[str, Any]:
    order_level = prepared["order_level"].copy()
    item_level = prepared["item_level"].copy()
    customer_key = prepared["customer_key"]

    customer_summary = (
        order_level.groupby(customer_key, as_index=False)
        .agg(
            customer_orders=("order_id", "nunique"),
            customer_revenue=("order_revenue", "sum"),
            avg_order_value=("order_revenue", "mean"),
            first_purchase=("order_purchase_timestamp", "min"),
        )
    )
    customer_summary["has_repurchase"] = customer_summary["customer_orders"] > 1

    ticket_tests = run_two_group_tests(
        customer_summary.loc[customer_summary["has_repurchase"], "avg_order_value"],
        customer_summary.loc[~customer_summary["has_repurchase"], "avg_order_value"],
        "ticket médio por grupo de cliente",
    )

    total_customers = customer_summary[customer_key].nunique()
    pct_customers_with_repurchase = customer_summary["has_repurchase"].mean() * 100
    revenue_repurchase_customers = customer_summary.loc[
        customer_summary["has_repurchase"], "customer_revenue"
    ].sum()
    avg_ticket_repurchase_customers = customer_summary.loc[
        customer_summary["has_repurchase"], "avg_order_value"
    ].mean()
    avg_ticket_non_repurchase_customers = customer_summary.loc[
        ~customer_summary["has_repurchase"], "avg_order_value"
    ].mean()

    first_purchase_month = customer_summary["first_purchase"].dt.to_period("M")
    monthly_new = (
        customer_summary.assign(first_purchase_month=first_purchase_month)
        .groupby("first_purchase_month")[customer_key]
        .nunique()
        .rename("new_customers")
        .reset_index()
        .rename(columns={"first_purchase_month": "year_month_period"})
    )
    monthly_repurchase = (
        order_level.loc[order_level["is_repurchase_order"]]
        .groupby("year_month_period")[customer_key]
        .nunique()
        .rename("repurchase_customers")
        .reset_index()
    )
    monthly_total = (
        order_level.groupby("year_month_period")[customer_key]
        .nunique()
        .rename("unique_customers")
        .reset_index()
    )
    monthly_customer_analysis = monthly_total.merge(monthly_new, on="year_month_period", how="left")
    monthly_customer_analysis = monthly_customer_analysis.merge(
        monthly_repurchase,
        on="year_month_period",
        how="left",
    )
    monthly_customer_analysis["new_customers"] = monthly_customer_analysis["new_customers"].fillna(0)
    monthly_customer_analysis["repurchase_customers"] = monthly_customer_analysis["repurchase_customers"].fillna(0)
    monthly_customer_analysis["repurchase_customer_rate"] = np.where(
        monthly_customer_analysis["unique_customers"] > 0,
        monthly_customer_analysis["repurchase_customers"] / monthly_customer_analysis["unique_customers"],
        np.nan,
    )
    monthly_customer_analysis["year_month"] = monthly_customer_analysis["year_month_period"].astype(str)
    monthly_customer_analysis = filter_complete_months(
        monthly_customer_analysis,
        "year_month_period",
        prepared["complete_month_bounds"],
    )
    monthly_customer_analysis = monthly_customer_analysis.sort_values("year_month_period")

    segment_monthly_ticket = (
        order_level.groupby(["year_month_period", "customer_has_repurchase"])["order_revenue"]
        .mean()
        .reset_index()
    )
    segment_pivot = segment_monthly_ticket.pivot(
        index="year_month_period",
        columns="customer_has_repurchase",
        values="order_revenue",
    ).reset_index()
    segment_pivot = segment_pivot.rename(
        columns={
            False: "avg_ticket_non_repurchase_customers",
            True: "avg_ticket_repurchase_customers",
        }
    )
    monthly_customer_analysis = monthly_customer_analysis.merge(segment_pivot, on="year_month_period", how="left")

    repurchase_customer_ids = set(
        customer_summary.loc[customer_summary["has_repurchase"], customer_key]
    )
    repurchase_items = item_level.loc[item_level[customer_key].isin(repurchase_customer_ids)].copy()
    repurchase_category_concentration = compute_concentration_table(
        repurchase_items,
        "product_category_final",
        "item_revenue",
    )

    save_dataframe(monthly_customer_analysis, output_dirs["tables"] / "customer_repurchase_analysis.csv")
    save_dataframe(customer_summary, output_dirs["tables"] / "customer_summary_repurchase.csv")
    save_dataframe(
        repurchase_category_concentration,
        output_dirs["tables"] / "categorias_recompra.csv",
    )

    plot_time_series(
        monthly_customer_analysis,
        "year_month",
        "new_customers",
        output_dirs["charts"] / "novos_vs_recompra_mes.png",
        "Novos clientes por mês",
        "Clientes",
    )
    # Sobrepõe a série de recompra no mesmo arquivo para facilitar leitura executiva.
    fig, axis = plt.subplots(figsize=(12, 6))
    axis.plot(
        monthly_customer_analysis["year_month"],
        monthly_customer_analysis["new_customers"],
        marker="o",
        linewidth=2,
        label="Novos clientes",
    )
    axis.plot(
        monthly_customer_analysis["year_month"],
        monthly_customer_analysis["repurchase_customers"],
        marker="o",
        linewidth=2,
        label="Clientes com recompra",
    )
    axis.set_title("Novos clientes vs clientes com recompra por mês")
    axis.set_xlabel("Ano-Mês")
    axis.set_ylabel("Clientes")
    axis.grid(alpha=0.3)
    axis.tick_params(axis="x", rotation=45)
    axis.legend()
    plt.tight_layout()
    fig.savefig(output_dirs["charts"] / "novos_vs_recompra_mes.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    plot_group_ticket_bar(
        {
            "Com recompra": avg_ticket_repurchase_customers,
            "Sem recompra": avg_ticket_non_repurchase_customers,
        },
        output_dirs["charts"] / "ticket_medio_grupo_recompra.png",
        "Ticket médio por grupo de clientes",
    )
    save_pareto_chart(
        repurchase_category_concentration,
        "product_category_final",
        "item_revenue",
        output_dirs["charts"] / "categorias_recompra.png",
        "Categorias mais compradas por clientes com recompra",
    )

    return {
        "customer_summary": customer_summary,
        "monthly_customer_analysis": monthly_customer_analysis,
        "repurchase_category_concentration": repurchase_category_concentration,
        "ticket_tests": ticket_tests,
        "total_customers": int(total_customers),
        "avg_orders_per_customer": float(customer_summary["customer_orders"].mean()),
        "pct_customers_with_repurchase": float(pct_customers_with_repurchase),
        "revenue_repurchase_customers": float(revenue_repurchase_customers),
        "avg_ticket_repurchase_customers": float(avg_ticket_repurchase_customers),
        "avg_ticket_non_repurchase_customers": float(avg_ticket_non_repurchase_customers),
    }


def analyze_strategic_sellers_and_regression(
    prepared: Dict[str, Any],
    output_dirs: Dict[str, Path],
) -> Dict[str, Any]:
    seller_order = prepared["seller_order"].copy()
    monthly = prepared["monthly_metrics"].copy()

    seller_performance = (
        seller_order.groupby("seller_id", as_index=False)
        .agg(
            total_revenue=("seller_order_revenue", "sum"),
            total_orders=("order_id", "nunique"),
            total_items=("seller_item_count", "sum"),
        )
        .sort_values("total_revenue", ascending=False)
    )

    for metric, weight in [("total_revenue", 0.5), ("total_orders", 0.3), ("total_items", 0.2)]:
        seller_performance[f"{metric}_pct_rank"] = seller_performance[metric].rank(pct=True, method="average")
        seller_performance[f"{metric}_weight"] = seller_performance[f"{metric}_pct_rank"] * weight

    seller_performance["strategic_score"] = seller_performance[
        ["total_revenue_weight", "total_orders_weight", "total_items_weight"]
    ].sum(axis=1)
    top_n = min(10, len(seller_performance))
    seller_performance["strategic_seller"] = False
    strategic_ids = seller_performance.nlargest(top_n, "strategic_score")["seller_id"].tolist()
    seller_performance.loc[seller_performance["seller_id"].isin(strategic_ids), "strategic_seller"] = True

    monthly_seller = (
        seller_order.groupby(["year_month_period", "seller_id"], as_index=False)
        .agg(
            monthly_seller_revenue=("seller_order_revenue", "sum"),
            monthly_seller_orders=("order_id", "nunique"),
            monthly_seller_items=("seller_item_count", "sum"),
        )
        .merge(
            seller_performance[["seller_id", "strategic_seller", "strategic_score"]],
            on="seller_id",
            how="left",
        )
    )

    monthly_total = (
        monthly_seller.groupby("year_month_period", as_index=False)
        .agg(
            total_revenue=("monthly_seller_revenue", "sum"),
            total_orders=("monthly_seller_orders", "sum"),
            total_items=("monthly_seller_items", "sum"),
        )
    )
    monthly_strategic = (
        monthly_seller.loc[monthly_seller["strategic_seller"]]
        .groupby("year_month_period", as_index=False)
        .agg(
            strategic_revenue=("monthly_seller_revenue", "sum"),
            strategic_orders=("monthly_seller_orders", "sum"),
            strategic_items=("monthly_seller_items", "sum"),
        )
    )

    strategic_monthly_analysis = monthly_total.merge(monthly_strategic, on="year_month_period", how="left")
    for column in ["strategic_revenue", "strategic_orders", "strategic_items"]:
        strategic_monthly_analysis[column] = strategic_monthly_analysis[column].fillna(0)

    strategic_monthly_analysis["strategic_revenue_share"] = np.where(
        strategic_monthly_analysis["total_revenue"] > 0,
        strategic_monthly_analysis["strategic_revenue"] / strategic_monthly_analysis["total_revenue"],
        np.nan,
    )
    strategic_monthly_analysis["strategic_orders_share"] = np.where(
        strategic_monthly_analysis["total_orders"] > 0,
        strategic_monthly_analysis["strategic_orders"] / strategic_monthly_analysis["total_orders"],
        np.nan,
    )
    strategic_monthly_analysis["year_month"] = strategic_monthly_analysis["year_month_period"].astype(str)
    strategic_monthly_analysis = filter_complete_months(
        strategic_monthly_analysis,
        "year_month_period",
        prepared["complete_month_bounds"],
    )
    strategic_monthly_analysis = strategic_monthly_analysis.sort_values("year_month_period")

    monthly_enriched = monthly.merge(
        strategic_monthly_analysis[
            [
                "year_month_period",
                "strategic_revenue_share",
                "strategic_orders_share",
                "strategic_revenue",
                "strategic_orders",
            ]
        ],
        on="year_month_period",
        how="left",
    )
    monthly_enriched["strategic_revenue_share"] = monthly_enriched["strategic_revenue_share"].fillna(0)
    monthly_enriched["strategic_orders_share"] = monthly_enriched["strategic_orders_share"].fillna(0)

    save_dataframe(seller_performance, output_dirs["tables"] / "strategic_seller_definition.csv")
    save_dataframe(strategic_monthly_analysis, output_dirs["tables"] / "strategic_seller_monthly_analysis.csv")

    strategic_global_share = safe_divide(
        seller_performance.loc[seller_performance["strategic_seller"], "total_revenue"].sum(),
        seller_performance["total_revenue"].sum(),
    )
    latest_share = (
        strategic_monthly_analysis.iloc[-1]["strategic_revenue_share"]
        if not strategic_monthly_analysis.empty
        else np.nan
    )

    return {
        "seller_performance": seller_performance,
        "strategic_monthly_analysis": strategic_monthly_analysis,
        "monthly_enriched": monthly_enriched,
        "strategic_global_share": float(strategic_global_share) if not pd.isna(strategic_global_share) else np.nan,
        "strategic_latest_share": float(latest_share) if not pd.isna(latest_share) else np.nan,
        "strategic_ids": strategic_ids,
    }


def build_monthly_business_output(monthly_enriched: pd.DataFrame) -> pd.DataFrame:
    output = monthly_enriched.copy()
    output["late_rate_pct"] = output["late_rate"] * 100
    output["repurchase_customer_rate_pct"] = output["repurchase_customer_rate"] * 100
    output["negative_review_rate_pct"] = output["negative_review_rate"] * 100
    output["strategic_revenue_share_pct"] = output["strategic_revenue_share"] * 100
    output["strategic_orders_share_pct"] = output["strategic_orders_share"] * 100
    output = output.rename(
        columns={
            "year_month": "ano_mes",
            "revenue_month": "receita_mensal",
            "orders_month": "pedidos_mensais",
            "avg_ticket_month": "ticket_medio_mensal",
            "revenue_mom_pct": "variacao_receita_mom_pct",
            "orders_mom_pct": "variacao_pedidos_mom_pct",
            "ticket_mom_pct": "variacao_ticket_mom_pct",
            "delivered_orders_valid": "pedidos_entregues_validos",
            "delayed_orders": "pedidos_atrasados",
            "late_rate_pct": "taxa_atraso_pct",
            "avg_delay_days": "atraso_medio_dias",
            "avg_lead_time_days": "lead_time_medio_dias",
            "avg_review_score": "nota_media_mensal",
            "negative_review_rate_pct": "taxa_reviews_negativas_pct",
            "unique_customers": "clientes_unicos",
            "new_customers": "novos_clientes",
            "repurchase_customers": "clientes_com_recompra",
            "repurchase_customer_rate_pct": "taxa_clientes_com_recompra_pct",
            "repurchase_order_rate": "taxa_pedidos_recompra",
            "strategic_revenue_share_pct": "percentual_receita_sellers_estrategicos",
            "strategic_orders_share_pct": "percentual_pedidos_sellers_estrategicos",
        }
    )
    columns_order = [
        "ano_mes",
        "receita_mensal",
        "pedidos_mensais",
        "ticket_medio_mensal",
        "variacao_receita_mom_pct",
        "variacao_pedidos_mom_pct",
        "variacao_ticket_mom_pct",
        "pedidos_entregues_validos",
        "pedidos_atrasados",
        "taxa_atraso_pct",
        "atraso_medio_dias",
        "lead_time_medio_dias",
        "nota_media_mensal",
        "taxa_reviews_negativas_pct",
        "clientes_unicos",
        "novos_clientes",
        "clientes_com_recompra",
        "taxa_clientes_com_recompra_pct",
        "percentual_receita_sellers_estrategicos",
        "percentual_pedidos_sellers_estrategicos",
    ]
    available_columns = [column for column in columns_order if column in output.columns]
    return output[available_columns].copy()


def build_regression_output(regression_df: pd.DataFrame) -> pd.DataFrame:
    output = regression_df.copy()
    output = output.rename(
        columns={
            "year_month": "ano_mes",
            "revenue_month": "receita_mes",
            "revenue_growth_m1_pct": "crescimento_receita_m1_pct",
            "revenue_growth_m1_pct_winsorized": "crescimento_receita_m1_pct_ajustado",
            "late_rate_pct": "percentual_pedidos_atrasados",
            "repurchase_customer_rate_pct": "percentual_clientes_com_recompra",
            "strategic_revenue_share_pct": "percentual_receita_sellers_estrategicos",
            "predicted_growth_m1_pct": "baseline_crescimento_m1_pct",
            "predicted_next_month_revenue": "baseline_receita_m1",
            "next_month_revenue": "receita_m1_observada",
            "next_month_label": "ano_mes_m1",
        }
    )
    return output[
        [
            "ano_mes",
            "receita_mes",
            "crescimento_receita_m1_pct",
            "crescimento_receita_m1_pct_ajustado",
            "percentual_pedidos_atrasados",
            "percentual_clientes_com_recompra",
            "percentual_receita_sellers_estrategicos",
            "baseline_crescimento_m1_pct",
            "baseline_receita_m1",
            "receita_m1_observada",
            "ano_mes_m1",
        ]
    ].copy()


def markdown_table(dataframe: pd.DataFrame, columns: List[str], max_rows: int = 10) -> str:
    if dataframe.empty:
        return "_Sem dados disponíveis._"

    subset = dataframe[columns].head(max_rows).copy()
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for _, row in subset.iterrows():
        values = [str(row[column]) for column in columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join([header, separator, *rows])


def build_docx_paragraph(text: str, kind: str = "body") -> str:
    escaped_text = xml_escape(text)
    if kind == "blank":
        return "<w:p/>"

    if kind == "title":
        run_properties = "<w:rPr><w:b/><w:sz w:val=\"32\"/></w:rPr>"
    elif kind == "heading1":
        run_properties = "<w:rPr><w:b/><w:sz w:val=\"28\"/></w:rPr>"
    elif kind == "heading2":
        run_properties = "<w:rPr><w:b/><w:sz w:val=\"24\"/></w:rPr>"
    elif kind == "heading3":
        run_properties = "<w:rPr><w:b/><w:sz w:val=\"22\"/></w:rPr>"
    elif kind == "bullet":
        escaped_text = xml_escape(f"- {text}")
        run_properties = "<w:rPr><w:sz w:val=\"22\"/></w:rPr>"
    else:
        run_properties = "<w:rPr><w:sz w:val=\"22\"/></w:rPr>"

    return (
        "<w:p>"
        "<w:pPr><w:spacing w:after=\"140\"/></w:pPr>"
        f"<w:r>{run_properties}<w:t xml:space=\"preserve\">{escaped_text}</w:t></w:r>"
        "</w:p>"
    )


def markdown_to_docx_paragraphs(markdown_text: str) -> List[str]:
    paragraphs: List[str] = []
    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped:
            paragraphs.append(build_docx_paragraph("", "blank"))
            continue
        if stripped.startswith("![") and "](" in stripped:
            image_label = stripped[2:].split("](", 1)[0]
            paragraphs.append(build_docx_paragraph(f"Grafico referenciado: {image_label}", "body"))
            continue
        if stripped.startswith("| ---"):
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            cleaned = " | ".join(part.strip() for part in stripped.strip("|").split("|"))
            paragraphs.append(build_docx_paragraph(cleaned, "body"))
            continue
        if stripped.startswith("# "):
            paragraphs.append(build_docx_paragraph(stripped[2:], "title"))
            continue
        if stripped.startswith("## "):
            paragraphs.append(build_docx_paragraph(stripped[3:], "heading1"))
            continue
        if stripped.startswith("### "):
            paragraphs.append(build_docx_paragraph(stripped[4:], "heading2"))
            continue
        if stripped.startswith("#### "):
            paragraphs.append(build_docx_paragraph(stripped[5:], "heading3"))
            continue
        if stripped.startswith("- "):
            paragraphs.append(build_docx_paragraph(stripped[2:], "bullet"))
            continue
        paragraphs.append(build_docx_paragraph(stripped, "body"))
    return paragraphs


def create_simple_docx_from_markdown(markdown_text: str, output_path: Path) -> None:
    paragraphs = markdown_to_docx_paragraphs(markdown_text)
    document_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\">"
        "<w:body>"
        + "".join(paragraphs)
        + (
            "<w:sectPr>"
            "<w:pgSz w:w=\"11906\" w:h=\"16838\"/>"
            "<w:pgMar w:top=\"1440\" w:right=\"1440\" w:bottom=\"1440\" w:left=\"1440\" "
            "w:header=\"708\" w:footer=\"708\" w:gutter=\"0\"/>"
            "</w:sectPr>"
        )
        + "</w:body></w:document>"
    )

    content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""

    rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""

    core_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Relatorio Executivo Tech Challenge Olist Data</dc:title>
  <dc:creator>OpenAI Codex</dc:creator>
  <cp:lastModifiedBy>OpenAI Codex</cp:lastModifiedBy>
</cp:coreProperties>"""

    app_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>OpenAI Codex</Application>
</Properties>"""

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as docx_file:
        docx_file.writestr("[Content_Types].xml", content_types_xml)
        docx_file.writestr("_rels/.rels", rels_xml)
        docx_file.writestr("docProps/core.xml", core_xml)
        docx_file.writestr("docProps/app.xml", app_xml)
        docx_file.writestr("word/document.xml", document_xml)

    info(f"Relatorio Word salvo em: {output_path}")


def generate_markdown_report(
    data_dir: Path,
    load_metadata: Dict[str, Dict[str, Any]],
    growth_results: Dict[str, Any],
    logistics_results: Dict[str, Any],
    seller_results: Dict[str, Any],
    repurchase_results: Dict[str, Any],
    strategic_results: Dict[str, Any],
    prepared: Dict[str, Any],
    output_dirs: Dict[str, Path],
) -> Path:
    report_path = output_dirs["report"] / "analise_estatistica_olist.md"
    seller_top = seller_results.get("eligible", pd.DataFrame()).copy()
    if not seller_top.empty:
        seller_top = seller_top.head(10)[
            [
                "seller_id",
                "seller_orders",
                "late_rate",
                "avg_delay_days",
                "avg_review_score",
                "risk_score",
            ]
        ].copy()
        seller_top["late_rate"] = seller_top["late_rate"].map(lambda value: format_pct(value * 100))
        seller_top["avg_delay_days"] = seller_top["avg_delay_days"].map(format_br_number)
        seller_top["avg_review_score"] = seller_top["avg_review_score"].map(format_br_number)
        seller_top["risk_score"] = seller_top["risk_score"].map(format_br_number)

    city_concentration = growth_results["city_concentration"].copy()
    seller_concentration = growth_results["seller_concentration"].copy()
    category_concentration = growth_results["category_concentration"].copy()
    repurchase_categories = repurchase_results["repurchase_category_concentration"].head(10).copy()
    repurchase_categories["share"] = repurchase_categories["share"].map(lambda value: format_pct(value * 100))
    repurchase_categories["item_revenue"] = repurchase_categories["item_revenue"].map(format_currency)

    city_top10_share = city_concentration["share"].head(10).sum() * 100
    city_top1_share = city_concentration.iloc[0]["share"] * 100 if not city_concentration.empty else np.nan
    category_top10_share = category_concentration["share"].head(10).sum() * 100
    category_top5_share = category_concentration["share"].head(5).sum() * 100
    seller_top10_share = seller_concentration["share"].head(10).sum() * 100

    review_gap_points = logistics_results.get("review_gap_points", np.nan)
    review_gap_pct = logistics_results.get("review_gap_pct", np.nan)
    strategic_global_share = strategic_results.get("strategic_global_share", np.nan)

    load_summary_lines = [
        f"- `{table_key}`: {meta['path'].name} | linhas={meta['rows']} | separador=`{meta['delimiter']}` | encoding=`{meta['encoding']}`"
        for table_key, meta in load_metadata.items()
    ]

    manual_alerts: List[str] = []
    manual_alerts.append(
        "A regressao e a simulacao de cenario foram retiradas deste material Python e devem ser apresentadas apenas na versao validada em Excel."
    )
    manual_alerts.append(
        "O grafico de taxa de atraso mensal nao deve entrar na apresentacao principal antes de reconciliar a definicao com o dashboard do Power BI."
    )
    manual_alerts.append(
        "Graficos de controle ficam restritos ao apendice tecnico, porque a serie tem tendencia e nao representa processo estavel classico."
    )
    if growth_results["monthly"]["taxa_atraso_pct" if "taxa_atraso_pct" in growth_results["monthly"].columns else "late_rate"].max() is not None:
        manual_alerts.append(
            "Ha pico mensal de atraso acima do patamar medio em parte da serie. Esse comportamento deve ser validado antes de ser usado como headline."
        )

    warnings_text = "\n".join(f"- {message}" for message in [*manual_alerts, *RUNTIME_WARNINGS]) or "- Nenhum alerta adicional."

    report_content = f"""# Analise Estatistica Olist - Versao Revisada para Storytelling Executivo

## Objetivo desta revisao

Este documento reorganiza a saida estatistica do Python para fortalecer a apresentacao executiva sem forcar conclusoes que os dados nao sustentam. O foco ficou em:

- manter apenas evidencias coerentes e defensaveis na narrativa principal;
- mover leituras sensiveis para apendice tecnico;
- retirar regressao e simulacao do escopo do Python;
- preservar a tese central com linguagem segura: associacao, leitura observada e priorizacao.

## Curadoria executiva do material

### Graficos mantidos na apresentacao principal

- `pareto_receita_cidade.png`: sustenta que o crescimento existe, mas esta concentrado em poucos polos geograficos.
- `pareto_receita_categoria.png`: mostra que o valor tambem se concentra em algumas categorias lideres.
- `boxplot_review_por_atraso.png`: evidencia central de que atraso piora a percepcao de valor.
- `top_10_sellers_detratores.png`: mostra que o problema logistico pode ser priorizado em sellers especificos.
- `novos_vs_recompra_mes.png`: sustenta que a aquisicao e muito maior do que a base com recompra.

### Graficos movidos para apendice tecnico

- `receita_mensal.png`: ajuda a mostrar tracao, mas nao precisa ser a prova central.
- `pedidos_mensais.png`: util como suporte de crescimento, sem ser headline.
- `pareto_receita_seller.png`: complementar para mostrar concentracao por seller.
- `categorias_recompra.png`: bom apoio para retencao seletiva, melhor no relatorio do que no slide principal.
- `dispersao_volume_vs_taxa_atraso_seller.png`: analitico e util para apendice.
- `controle_receita_mensal.png`, `controle_pedidos_mensais.png`, `controle_nota_media.png`: leitura exploratoria apenas.

### Graficos removidos da apresentacao principal

- `coeficientes_regressao.png`: removido porque pode contradizer a tese e depende de amostra mensal curta.
- `correlacao_drivers.png`: removido porque correlacao simples nao sustenta decisao executiva isoladamente.
- `comparacao_baseline_vs_cenario_m1.png`: removido porque a simulacao passou a ficar fora do Python.
- `receita_historica_vs_baseline.png`: removido pelo mesmo motivo da simulacao.
- `ticket_medio_grupo_recompra.png`: removido porque enfraquece a narrativa se lido como prova de maior valor.
- `taxa_atraso_mensal.png` e `controle_taxa_atraso.png`: removidos da narrativa principal ate reconciliar integralmente a formula com o dashboard.

## Narrativa estatistica revisada

### 1. Crescimento existe, mas e concentrado

- Top 10 cidades concentram **{format_pct(city_top10_share)}** da receita.
- Sao Paulo sozinha concentra **{format_pct(city_top1_share)}**.
- Top 5 categorias concentram **{format_pct(category_top5_share)}** e top 10 categorias **{format_pct(category_top10_share)}**.
- Top 10 sellers concentram **{format_pct(seller_top10_share)}** da receita.

Texto executivo sugerido:
> Os dados sugerem que a Olist ganhou escala comercial, mas com dependencia relevante de poucos polos geograficos, categorias lideres e um grupo restrito de sellers. Isso reforca tracao, mas tambem indica concentracao de risco e de oportunidade.

![Pareto de receita por cidade](../charts/pareto_receita_cidade.png)

![Pareto de receita por categoria](../charts/pareto_receita_categoria.png)

### 2. Atraso destroi valor percebido

- Nota media no prazo: **{format_br_number(logistics_results.get('on_time_mean_review'))}**
- Nota media com atraso: **{format_br_number(logistics_results.get('delayed_mean_review'))}**
- Gap absoluto: **{format_br_number(review_gap_points)} pontos**
- Variacao relativa: **{format_pct(review_gap_pct)}**
- Teste de Mann-Whitney: **p={format_pvalue(logistics_results.get('group_tests', {}).get('mannwhitney_pvalue'))}**
- Spearman atraso vs nota: **rho={format_br_number(logistics_results.get('spearman', {}).get('rho'))} | p={format_pvalue(logistics_results.get('spearman', {}).get('pvalue'))}**

Texto executivo sugerido:
> Ha evidencia estatistica de associacao entre atraso logistico e pior satisfacao. O comportamento observado aponta que logistica deve ser tratada como tema de experiencia e reputacao, e nao apenas de eficiencia operacional.

![Boxplot de review_score por atraso](../charts/boxplot_review_por_atraso.png)

### 3. O problema logistico e priorizavel

- O score de risco foi definido como `volume_pedidos * taxa_atraso * impacto_na_nota`.
- O ranking prioriza sellers com volume suficiente para acao pratica.
- A leitura correta e de priorizacao operacional, nao de causalidade individual.

Texto executivo sugerido:
> O problema logistico nao e homogeneo. A analise indica que parte relevante do risco esta concentrada em sellers especificos, o que permite plano direcionado em vez de acao generica sobre toda a base.

{markdown_table(seller_top, ["seller_id", "seller_orders", "late_rate", "avg_delay_days", "avg_review_score", "risk_score"]) if not seller_top.empty else "_Sem sellers elegiveis para ranking._"}

![Top 10 sellers detratores](../charts/top_10_sellers_detratores.png)

### 4. Recompra e oportunidade, nao prova isolada de valor

- Clientes unicos: **{format_br_int(repurchase_results.get('total_customers'))}**
- Frequencia media: **{format_br_number(repurchase_results.get('avg_orders_per_customer'))} compras por cliente**
- Clientes com recompra: **{format_pct(repurchase_results.get('pct_customers_with_repurchase'))}**
- Receita da base com recompra: **{format_currency(repurchase_results.get('revenue_repurchase_customers'))}**

Texto executivo sugerido:
> A recompra ainda e pequena frente ao volume de aquisicao. Isso nao invalida a agenda de retencao; ao contrario, sugere que existe espaco para expansao seletiva nas categorias que ja mostram tracao dentro da base recorrente.

![Novos clientes vs clientes com recompra](../charts/novos_vs_recompra_mes.png)

Categorias mais relevantes dentro da base com recompra:

{markdown_table(repurchase_categories, ["product_category_final", "item_revenue", "share"])}

### 5. Sellers estrategicos e cenario futuro

- O Python manteve apenas a identificacao operacional de sellers estrategicos por score composto de receita, pedidos e itens.
- O grupo estrategico definido no recorte responde por **{format_pct(strategic_global_share * 100) if not pd.isna(strategic_global_share) else 'n/d'}** da receita consolidada do grupo.
- A simulacao e a regressao ficaram fora deste material e devem ser tratadas na versao validada em Excel.

Texto executivo sugerido:
> A leitura mais defensavel e usar sellers estrategicos como frente de expansao seletiva, apoiada por retencao e disciplina operacional. O cenario numerico deve ser apresentado separadamente, como hipotese validada fora deste relatorio Python.

## Recomendacao de uso em apresentacao

### Entram na apresentacao principal

- Pareto por cidade
- Pareto por categoria
- Boxplot de review por atraso
- Top 10 sellers detratores
- Novos clientes vs clientes com recompra

### Ficam no apendice tecnico

- Dispersao volume vs taxa de atraso por seller
- Serie de receita e pedidos
- Graficos de controle
- Categorias da base com recompra
- Pareto de receita por seller

## Alertas de consistencia antes da defesa

- Validar a taxa de atraso do Python contra a definicao usada no Power BI: pedidos atrasados / pedidos entregues com datas validas.
- Nao usar ticket medio por grupo de recompra como headline.
- Nao usar regressao, correlacao simples ou simulacao do Python para sustentar causalidade.
- Revisar slides antigos com numeros hardcoded para evitar divergencia com a base tratada.

## Fontes e filtros aplicados

Os CSVs foram lidos automaticamente a partir de `{data_dir}`. Arquivos carregados:

{chr(10).join(load_summary_lines)}

Filtros e regras principais:

- Recorte principal alinhado ao dashboard: pedidos entregues de `{ANALYSIS_START_DATE.date()}` a `{ANALYSIS_END_DATE.date()}`.
- Pedidos sem `order_purchase_timestamp` foram descartados.
- A camada comercial considera apenas pedidos `delivered` com `order_delivered_customer_date` válido.
- Meses residuais removidos nas bordas da serie: `{prepared['complete_month_bounds']['dropped']}`.
- Analise de atraso considera apenas pedidos entregues com datas validas.
- Quando havia mais de um review por pedido, a nota foi agregada pela media.

## Limitacoes

- A base e observacional e nao sustenta causalidade.
- Parte das leituras mensais pode ser sensivel a meses especificos e a amostra curta.
- Nem todo pedido recebeu review, o que pode introduzir vies de selecao.
- O score de seller detrator e uma ferramenta de priorizacao, nao diagnostico causal definitivo.

## Alertas tecnicos consolidados

{warnings_text}
"""

    report_path.write_text(report_content, encoding="utf-8")
    info(f"Relatório salvo em: {report_path}")
    create_simple_docx_from_markdown(report_content, output_dirs["report"] / "relatorio_executivo_olist.docx")
    create_simple_docx_from_markdown(report_content, EXECUTIVE_REPORT_DOCX)

    return report_path


def print_executive_summary(
    growth_results: Dict[str, Any],
    logistics_results: Dict[str, Any],
    seller_results: Dict[str, Any],
    repurchase_results: Dict[str, Any],
    strategic_results: Dict[str, Any],
) -> None:
    city_top10_share = growth_results["city_concentration"]["share"].head(10).sum() * 100
    seller_top10_share = growth_results["seller_concentration"]["share"].head(10).sum() * 100
    category_top10_share = growth_results["category_concentration"]["share"].head(10).sum() * 100

    top_seller_id = "n/d"
    top_seller_score = np.nan
    if seller_results.get("eligible") is not None and not seller_results["eligible"].empty:
        top_seller_id = seller_results["eligible"].iloc[0]["seller_id"]
        top_seller_score = seller_results["eligible"].iloc[0]["risk_score"]

    print("\nResumo Executivo:")
    print(
        "1. Crescimento: "
        f"as 10 maiores cidades concentram {format_pct(city_top10_share)}, "
        f"os 10 maiores sellers concentram {format_pct(seller_top10_share)} "
        f"e as 10 maiores categorias concentram {format_pct(category_top10_share)} da receita."
    )
    print(
        "2. Logística: "
        f"pedidos no prazo tiveram nota média de {format_br_number(logistics_results.get('on_time_mean_review'))}, "
        f"contra {format_br_number(logistics_results.get('delayed_mean_review'))} para atrasados; "
        f"p(Mann-Whitney)={format_pvalue(logistics_results.get('group_tests', {}).get('mannwhitney_pvalue'))}."
    )
    print(
        "3. Sellers: "
        f"o seller mais crítico no ranking detrator foi {top_seller_id}, com score de risco "
        f"{format_br_number(top_seller_score)}."
    )
    print(
        "4. Recompra: "
        f"{format_pct(repurchase_results.get('pct_customers_with_repurchase'))} dos clientes fizeram recompra, "
        f"com frequência média de {format_br_number(repurchase_results.get('avg_orders_per_customer'))} compras por cliente."
    )
    print(
        "5. Cenário: "
        "a simulação quantitativa foi retirada do Python e deve ser apresentada apenas na versão validada em Excel."
    )


def main() -> None:
    output_dirs = ensure_output_dirs()
    remove_obsolete_generated_files()
    data_dir = detect_data_dir()
    datasets, load_metadata = load_datasets(data_dir)
    prepared = prepare_datasets(datasets)

    growth_results = analyze_growth_and_concentration(prepared, output_dirs)
    logistics_results = analyze_logistics_and_satisfaction(prepared, output_dirs)
    seller_results = analyze_seller_risk(prepared, logistics_results, output_dirs)
    repurchase_results = analyze_repurchase(prepared, output_dirs)
    strategic_results = analyze_strategic_sellers_and_regression(prepared, output_dirs)

    monthly_business_output = build_monthly_business_output(strategic_results["monthly_enriched"])
    save_dataframe(monthly_business_output, output_dirs["tables"] / "monthly_business_metrics.csv")

    generate_candlestick(
        prepared["daily_revenue"],
        output_dirs["charts"],
        prepared["complete_month_bounds"],
    )
    generate_markdown_report(
        data_dir,
        load_metadata,
        growth_results,
        logistics_results,
        seller_results,
        repurchase_results,
        strategic_results,
        prepared,
        output_dirs,
    )
    print_executive_summary(
        growth_results,
        logistics_results,
        seller_results,
        repurchase_results,
        strategic_results,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[ERRO] A análise falhou: {exc}")
        raise
