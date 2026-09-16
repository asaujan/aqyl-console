"""Aqyl Console: internal MMS/Billing operations dashboard."""
import streamlit as st

st.set_page_config(page_title="Aqyl Console", page_icon="⚡", layout="wide")

st.title("⚡ Aqyl Console")
st.caption("Внутренний пульт по интеграции MMS · Billing · e-Qural")

from aqyl_console.core import db, config, session

session.render_cookie_sidebar()

col1, col2, col3, col4 = st.columns(4)

with col1:
    ok, msg = db.test_connection()
    if ok:
        st.success(f"БД device_life: подключено ({config.DB_HOST})")
    else:
        st.error(f"БД: {msg}")

with col2:
    if not config.EQURAL_DB_USER:
        st.warning("e-Qural (mds): креды не заданы")
    else:
        ok, msg = db.test_equral_connection()
        if ok:
            st.success(f"БД e-Qural (mds): подключено ({config.EQURAL_DB_HOST})")
        else:
            st.error(f"e-Qural: {msg}")

with col3:
    if config.MMS_COOKIE and "JSESSIONID" in config.MMS_COOKIE:
        st.info("MMS cookie: задан")
    else:
        st.warning("MMS cookie: не задан (нужен для репуша)")

with col4:
    if config.BILLING_PASSWORD:
        st.info("Billing: креды заданы")
    else:
        st.warning("Billing: креды не заданы")

st.divider()
st.markdown(
    """
    ### Разделы (слева в меню):
    1. **Просмотр синхронизации**: таблица dl_device_sync с фильтрами и экспортом
    2. **Массовый репуш**: загрузка списка, автоподбор id, прогон с логом
    3. **Проверка в Billing**: статус ПУ и ЛС в 1С, сверка ожидаемого с фактическим
    4. **Статистика**: дашборд по dl_device_sync (динамика, регионы, платформы, ошибки Billing)
    5. **Проверка e-Qural**: реальная установка в БД mds (одиночная, по выбору, из файла)

    Настройки подключения: в файле `.env` (скопировать из `.env.example`).
    """
)
