"""Главная страница: статус подключений (БД, e-Qural, куки MMS, Billing)."""
import streamlit as st

from aqyl_console.core import db, config, session
from aqyl_console.core.i18n import t

st.title("⚡ Aqyl Console")
st.caption(t("app_caption"))

col1, col2, col3, col4 = st.columns(4)

with col1:
    ok, msg = db.test_connection()
    if ok:
        st.success(t("app_db_ok", host=config.DB_HOST))
    else:
        st.error(t("app_db_err", msg=msg))

with col2:
    if not config.EQURAL_DB_USER:
        st.warning(t("app_equral_no_creds"))
    else:
        ok, msg = db.test_equral_connection()
        if ok:
            st.success(t("app_equral_ok", host=config.EQURAL_DB_HOST))
        else:
            st.error(t("app_equral_err", msg=msg))

with col3:
    if session.has_mms_cookie():
        st.info(t("app_cookie_set"))
    else:
        st.warning(t("app_cookie_missing"))

with col4:
    if config.BILLING_PASSWORD:
        st.info(t("app_billing_ok"))
    else:
        st.warning(t("app_billing_missing"))

st.divider()
st.markdown(t("app_sections_md"))
