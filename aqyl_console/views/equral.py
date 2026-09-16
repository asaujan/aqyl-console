"""Проверка установки счётчика в e-Qural (БД mds).

Три режима: одиночная, по выбору из dl_device_sync, из файла. Вердикт строится
на данных mds (не на response_status, который для EQURAL ненадёжен).
Вердикты приходят из core.equral русскими константами и переводятся
на текущий язык только при показе (внутренние ключи не меняются).
"""
import io
import pandas as pd
import streamlit as st

from aqyl_console.core import db, equral, config
from aqyl_console.core.i18n import t

st.title(f"✅ {t('page5_title')}")
st.caption(t("page5_caption"))

# Ключ перевода для каждого вердикта из core.equral.
VERDICT_KEYS = {
    equral.V_INSTALLED: "verdict_installed",
    equral.V_AWAITING: "verdict_awaiting",
    equral.V_NO_CONSUMER: "verdict_no_consumer",
    equral.V_DELETED: "verdict_deleted",
    equral.V_BLOCKED: "verdict_blocked",
    equral.V_ABSENT: "verdict_absent",
}

# Цвета фона для колонки вердикта.
_BG = {"green": "#1b5e20", "yellow": "#8d6e00", "red": "#7f1d1d"}


def _verdict_display(verdict: str) -> str:
    """Вердикт на текущем языке (неизвестное значение остаётся как есть)."""
    key = VERDICT_KEYS.get(verdict)
    return t(key) if key else verdict


def _result_columns() -> dict:
    """Человекочитаемые заголовки результата на текущем языке."""
    return {
        "device_no": t("col_device_no_full"),
        "status_name": t("col_status_mds"),
        "really_installed": t("col_really_installed"),
        "personal_account": t("col_ls"),
        "region_kato": t("col_region_kato"),
        "region_name": t("col_region"),
        "is_blocked_flag": t("col_block_flag"),
        "date_create": t("col_created"),
        "date_update": t("col_updated"),
        "Вердикт e-Qural": t("col_equral_verdict"),
    }


RESULT_ORDER = [
    "device_no", "Вердикт e-Qural", "status_name", "really_installed",
    "personal_account", "region_kato", "region_name", "is_blocked_flag",
    "date_create", "date_update",
]


def _style_verdict(df: pd.DataFrame):
    """Styler: подсветить колонку вердикта по цвету вердикта.

    Работает по переведённым значениям, поэтому цвет ищем через
    отображаемый текст каждого вердикта.
    """
    verdict_col = t("col_equral_verdict")
    display_color = {
        _verdict_display(v): c for v, c in equral.VERDICT_COLOR.items()
    }

    def color(val):
        c = display_color.get(val)
        return f"background-color: {_BG[c]}; color: white" if c else ""
    return df.style.map(color, subset=[verdict_col]) \
        if verdict_col in df.columns else df.style


def _prep_view(res: pd.DataFrame) -> pd.DataFrame:
    """Готовит результат к показу: порядок, заголовки и вердикты на текущем языке."""
    cols = [c for c in RESULT_ORDER if c in res.columns]
    view = res.reindex(columns=cols).copy()
    if "Вердикт e-Qural" in view.columns:
        view["Вердикт e-Qural"] = view["Вердикт e-Qural"].map(_verdict_display)
    return view.rename(columns=_result_columns())


def _summary(res: pd.DataFrame) -> None:
    """Сводка внизу массовой проверки: установлено и не прошло по причинам."""
    counts = res["Вердикт e-Qural"].value_counts()
    installed = int(counts.get(equral.V_INSTALLED, 0))
    total = len(res)
    failed = total - installed
    st.divider()
    st.subheader(t("summary_header"))
    m1, m2, m3 = st.columns(3)
    m1.metric(t("metric_checked"), total)
    m2.metric(t("verdict_installed"), installed)
    m3.metric(t("metric_failed"), failed)
    # Разбивка по причинам (всё, кроме успешной установки).
    reasons = counts.drop(labels=[equral.V_INSTALLED], errors="ignore")
    if not reasons.empty:
        st.markdown(t("breakdown_md"))
        breakdown = reasons.reset_index()
        breakdown.columns = [t("col_reason"), t("col_count")]
        breakdown[t("col_reason")] = breakdown[t("col_reason")].map(_verdict_display)
        st.dataframe(breakdown, use_container_width=True, hide_index=True)


