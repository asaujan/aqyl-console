"""Sync table viewer with filters and Excel export."""
import io
import pandas as pd
import streamlit as st

from aqyl_console.core import db, config, status_meaning
from aqyl_console.core.i18n import t, sync_columns

st.title(f"📋 {t('page1_title')}")

with st.form("filters"):
    c1, c2, c3 = st.columns(3)
    with c1:
        region = st.selectbox(
            t("filter_region"),
            [t("all_option")] + [f"{k}: {v}" for k, v in config.REGIONS.items()],
        )
        platform = st.multiselect(
            t("filter_platform"),
            ["BILING-INSTALL", "BILING-REMOVE", "EQURAL", "KAZGAS_IOT"],
        )
    with c2:
        status = st.multiselect(t("filter_http"), [200, 204, 400, 401, 500, 502])
        device_no = st.text_input(t("filter_device"))
    with c3:
        date_from = st.date_input(t("filter_date_from"), value=None)
        date_to = st.date_input(t("filter_date_to"), value=None)
    limit = st.slider(t("filter_limit"), 100, 10000, 1000, step=100)
    submitted = st.form_submit_button(t("btn_show"), type="primary")

if submitted:
    where = []
    params = {}
    if region != t("all_option"):
        params["region"] = int(region.split(":")[0])
        where.append("region_code = :region")
    if platform:
        where.append("platform_type IN :platforms")
        params["platforms"] = tuple(platform)
    if status:
        where.append("response_status IN :statuses")
        params["statuses"] = tuple(status)
    if device_no.strip():
        params["dev"] = device_no.strip()
        where.append("device_no = :dev")
    if date_from:
        params["df"] = str(date_from)
        where.append("create_time >= :df")
    if date_to:
        params["dt"] = str(date_to) + " 23:59:59"
        where.append("create_time <= :dt")

    sql = "SELECT * FROM dl_device_sync"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += f" ORDER BY id DESC LIMIT {int(limit)}"

    # SQLAlchemy needs expanding IN, use text with tuple via pandas fallback
    try:
        df = db.run_query(sql, params)
    except Exception as e:
        st.error(t("query_error", e=e))
        st.stop()

    st.caption(t("rows_found", n=len(df)))

    # Смысл HTTP-кода (с учётом платформы) и категория ошибки Billing.
    if "response_status" in df.columns and "platform_type" in df.columns:
        meaning_col = t("col_status_meaning")
        category_col = t("col_error_category")
        df = df.copy()
        df[meaning_col] = [
            status_meaning.http_meaning(p, c)
            for p, c in zip(df["platform_type"], df["response_status"])
        ]
        BILLING = ("BILING-INSTALL", "BILING-REMOVE")
        body_col = "response_body" if "response_body" in df.columns else None

        def _cat(row):
            # Категория только для неуспешных ответов Billing.
            if row["platform_type"] not in BILLING:
                return ""
            if status_meaning.is_success(row["platform_type"], row["response_status"]):
                return ""
            text = row[body_col] if body_col else None
            return status_meaning.classify_billing_error(text)[0]

        df[category_col] = df.apply(_cat, axis=1)

        # Поставим смысл статуса сразу за HTTP-колонкой.
        cols = list(df.columns)
        cols.remove(meaning_col)
        cols.remove(category_col)
        pos = cols.index("response_status") + 1
        cols[pos:pos] = [meaning_col, category_col]
        df = df[cols]

    show = df.rename(columns=sync_columns())
    st.dataframe(show, use_container_width=True, height=500)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        show.to_excel(w, index=False, sheet_name="sync")
    st.download_button(
        t("export_excel"),
        buf.getvalue(),
        file_name="sync_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
