"""Bulk repush: три режима (одиночный, выбор галочками, из файла)."""
import time
import pandas as pd
import streamlit as st

from aqyl_console.core import db, mms, config, session, status_meaning

st.set_page_config(page_title="Массовый репуш", page_icon="🔁", layout="wide")
st.title("🔁 Массовый репуш")

PLATFORMS = ["BILING-INSTALL", "BILING-REMOVE", "EQURAL", "KAZGAS_IOT"]
TABLE_COLS = ["id", "device_no", "platform_type", "response_status", "create_time"]

session.render_cookie_sidebar()

with st.expander("Настройки сессии (куки)", expanded=not session.has_mms_cookie()):
    session.render_cookie_controls("page2", with_steps=True)

if not session.has_mms_cookie():
    st.warning("MMS куки не заданы, репуш вернёт 401. Вставь куки в блоке выше.")


def run_repush(ids, delay, platform_map=None):
    """Гонит репуш по списку id с прогресс-баром и живым логом.

    platform_map: dict id -> platform_type, чтобы показать смысл статуса
    с учётом платформы (у EQURAL успех это 204, у Billing 200).
    """
    ids = [int(x) for x in ids]
    platform_map = platform_map or {}
    progress = st.progress(0.0)
    log_area = st.empty()
    results = []
    total = len(ids)
    for i, rid in enumerate(ids, start=1):
        status, body = mms.repush(rid)
        plat = platform_map.get(rid)
        results.append({
            "id": rid,
            "http": status,
            "смысл": status_meaning.http_meaning(plat, status) if plat else status_meaning.http_meaning("", status),
            "response": body[:120],
        })
        progress.progress(i / total)
        log_area.dataframe(pd.DataFrame(results[-15:]), use_container_width=True)
        time.sleep(delay)
    res_df = pd.DataFrame(results)
    # Успех считаем с учётом платформы, где она известна.
    ok = int(sum(
        status_meaning.is_success(platform_map.get(r["id"], ""), r["http"])
        for _, r in res_df.iterrows()
    ))
    st.success(f"Готово. OK={ok} FAIL={len(res_df) - ok}")
    st.download_button(
        "⬇ Скачать лог",
        res_df.to_csv(index=False).encode(),
        file_name="repush_log.csv",
        mime="text/csv",
    )
    return res_df


def select_from_table(found, key):
    """Показывает таблицу записей с колонкой чекбоксов, возвращает отмеченные id.

    Отметки живут в st.session_state (f"{key}_checks"), кнопки массового
    выделения меняют их целиком и бампают версию ключа data_editor,
    чтобы таблица перерисовалась с новыми галочками.
    """
    if found is None or not len(found):
        st.info("Записи не найдены.")
        return []
    view = found.reindex(columns=TABLE_COLS).copy().reset_index(drop=True)

    checks_key = f"{key}_checks"
    ids_key = f"{key}_ids"
    ver_key = f"{key}_ver"
    current_ids = view["id"].tolist()
    if st.session_state.get(ids_key) != current_ids:
        # Новая выборка: сбрасываем отметки и заставляем editor перерисоваться.
        st.session_state[ids_key] = current_ids
        st.session_state[checks_key] = [False] * len(view)
        st.session_state[ver_key] = st.session_state.get(ver_key, 0) + 1

    b1, b2, b3 = st.columns(3)
    if b1.button("Выделить все", key=f"{key}_check_all", use_container_width=True):
        st.session_state[checks_key] = [True] * len(view)
        st.session_state[ver_key] += 1
    if b2.button("Снять все", key=f"{key}_uncheck_all", use_container_width=True):
        st.session_state[checks_key] = [False] * len(view)
        st.session_state[ver_key] += 1
    if b3.button("Только неуспешные", key=f"{key}_check_failed", use_container_width=True):
        st.session_state[checks_key] = [
            not status_meaning.is_success(r.get("platform_type"), r.get("response_status"))
            for _, r in view.iterrows()
        ]
        st.session_state[ver_key] += 1

    view.insert(0, "✓", st.session_state[checks_key])
    edited = st.data_editor(
        view,
        key=f"{key}_editor_v{st.session_state[ver_key]}",
        use_container_width=True,
        height=350,
        hide_index=True,
        column_config={
            "✓": st.column_config.CheckboxColumn("Репуш?", default=False),
            "id": st.column_config.NumberColumn("id", format="%d"),
            "device_no": "device_no",
            "platform_type": "Тип",
            "response_status": st.column_config.NumberColumn("HTTP", format="%d"),
            "create_time": "Дата",
        },
        disabled=[c for c in view.columns if c != "✓"],
    )
    # Ручные клики по чекбоксам тоже сохраняем, чтобы пережили любой rerun.
    st.session_state[checks_key] = edited["✓"].tolist()
    selected = edited[edited["✓"]]
    st.caption(f"Отмечено: {len(selected)} из {len(edited)}")
    delay = st.number_input(
        "Задержка между запросами (сек)", 0.2, 5.0, 1.0, 0.1, key=f"{key}_delay"
    )
    if st.button(
        f"🚀 Репушнуть выбранные ({len(selected)})",
        type="primary",
        disabled=not len(selected),
        key=f"{key}_run",
    ):
        pmap = {}
        if "platform_type" in selected.columns:
            pmap = {int(r["id"]): r["platform_type"] for _, r in selected.iterrows()}
        run_repush(selected["id"].tolist(), delay, pmap)
    return selected["id"].tolist()


mode = st.radio(
    "Способ репуша",
    ["Одиночный", "По выбору из таблицы", "Из файла"],
    horizontal=True,
)
st.divider()

