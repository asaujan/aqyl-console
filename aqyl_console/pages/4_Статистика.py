"""Сводный дашборд по dl_device_sync: динамика, регионы, платформы, ошибки Billing."""
import datetime as dt
import pandas as pd
import streamlit as st

from aqyl_console.core import db, config, session, status_meaning

st.set_page_config(page_title="Статистика", page_icon="📊", layout="wide")
st.title("📊 Статистика синхронизации")
st.caption("Сводка по таблице dl_device_sync: запросы, успех (Billing 200, e-Qural 204), регионы, платформы, ошибки Billing.")

session.render_cookie_sidebar()

# Типы платформ Billing (для раздела с ошибками)
BILLING_PLATFORMS = ("BILING-INSTALL", "BILING-REMOVE")

# Успех с учётом платформы: у EQURAL это 204, у остальных 200.
# Считаем прямо в SQL, чтобы агрегаты были корректны.
OK_SQL = (
    "SUM(CASE WHEN (platform_type = 'EQURAL' AND response_status = 204) "
    "OR (platform_type <> 'EQURAL' AND response_status = 200) THEN 1 ELSE 0 END)"
)


def classify(msg) -> str:
    """Категория ошибки Billing по тексту ответа (из core.status_meaning)."""
    return status_meaning.classify_billing_error(msg)[0]


# --- Фильтры ---
with st.form("stats_filters"):
    c1, c2, c3 = st.columns(3)
    with c1:
        region = st.selectbox(
            "Регион", ["Все"] + [f"{k}: {v}" for k, v in config.REGIONS.items()]
        )
    with c2:
        default_from = dt.date.today() - dt.timedelta(days=14)
        date_from = st.date_input("Дата с", value=default_from)
    with c3:
        date_to = st.date_input("Дата по", value=dt.date.today())
    platform = st.multiselect(
        "Тип платформы", ["BILING-INSTALL", "BILING-REMOVE", "EQURAL", "KAZGAS_IOT"]
    )
    submitted = st.form_submit_button("Построить", type="primary")

if not submitted:
    st.info("Задай период и нажми «Построить».")
    st.stop()

# --- Общий WHERE для запросов ---
where = ["create_time >= :df", "create_time <= :dt"]
params: dict = {
    "df": str(date_from),
    "dt": str(date_to) + " 23:59:59",
}
if region != "Все":
    params["region"] = int(region.split(":")[0])
    where.append("region_code = :region")
if platform:
    params["platforms"] = tuple(platform)
    where.append("platform_type IN :platforms")
where_sql = " AND ".join(where)

# --- Загрузка агрегатов ---
try:
    daily = db.run_query(
        f"""
        SELECT DATE(create_time) AS day,
               COUNT(*) AS total,
               {OK_SQL} AS ok
        FROM dl_device_sync
        WHERE {where_sql}
        GROUP BY DATE(create_time)
        ORDER BY day
        """,
        params,
    )
    by_region = db.run_query(
        f"""
        SELECT region_code,
               COUNT(*) AS total,
               {OK_SQL} AS ok
        FROM dl_device_sync
        WHERE {where_sql}
        GROUP BY region_code
        ORDER BY total DESC
        """,
        params,
    )
    by_platform = db.run_query(
        f"""
        SELECT platform_type,
               COUNT(*) AS total,
               {OK_SQL} AS ok
        FROM dl_device_sync
        WHERE {where_sql}
        GROUP BY platform_type
        ORDER BY total DESC
        """,
        params,
    )
    # Ошибки Billing (не 200), для группировки по паттернам в pandas
    err_params = dict(params)
    err_params["billing"] = BILLING_PLATFORMS
    billing_errors = db.run_query(
        f"""
        SELECT response_body
        FROM dl_device_sync
        WHERE {where_sql}
          AND platform_type IN :billing
          AND (response_status <> 200 OR response_status IS NULL)
        """,
        err_params,
    )
except Exception as e:
    st.error(f"Ошибка запроса: {e}")
    st.stop()

if daily.empty:
    st.warning("За выбранный период данных нет.")
    st.stop()

