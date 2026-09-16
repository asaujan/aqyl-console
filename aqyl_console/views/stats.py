"""Сводный дашборд по dl_device_sync: динамика, регионы, платформы, ошибки Billing."""
import datetime as dt
import pandas as pd
import streamlit as st

from aqyl_console.core import db, config, status_meaning
from aqyl_console.core.i18n import t

st.title(f"📊 {t('page4_title')}")
st.caption(t("page4_caption"))

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
            t("filter_region"),
            [t("all_option")] + [f"{k}: {v}" for k, v in config.REGIONS.items()],
        )
    with c2:
        default_from = dt.date.today() - dt.timedelta(days=14)
        date_from = st.date_input(t("filter_date_from"), value=default_from)
    with c3:
        date_to = st.date_input(t("filter_date_to"), value=dt.date.today())
    platform = st.multiselect(
        t("filter_platform"), ["BILING-INSTALL", "BILING-REMOVE", "EQURAL", "KAZGAS_IOT"]
    )
    submitted = st.form_submit_button(t("btn_build"), type="primary")

if not submitted:
    st.info(t("stats_hint"))
    st.stop()

# --- Общий WHERE для запросов ---
where = ["create_time >= :df", "create_time <= :dt"]
params: dict = {
    "df": str(date_from),
    "dt": str(date_to) + " 23:59:59",
}
if region != t("all_option"):
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
    st.error(t("query_error", e=e))
    st.stop()

if daily.empty:
    st.warning(t("no_data_period"))
    st.stop()

# --- Сводные метрики ---
total_all = int(daily["total"].sum())
ok_all = int(daily["ok"].fillna(0).sum())
rate_all = (ok_all / total_all * 100) if total_all else 0.0

m1, m2, m3, m4 = st.columns(4)
m1.metric(t("metric_total_requests"), f"{total_all:,}".replace(",", " "))
m2.metric(t("metric_ok"), f"{ok_all:,}".replace(",", " "))
m3.metric(t("metric_rate"), f"{rate_all:.1f}%")
m4.metric(t("metric_billing_errors"), f"{len(billing_errors):,}".replace(",", " "))

st.divider()

# --- Динамика по дням ---
st.subheader(t("daily_header"))
rate_col = t("metric_rate")
requests_col = t("col_requests")
daily = daily.copy()
daily["day"] = pd.to_datetime(daily["day"])
daily["ok"] = daily["ok"].fillna(0).astype(int)
daily[rate_col] = (daily["ok"] / daily["total"] * 100).round(1)

col_a, col_b = st.columns(2)
with col_a:
    st.caption(t("requests_count_caption"))
    chart = daily.rename(columns={"total": requests_col}).set_index("day")[[requests_col]]
    st.bar_chart(chart)
with col_b:
    st.caption(t("success_rate_caption"))
    st.line_chart(daily.set_index("day")[[rate_col]])

st.divider()

# --- Разбивка по регионам и платформам ---
col_r, col_p = st.columns(2)

with col_r:
    st.subheader(t("by_region_header"))
    if by_region.empty:
        st.caption(t("no_data"))
    else:
        region_col = t("col_region")
        pct_col = t("col_success_pct")
        by_region = by_region.copy()
        by_region["ok"] = by_region["ok"].fillna(0).astype(int)
        by_region[region_col] = by_region["region_code"].map(
            lambda c: f"{c}: {config.REGIONS.get(int(c), '?')}" if pd.notna(c) else t("no_region_code")
        )
        by_region[pct_col] = (by_region["ok"] / by_region["total"] * 100).round(1)
        st.bar_chart(by_region.set_index(region_col)[["total"]].rename(columns={"total": requests_col}))
        st.dataframe(
            by_region.rename(columns={"total": t("col_total"), "ok": t("col_ok")})[
                [region_col, t("col_total"), t("col_ok"), pct_col]
            ],
            use_container_width=True,
            hide_index=True,
        )

with col_p:
    st.subheader(t("by_platform_header"))
    if by_platform.empty:
        st.caption(t("no_data"))
    else:
        pct_col = t("col_success_pct")
        by_platform = by_platform.copy()
        by_platform["ok"] = by_platform["ok"].fillna(0).astype(int)
        by_platform["platform_type"] = by_platform["platform_type"].fillna(t("no_platform_type"))
        by_platform[pct_col] = (by_platform["ok"] / by_platform["total"] * 100).round(1)
        st.bar_chart(
            by_platform.set_index("platform_type")[["total"]].rename(columns={"total": requests_col})
        )
        st.dataframe(
            by_platform.rename(
                columns={"platform_type": t("filter_platform"), "total": t("col_total"), "ok": t("col_ok")}
            )[[t("filter_platform"), t("col_total"), t("col_ok"), pct_col]],
            use_container_width=True,
            hide_index=True,
        )

st.divider()

# --- Топ ошибок Billing по паттернам ---
st.subheader(t("top_errors_header"))
st.caption(t("top_errors_caption", platforms=", ".join(BILLING_PLATFORMS)))

if billing_errors.empty:
    st.success(t("no_billing_errors"))
else:
    category_col = t("col_category")
    count_col = t("col_count")
    share_col = t("col_share_pct")
    err = billing_errors.copy()
    err[category_col] = err["response_body"].map(classify)
    grouped = (
        err.groupby(category_col)
        .size()
        .reset_index(name=count_col)
        .sort_values(count_col, ascending=False)
    )
    total_err = int(grouped[count_col].sum())
    grouped[share_col] = (grouped[count_col] / total_err * 100).round(1)

    col_c, col_t2 = st.columns([1, 1])
    with col_c:
        st.bar_chart(grouped.set_index(category_col)[[count_col]])
    with col_t2:
        st.dataframe(grouped, use_container_width=True, hide_index=True)

    # Примеры сообщений по категориям (для уточнения паттернов)
    with st.expander(t("samples_expander")):
        for cat in grouped[category_col]:
            samples = (
                err.loc[err[category_col] == cat, "response_body"]
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