# --- Режим 1: одиночный репуш -------------------------------------------------
if mode == "Одиночный":
    st.subheader("Одиночный репуш")
    kind = st.radio("Что введено", ["id", "device_no"], horizontal=True)
    value = st.text_input("Значение", placeholder="например 123456 или KZ00123456")
    platform = None
    if kind == "device_no":
        platform = st.selectbox("Тип операции для подбора id", PLATFORMS)

    if st.button("🚀 Репушнуть", type="primary", disabled=not value.strip()):
        val = value.strip()
        rid = None
        if kind == "id":
            if not val.isdigit():
                st.error("id должен быть числом.")
                st.stop()
            rid = int(val)
        else:
            sql = """
                SELECT id, device_no, platform_type, response_status, create_time
                FROM dl_device_sync
                WHERE device_no = :dev AND platform_type = :pt
                ORDER BY id DESC LIMIT 1
            """
            try:
                found = db.run_query(sql, {"dev": val, "pt": platform})
            except Exception as e:
                st.error(f"Ошибка запроса: {e}")
                st.stop()
            if not len(found):
                st.error(f"Не нашёл записей по device_no={val} и типу {platform}.")
                st.stop()
            row = found.iloc[0]
            rid = int(row["id"])
            st.info(
                f"Найден id={rid} (device_no={row['device_no']}, "
                f"тип {row['platform_type']}, HTTP {row['response_status']}, "
                f"дата {row['create_time']})."
            )

        with st.spinner("Отправляю репуш..."):
            status, body = mms.repush(rid)
        meaning = status_meaning.http_meaning(platform or "", status)
        if status_meaning.is_success(platform or "", status):
            st.success(f"id={rid}: HTTP {status} ({meaning})")
        else:
            st.error(f"id={rid}: HTTP {status} ({meaning})")
        st.code(body or "(пустой ответ)")

# --- Режим 2: выбор галочками по фильтрам ------------------------------------
elif mode == "По выбору из таблицы":
    st.subheader("Подбор записей по фильтрам, выбор галочками")
    with st.form("table_filters"):
        c1, c2, c3 = st.columns(3)
        with c1:
            region = st.selectbox(
                "Регион", ["Все"] + [f"{k}: {v}" for k, v in config.REGIONS.items()]
            )
            platform = st.multiselect("Тип платформы", PLATFORMS)
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

        sql = "SELECT id, device_no, platform_type, response_status, create_time FROM dl_device_sync"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += f" ORDER BY id DESC LIMIT {int(limit)}"
        try:
            found = db.run_query(sql, params)
        except Exception as e:
            st.error(f"Ошибка запроса: {e}")
            st.stop()
        st.caption(f"Найдено строк: {len(found)}")
        st.session_state["table_found"] = found

    found = st.session_state.get("table_found")
    if found is not None:
        select_from_table(found, key="filter_table")

# --- Режим 3: из файла --------------------------------------------------------
else:
    st.subheader("Загрузка из файла")
    st.markdown("**Шаг 1.** Загрузи Excel/CSV со столбцом `device_no` (или `id`).")
    up = st.file_uploader("Файл", type=["xlsx", "csv"])

    platform = st.selectbox(
        "Тип операции для подбора id (если в файле только device_no)", PLATFORMS
    )
    only_failed = st.checkbox("Только неуспешные (400/500) последние попытки", value=False)

    found = None
    if up:
        if up.name.endswith(".csv"):
            raw = pd.read_csv(up, dtype=str)
        else:
            raw = pd.read_excel(up, dtype=str)
        raw.columns = [c.strip() for c in raw.columns]
        st.caption(f"Загружено строк: {len(raw)}. Колонки: {list(raw.columns)}")

        if "id" in raw.columns:
            ids = tuple(raw["id"].dropna().astype(str).str.strip().unique())
            st.info(f"В файле есть id, беру напрямую ({len(ids)}).")
            sql = """
                SELECT id, device_no, platform_type, response_status, create_time
                FROM dl_device_sync
                WHERE id IN :ids
                ORDER BY id
            """
            try:
                found = db.run_query(sql, {"ids": ids})
            except Exception as e:
                st.error(f"Ошибка запроса: {e}")
                st.stop()
            # id, которых нет в базе, всё равно можно репушнуть напрямую
            known = set(found["id"].astype(str))
            missing = [x for x in ids if x not in known]
            if missing:
                extra = pd.DataFrame({"id": [int(x) for x in missing]})
                found = pd.concat([found, extra], ignore_index=True)
        else:
            dev_col = next(
                (c for c in raw.columns if c.lower() in ("device_no", "пу", "заводской номер")),
                None,
            )
            if not dev_col:
                st.error("Не нашёл столбец device_no / ПУ в файле.")
                st.stop()
            devices = tuple(raw[dev_col].dropna().astype(str).str.strip().unique())
            st.caption(f"Уникальных device_no: {len(devices)}")

            sql = """
                SELECT id, device_no, platform_type, response_status, create_time
                FROM dl_device_sync
                WHERE platform_type = :pt AND device_no IN :devs
                ORDER BY id
            """
            try:
                found = db.run_query(sql, {"pt": platform, "devs": devices})
            except Exception as e:
                st.error(f"Ошибка запроса: {e}")
                st.stop()
            found = found.sort_values("id").drop_duplicates("device_no", keep="last")
            if only_failed:
                found = found[found["response_status"].isin([400, 500])]
        st.success(f"Подобрано записей: {len(found)}")

    if found is not None and len(found):
        st.markdown("**Шаг 2.** Отметь галочками и запусти репуш.")
        select_from_table(found, key="file_table")