# --- Сводные метрики ---
total_all = int(daily["total"].sum())
ok_all = int(daily["ok"].fillna(0).sum())
rate_all = (ok_all / total_all * 100) if total_all else 0.0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Всего запросов", f"{total_all:,}".replace(",", " "))
m2.metric("Успешных", f"{ok_all:,}".replace(",", " "))
m3.metric("Процент успеха", f"{rate_all:.1f}%")
m4.metric("Ошибок Billing", f"{len(billing_errors):,}".replace(",", " "))

st.divider()

# --- Динамика по дням ---
st.subheader("Динамика по дням")
daily = daily.copy()
daily["day"] = pd.to_datetime(daily["day"])
daily["ok"] = daily["ok"].fillna(0).astype(int)
daily["Процент успеха"] = (daily["ok"] / daily["total"] * 100).round(1)

col_a, col_b = st.columns(2)
with col_a:
    st.caption("Количество запросов")
    chart = daily.rename(columns={"total": "Запросы"}).set_index("day")[["Запросы"]]
    st.bar_chart(chart)
with col_b:
    st.caption("Процент успеха (Billing 200, e-Qural 204), %")
    st.line_chart(daily.set_index("day")[["Процент успеха"]])

st.divider()

# --- Разбивка по регионам и платформам ---
col_r, col_p = st.columns(2)

with col_r:
    st.subheader("По регионам")
    if by_region.empty:
        st.caption("Нет данных.")
    else:
        by_region = by_region.copy()
        by_region["ok"] = by_region["ok"].fillna(0).astype(int)
        by_region["Регион"] = by_region["region_code"].map(
            lambda c: f"{c}: {config.REGIONS.get(int(c), '?')}" if pd.notna(c) else "нет кода"
        )
        by_region["Успех, %"] = (by_region["ok"] / by_region["total"] * 100).round(1)
        st.bar_chart(by_region.set_index("Регион")[["total"]].rename(columns={"total": "Запросы"}))
        st.dataframe(
            by_region.rename(columns={"total": "Всего", "ok": "Успешных"})[
                ["Регион", "Всего", "Успешных", "Успех, %"]
            ],
            use_container_width=True,
            hide_index=True,
        )

with col_p:
    st.subheader("По типу платформы")
    if by_platform.empty:
        st.caption("Нет данных.")
    else:
        by_platform = by_platform.copy()
        by_platform["ok"] = by_platform["ok"].fillna(0).astype(int)
        by_platform["platform_type"] = by_platform["platform_type"].fillna("нет типа")
        by_platform["Успех, %"] = (by_platform["ok"] / by_platform["total"] * 100).round(1)
        st.bar_chart(
            by_platform.set_index("platform_type")[["total"]].rename(columns={"total": "Запросы"})
        )
        st.dataframe(
            by_platform.rename(
                columns={"platform_type": "Тип платформы", "total": "Всего", "ok": "Успешных"}
            )[["Тип платформы", "Всего", "Успешных", "Успех, %"]],
            use_container_width=True,
            hide_index=True,
        )

st.divider()

# --- Топ ошибок Billing по паттернам ---
st.subheader("Топ ошибок Billing по паттернам")
st.caption(
    "Ошибки (не 200) по платформам "
    + ", ".join(BILLING_PLATFORMS)
    + ", сгруппированные по тексту ответа."
)

if billing_errors.empty:
    st.success("Ошибок Billing за период нет.")
else:
    err = billing_errors.copy()
    err["Категория"] = err["response_body"].map(classify)
    grouped = (
        err.groupby("Категория")
        .size()
        .reset_index(name="Количество")
        .sort_values("Количество", ascending=False)
    )
    total_err = int(grouped["Количество"].sum())
    grouped["Доля, %"] = (grouped["Количество"] / total_err * 100).round(1)

    col_c, col_t = st.columns([1, 1])
    with col_c:
        st.bar_chart(grouped.set_index("Категория")[["Количество"]])
    with col_t:
        st.dataframe(grouped, use_container_width=True, hide_index=True)

    # Примеры сообщений по категориям (для уточнения паттернов)
    with st.expander("Примеры сообщений по категориям"):
        for cat in grouped["Категория"]:
            samples = (
                err.loc[err["Категория"] == cat, "response_body"]
                .dropna()
                .astype(str)
                .str.strip()
                .value_counts()
                .head(5)
            )
            st.markdown(f"**{cat}**")
            for msg, cnt in samples.items():
                short = msg if len(msg) <= 200 else msg[:200] + "…"
                st.text(f"  ({cnt}) {short}")
