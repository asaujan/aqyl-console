"""MySQL access layer for device_life DB."""
import warnings
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.sql.expression import bindparam
from urllib.parse import quote_plus

from aqyl_console.core import config


@st.cache_resource
def get_engine():
    pwd = quote_plus(config.DB_PASSWORD)
    url = (
        f"mysql+pymysql://{config.DB_USER}:{pwd}"
        f"@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}?charset=utf8mb4"
    )
    return create_engine(url, pool_pre_ping=True, pool_recycle=1800)


def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Run SQL. Tuple params are treated as expanding IN-lists automatically."""
    eng = get_engine()
    params = params or {}
    stmt = text(sql)
    for k, v in params.items():
        if isinstance(v, tuple):
            stmt = stmt.bindparams(bindparam(k, expanding=True))
    with eng.connect() as conn:
        return pd.read_sql(stmt, conn, params=params)


def test_connection() -> tuple[bool, str]:
    try:
        df = run_query("SELECT 1 AS ok")
        return (int(df.iloc[0]["ok"]) == 1, "OK")
    except Exception as e:
        return (False, f"{type(e).__name__}: {e}")


# --- e-Qural (PostgreSQL, база mds) ------------------------------------------

@st.cache_resource
def get_equral_engine():
    """Engine к БД e-Qural. ВАЖНО: база mds, не postgres (там пусто)."""
    pwd = quote_plus(config.EQURAL_DB_PASSWORD)
    url = (
        f"postgresql+psycopg2://{config.EQURAL_DB_USER}:{pwd}"
        f"@{config.EQURAL_DB_HOST}:{config.EQURAL_DB_PORT}/{config.EQURAL_DB_NAME}"
    )
    return create_engine(url, pool_pre_ping=True, pool_recycle=1800)


def run_equral_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Запрос к e-Qural через psycopg2.

    Плейсхолдеры psycopg2 в стиле %(name)s, поэтому SQL передаём как есть,
    а pandas прокидывает params прямо в драйвер. Питоновский список в params
    (например device_list) работает с конструкцией = ANY(%(device_list)s).
    """
    eng = get_equral_engine()
    params = params or {}
    with eng.connect() as conn:
        # Берём сырое DBAPI-соединение, чтобы psycopg2 сам разобрал %(name)s
        # и корректно передал питоновский список для = ANY(...).
        raw = conn.connection
        # pandas предупреждает про сырое DBAPI-соединение, но именно оно нужно,
        # чтобы psycopg2 разобрал %(name)s и передал список для = ANY(...).
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            return pd.read_sql(sql, raw, params=params)


def test_equral_connection() -> tuple[bool, str]:
    try:
        df = run_equral_query("SELECT 1 AS ok")
        return (int(df.iloc[0]["ok"]) == 1, "OK")
    except Exception as e:
        return (False, f"{type(e).__name__}: {e}")