def _show_result_table(res: pd.DataFrame, filename: str) -> None:
    """Общий блок: таблица с подсветкой вердикта, сводка, экспорт в Excel."""
    if res.empty:
        st.warning(t("no_data_show"))
        return
    view = _prep_view(res)
    st.dataframe(_style_verdict(view), use_container_width=True, height=460)
    _summary(res)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        view.to_excel(w, index=False, sheet_name="equral")
    st.download_button(
        t("export_excel"),
        buf.getvalue(),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


MODE_SINGLE = t("mode_single_f")
MODE_TABLE = t("mode_table")
MODE_FILE = t("mode_file")

mode = st.radio(
    t("mode_check_label"),
    [MODE_SINGLE, MODE_TABLE, MODE_FILE],
    horizontal=True,
)
st.divider()

# --- Режим 1: одиночная проверка ---------------------------------------------
if mode == MODE_SINGLE:
    st.subheader(t("single_check_header"))
    device_no = st.text_input(t("filter_device"), placeholder=t("device_placeholder"))
    if st.button(t("btn_check_equral"), type="primary", disabled=not device_no.strip()):
        try:
            res = equral.check_devices([device_no])
        except Exception as e:
            st.error(t("equral_query_error", e=e))
            st.stop()
        if res.empty:
            st.warning(t("empty_input"))
            st.stop()
        row = res.iloc[0]
        verdict = row["Вердикт e-Qural"]
        color = equral.VERDICT_COLOR.get(verdict, "red")
        verdict_msg = t("verdict_is", v=_verdict_display(verdict))
        if color == "green":
            st.success(verdict_msg)
        elif color == "yellow":
            st.warning(verdict_msg)
        else:
            st.error(verdict_msg)

        c1, c2, c3 = st.columns(3)
        c1.metric(t("col_status_mds"), row["status_name"] if pd.notna(row["status_name"]) else t("not_in_mds"))
        c2.metric(t("col_really_installed"), t("val_yes") if row["really_installed"] else t("val_no"))
        c3.metric(t("col_block_flag"), t("val_yes") if row["is_blocked_flag"] else t("val_no"))

        st.markdown(
            f"- **{t('label_consumer_link')}:** {t('val_present') if row['has_consumer'] else t('val_none')}\n"
            f"- **{t('label_account')}:** {row['personal_account'] or t('val_none')}\n"
            f"- **{t('label_region')}:** {row['region_name'] or t('val_none')} "
            f"({row['region_kato'] if pd.notna(row['region_kato']) else t('no_kato')})\n"
            f"- **{t('label_created')}:** {row['date_create'] or t('val_none')}\n"
            f"- **{t('label_updated')}:** {row['date_update'] or t('val_none')}"
        )

# --- Режим 2: выбор из dl_device_sync ----------------------------------------
elif mode == MODE_TABLE:
    st.subheader(t("table_check_header"))
    st.caption(t("table_check_caption"))
    with st.form("equral_filters"):
        c1, c2, c3 = st.columns(3)
        with c1:
            region = st.selectbox(
                t("filter_region"),
                [t("all_option")] + [f"{k}: {v}" for k, v in config.REGIONS.items()],
            )
            platform = st.multiselect(
                t("filter_platform"),
                ["EQURAL", "BILING-INSTALL", "BILING-REMOVE", "KAZGAS_IOT"],
                default=["EQURAL"],
            )
        with c2:
            status = st.multiselect(t("filter_http"), [200, 204, 400, 401, 500, 502])
            device_no = st.text_input(t("filter_device"))
        with c3:
            date_from = st.date_input(t("filter_date_from"), value=None)
            date_to = st.date_input(t("filter_date_to"), value=None)
        limit = st.slider(t("filter_limit"), 50, 5000, 500, step=50)
        submitted = st.form_submit_button(t("btn_show_records"), type="primary")

    if submitted:
        where = []
        params = {}
        if region != t("all_option"):
            params["region"] = int(region.split(":")[0])
            where.append("region_code = :region")
        if platform:
            params["platforms"] = tuple(platform)
            where.append("platform_type IN :platforms")
        if status:
            params["statuses"] = tuple(status)
            where.append("response_status IN :statuses")
        if device_no.strip():
            params["dev"] = device_no.strip()
            where.append("device_no = :dev")
        if date_from:
            params["df"] = str(date_from)
            where.append("create_time >= :df")
        if date_to:
            params["dt"] = str(date_to) + " 23:59:59"
            where.append("create_time <= :dt")

        sql = ("SELECT id, device_no, platform_type, response_status, create_time "
               "FROM dl_device_sync")
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += f" ORDER BY id DESC LIMIT {int(limit)}"
        try:
            found = db.run_query(sql, params)
        except Exception as e:
            st.error(t("query_error", e=e))
            st.stop()
        st.caption(t("rows_found", n=len(found)))
        st.session_state["equral_table_found"] = found

    found = st.session_state.get("equral_table_found")
    if found is not None and len(found):
        view = found.reindex(
            columns=["id", "device_no", "platform_type", "response_status", "create_time"]
        ).copy()
        view.insert(0, "✓", False)
        edited = st.data_editor(
            view,
            key="equral_select_table",
            use_container_width=True,
            height=350,
            hide_index=True,
            column_config={
                "✓": st.column_config.CheckboxColumn(t("col_check_q"), default=False),
                "id": st.column_config.NumberColumn("id", format="%d"),
                "device_no": "device_no",
                "platform_type": t("col_type_short"),
                "response_status": st.column_config.NumberColumn("HTTP", format="%d"),
                "create_time": t("col_date_short"),
            },
            disabled=[c for c in view.columns if c != "✓"],
        )
        selected = edited[edited["✓"]]
        st.caption(t("checked_of", sel=len(selected), total=len(edited)))
        if st.button(
            t("btn_check_selected", n=len(selected)),
            type="primary",
            disabled=not len(selected),
        ):
            devices = selected["device_no"].dropna().astype(str).str.strip().tolist()
            with st.spinner(t("checking_spinner")):
                try:
                    res = equral.check_devices(devices)
                except Exception as e:
                    st.error(t("equral_query_error", e=e))
                    st.stop()
            _show_result_table(res, "equral_selected.xlsx")
    elif found is not None:
        st.info(t("no_records"))

# --- Режим 3: из файла --------------------------------------------------------
else:
    st.subheader(t("file_repush_header"))
    st.markdown(t("file_check_intro"))
    up = st.file_uploader(t("file_label"), type=["xlsx", "csv"], key="equral_file")
    if up:
        if up.name.endswith(".csv"):
            raw = pd.read_csv(up, dtype=str)
        else:
            raw = pd.read_excel(up, dtype=str)
        raw.columns = [c.strip() for c in raw.columns]
        dev_col = next(
            (c for c in raw.columns if c.lower() in ("device_no", "пу", "счётчик", "заводской номер")),
            None,
        )
        if not dev_col:
            st.error(t("no_dev_col"))
            st.stop()
        devices = raw[dev_col].dropna().astype(str).str.strip()
        devices = sorted({d for d in devices if d})
        st.caption(t("unique_devices", n=len(devices)))
        if st.button(t("btn_check_equral"), type="primary", disabled=not devices):
            with st.spinner(t("checking_one_request")):
                try:
                    res = equral.check_devices(devices)
                except Exception as e:
                    st.error(t("equral_query_error", e=e))
                    st.stop()
            st.success(t("checked_n", n=len(res)))
            _show_result_table(res, "equral_file.xlsx")
