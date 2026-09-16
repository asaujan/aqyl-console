"""Проверка установки счётчика в e-Qural (БД mds).

Три режима: одиночная, по выбору из dl_device_sync, из файла. Вердикт строится
на данных mds (не на response_status, который для EQURAL ненадёжен).
"""
import io
import pandas as pd
import streamlit as st

from aqyl_console.core import db, equral, config, session

st.set_page_config(page_title="Проверка e-Qural", page_icon="✅", layout="wide")
st.title("✅ Проверка установки в e-Qural")
st.caption("Истина в базе mds: реально установлен = статус Installed и есть привязка к абоненту.")

session.render_cookie_sidebar()

# Колонки результата в человекочитаемом виде.
RESULT_COLS_RU = {
    "device_no": "Счётчик (device_no)",
    "status_name": "Статус mds",
    "really_installed": "Реально установлен",
    "personal_account": "ЛС",
    "region_kato": "Регион (КАТО)",
    "region_name": "Регион",
    "is_blocked_flag": "Флаг блокировки",
    "date_create": "Создан",
    "date_update": "Обновлён",
    "Вердикт e-Qural": "Вердикт e-Qural",
}
RESULT_ORDER = [
    "device_no", "Вердикт e-Qural", "status_name", "really_installed",
    "personal_account", "region_kato", "region_name", "is_blocked_flag",
    "date_create", "date_update",
]

# Цвета фона для колонки вердикта.
_BG = {"green": "#1b5e20", "yellow": "#8d6e00", "red": "#7f1d1d"}


def _style_verdict(df: pd.DataFrame):
    """Styler: подсветить колонку 'Вердикт e-Qural' по цвету вердикта."""
    def color(val):
        c = equral.VERDICT_COLOR.get(val)
        return f"background-color: {_BG[c]}; color: white" if c else ""
    return df.style.map(color, subset=["Вердикт e-Qural"]) \
        if "Вердикт e-Qural" in df.columns else df.style


def _prep_view(res: pd.DataFrame) -> pd.DataFrame:
    """Готовит результат к показу: порядок и русские заголовки колонок."""
    cols = [c for c in RESULT_ORDER if c in res.columns]
    return res.reindex(columns=cols).rename(columns=RESULT_COLS_RU)


def _summary(res: pd.DataFrame) -> None:
    """Сводка внизу массовой проверки: установлено и не прошло по причинам."""
    counts = res["Вердикт e-Qural"].value_counts()
    installed = int(counts.get(equral.V_INSTALLED, 0))
    total = len(res)
    failed = total - installed
    st.divider()
    st.subheader("Сводка")
    m1, m2, m3 = st.columns(3)
    m1.metric("Всего проверено", total)
    m2.metric("Установлен в e-Qural", installed)
    m3.metric("Не прошло / проблемы", failed)
    # Разбивка по причинам (всё, кроме успешной установки).
    reasons = counts.drop(labels=[equral.V_INSTALLED], errors="ignore")
    if not reasons.empty:
        st.markdown("**Разбивка не прошедших по причинам:**")
        breakdown = reasons.reset_index()
        breakdown.columns = ["Причина", "Количество"]
        st.dataframe(breakdown, use_container_width=True, hide_index=True)


