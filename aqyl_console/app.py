"""Aqyl Console: точка входа с программной навигацией (st.navigation).

Страницы объявлены через st.Page с заголовками из словаря переводов,
поэтому боковое меню переводится вместе с остальным интерфейсом.
Сайдбар (язык, куки) рендерится здесь и общий для всех страниц: на каждом
rerun навигация пересобирается с заголовками на текущем языке.
"""
import streamlit as st

st.set_page_config(page_title="Aqyl Console", page_icon="⚡", layout="wide")

from aqyl_console.core import session
from aqyl_console.core.i18n import t

session.init_state()
session.render_cookie_sidebar()

nav = st.navigation([
    st.Page("views/home.py", title=t("nav_home"), icon="⚡", default=True),
    st.Page("views/sync.py", title=t("nav_sync"), icon="📋"),
    st.Page("views/repush.py", title=t("nav_repush"), icon="🔁"),
    st.Page("views/billing.py", title=t("nav_billing"), icon="🔎"),
    st.Page("views/stats.py", title=t("nav_stats"), icon="📊"),
    st.Page("views/equral.py", title=t("nav_equral"), icon="✅"),
])
nav.run()
