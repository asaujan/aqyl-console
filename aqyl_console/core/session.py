"""Работа с MMS-куки в рамках сессии Streamlit.

Куки, введённые в UI, кладутся в st.session_state и переопределяют значение
из .env (config.MMS_COOKIE), которое остаётся значением по умолчанию.
"""
import streamlit as st

from aqyl_console.core import config

# Ключ хранения куки в session_state
_KEY = "mms_cookie"

# Пошаговая инструкция, как достать строку Cookie из DevTools
COOKIE_HELP_STEPS = """
1. Открой http://lifecycle-mgmt.ktga.kz:32068/ в браузере (VPN GlobalProtect включён, hosts прописан).
2. Если разлогинило, войди (admin / eslink@2026).
3. Правая кнопка на странице, Просмотреть код (или Cmd+Option+I на маке).
4. Вкладка Network, фильтр Fetch/XHR.
5. Нажми Query на странице чтобы появился запрос.
6. Клик на строку device-sync-records, вкладка Headers.
7. Прокрути до Request Headers, найди строку Cookie.
8. Скопируй всё значение и вставь в поле выше.
"""


def get_mms_cookie() -> str:
    """Куки из UI (session_state), если заданы, иначе из config.MMS_COOKIE (.env)."""
    ui_val = str(st.session_state.get(_KEY, "")).strip()
    return ui_val or config.MMS_COOKIE


def set_mms_cookie(value: str) -> None:
    """Сохранить куки в session_state."""
    st.session_state[_KEY] = (value or "").strip()


def has_mms_cookie() -> bool:
    """Заданы ли куки (в UI или в .env) и похожи ли на валидную сессию."""
    cookie = get_mms_cookie()
    return bool(cookie.strip()) and "JSESSIONID" in cookie


def _help_block(context: str) -> None:
    """Раскрывающийся блок с пошаговой инструкцией (через чекбокс,
    так как вложенные expander в Streamlit не допускаются)."""
    if st.checkbox("Как получить куки", key=f"cookie_help_{context}"):
        st.markdown(COOKIE_HELP_STEPS)


def render_cookie_controls(context: str, with_steps: bool = True) -> None:
    """Поле ввода куки, кнопка сохранения, статус и (опционально) инструкция.

    context: уникальный префикс для ключей виджетов (напр. "page2", "sidebar").
    Каждый text_area и кнопка получают уникальный key на основе context,
    чтобы сайдбар и страница репуша не делили один виджет. Сами куки при этом
    всегда хранятся в фиксированном ключе session_state (см. set_mms_cookie).
    """
    if has_mms_cookie():
        st.success("Куки заданы")
    else:
        st.warning("Куки не заданы")

    # Сообщение об успешном сохранении переживает st.rerun через флаг.
    if st.session_state.pop("cookie_saved_flag", False):
        st.success("Куки сохранены")

    st.caption("Где взять: DevTools, вкладка Network, Request Headers, строка Cookie.")

    val = st.text_area(
        "Строка Cookie из DevTools",
        key=f"cookie_input_{context}",
        height=100,
        placeholder="loginName=...; SESSION=...; JSESSIONID=...",
    )
    if st.button("Сохранить куки", key=f"cookie_save_{context}"):
        if val.strip():
            set_mms_cookie(val)
            st.session_state["cookie_saved_flag"] = True
            st.rerun()
        else:
            st.warning("Поле пустое, вставь строку Cookie.")

    if with_steps:
        _help_block(context)


def render_cookie_sidebar() -> None:
    """Компактное поле ввода куки в сайдбаре, доступно с любой страницы."""
    with st.sidebar:
        st.markdown("### MMS куки")
        render_cookie_controls("sidebar", with_steps=False)