def _show_result_table(res: pd.DataFrame, filename: str) -> None:
    """Общий блок: таблица с подсветкой вердикта, сводка, экспорт в Excel."""
    if res.empty:
        st.warning("Нет данных для показа.")
        return
    view = _prep_view(res)
    st.dataframe(_style_verdict(view), use_container_width=True, height=460)
    _summary(res)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        view.to_excel(w, index=False, sheet_name="equral")
    st.download_button(
        "⬇ Экспорт в Excel",
        buf.getvalue(),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


mode = st.radio(
    "Способ проверки",
    ["Одиночная", "По выбору из таблицы", "Из файла"],
    horizontal=True,
)
st.divider()

# --- Режим 1: одиночная проверка ---------------------------------------------
if mode == "Одиночная":
    st.subheader("Одиночная проверка")
    device_no = st.text_input("Счётчик (device_no)", placeholder="например 0123456789")
    if st.button("Проверить в e-Qural", type="primary", disabled=not device_no.strip()):
        try:
            res = equral.check_devices([device_no])
        except Exception as e:
            st.error(f"Ошибка запроса к e-Qural: {e}")
            st.stop()
        if res.empty:
            st.warning("Пустой ввод.")
            st.stop()
        row = res.iloc[0]
        verdict = row["Вердикт e-Qural"]
        color = equral.VERDICT_COLOR.get(verdict, "red")
        if color == "green":
            st.success(f"Вердикт: {verdict}")
        elif color == "yellow":
            st.warning(f"Вердикт: {verdict}")
        else:
            st.error(f"Вердикт: {verdict}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Статус mds", row["status_name"] if pd.notna(row["status_name"]) else "нет в mds")
        c2.metric("Реально установлен", "Да" if row["really_installed"] else "Нет")
        c3.metric("Флаг блокировки", "Да" if row["is_blocked_flag"] else "Нет")

        st.markdown(
            f"- **Привязка к абоненту:** {'есть' if row['has_consumer'] else 'нет'}\n"
            f"- **Лицевой счёт (ЛС):** {row['personal_account'] or 'нет'}\n"
            f"- **Регион:** {row['region_name'] or 'нет'} "
            f"({row['region_kato'] if pd.notna(row['region_kato']) else 'нет КАТО'})\n"
            f"- **Создан:** {row['date_create'] or 'нет'}\n"
            f"- **Обновлён:** {row['date_update'] or 'нет'}"
        )

# --- Режим 2: выбор из dl_device_sync ----------------------------------------
elif mode == "По выбору из таблицы":
    st.subheader("Подбор записей EQURAL по фильтрам, выбор галочками")
    st.caption("Отмеченные device_no проверяются в mds. response_status тут только для справки.")
    with st.form("equral_filters"):
        c1, c2, c3 = st.columns(3)
        with c1:
            region = st.selectbox(
                "Регион", ["Все"] + [f"{k}: {v}" for k, v in config.REGIONS.items()]
            )
            platform = st.multiselect(
                "Тип платформы", ["EQURAL", "BILING-INSTALL", "BILING-REMOVE", "KAZGAS_IOT"],
                default=["EQURAL"],
            )
        with c2:
            status = st.multiselect("HTTP статус", [200, 204, 400, 401, 500, 502])
            device_no = st.text_input("Счётчик (device_no)")
        with c3:
            date_from = st.date_input("Дата с", value=None)
            date_to = st.date_input("Дата по", value=None)
        limit = st.slider("Лимит строк", 50, 5000, 500, step=50)
        submitted = st.form_submit_button("Показать записи", type="primary")

    if submitted:
        where = []
        params = {}
        if region != "Все":
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
            st.error(f"Ошибка запроса: {e}")
            st.stop()
        st.caption(f"Найдено строк: {len(found)}")
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
                "✓": st.column_config.CheckboxColumn("Проверить?", default=False),
                "id": st.column_config.NumberColumn("id", format="%d"),
                "device_no": "device_no",
                "platform_type": "Тип",
                "response_status": st.column_config.NumberColumn("HTTP", format="%d"),
                "create_time": "Дата",
            },
            disabled=[c for c in view.columns if c != "✓"],
        )
        selected = edited[edited["✓"]]
        st.caption(f"Отмечено: {len(selected)} из {len(edited)}")
        if st.button(
            f"Проверить выбранные ({len(selected)})",
            type="primary",
            disabled=not len(selected),
        ):
            devices = selected["device_no"].dropna().astype(str).str.strip().tolist()
            with st.spinner("Проверяю в e-Qural..."):
                try:
                    res = equral.check_devices(devices)
                except Exception as e:
                    st.error(f"Ошибка запроса к e-Qural: {e}")
                    st.stop()
            _show_result_table(res, "equral_selected.xlsx")
    elif found is not None:
        st.info("Записи не найдены.")

# --- Режим 3: из файла --------------------------------------------------------
else:
    st.subheader("Загрузка из файла")
    st.markdown("Загрузи Excel/CSV со столбцом `device_no`. Дубли и пробелы уберу сам.")
    up = st.file_uploader("Файл", type=["xlsx", "csv"], key="equral_file")
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
            st.error("Не нашёл столбец device_no / ПУ в файле.")
            st.stop()
        devices = raw[dev_col].dropna().astype(str).str.strip()
        devices = sorted({d for d in devices if d})
        st.caption(f"Уникальных device_no: {len(devices)}")
        if st.button("Проверить в e-Qural", type="primary", disabled=not devices):
            with st.spinner("Проверяю в e-Qural одним запросом..."):
                try:
                    res = equral.check_devices(devices)
                except Exception as e:
                    st.error(f"Ошибка запроса к e-Qural: {e}")
                    st.stop()
            st.success(f"Проверено device_no: {len(res)}")
            _show_result_table(res, "equral_file.xlsx")
