"""Работа с MMS-куки в рамках сессии Streamlit.

Куки, введённые в UI, кладутся в st.session_state и переопределяют значение
из .env (config.MMS_COOKIE), которое остаётся значением по умолчанию.
Здесь же живёт переключатель языка интерфейса (RU/EN), общий для всех страниц.
"""
import streamlit as st

from aqyl_console.core import config
from aqyl_console.core.i18n import t

# Ключ хранения куки в session_state
_KEY = "mms_cookie"

# Ключ хранения языка и отдельный ключ виджета-переключателя.
# Данные живут в фиксированных ключах, а не в ключах виджетов: Streamlit
# чистит состояние виджета, если тот не отрисован в текущем прогоне,
# поэтому виджеты только читают и пишут фиксированные ключи.
_LANG_KEY = "lang"
_LANG_WIDGET_KEY = "lang_selector"

# Подпись вариантов языка в переключателе
_LANG_LABELS = {"ru": "RU", "en": "EN"}


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


def init_state() -> None:
    """Инициализация фиксированных ключей session_state (один раз за сессию)."""
    if st.session_state.get(_LANG_KEY) not in _LANG_LABELS:
        st.session_state[_LANG_KEY] = "ru"
    st.session_state.setdefault(_KEY, "")


def _apply_lang_choice() -> None:
    """on_change виджета: переносит выбор в фиксированный ключ языка."""
    st.session_state[_LANG_KEY] = st.session_state[_LANG_WIDGET_KEY]


def render_language_selector() -> None:
    """Переключатель языка RU/EN. Выбор хранится в st.session_state['lang'].

    Виджет живёт под своим ключом, значение берёт из session_state['lang']
    через index, а пишет туда же через on_change. Колбэк срабатывает до
    rerun, поэтому новые тексты (включая заголовки навигации) применяются
    сразу ко всем страницам.
    """
    init_state()
    langs = list(_LANG_LABELS)
    st.radio(
        t("lang_label"),
        options=langs,
        index=langs.index(st.session_state[_LANG_KEY]),
        format_func=_LANG_LABELS.get,
        horizontal=True,
        key=_LANG_WIDGET_KEY,
        on_change=_apply_lang_choice,
    )


def _help_block(context: str) -> None:
    """Раскрывающийся блок с пошаговой инструкцией (через чекбокс,
    так как вложенные expander в Streamlit не допускаются)."""
    if st.checkbox(t("cookie_help_toggle"), key=f"cookie_help_{context}"):
        st.markdown(t("cookie_help_steps"))


def render_cookie_controls(context: str, with_steps: bool = True) -> None:
    """Поле ввода куки, кнопка сохранения, статус и (опционально) инструкция.

    context: уникальный префикс для ключей виджетов (напр. "page2", "sidebar").
    Каждый text_area и кнопка получают уникальный key на основе context,
    чтобы сайдбар и страница репуша не делили один виджет. Сами куки при этом
    всегда хранятся в фиксированном ключе session_state (см. set_mms_cookie),
    а виджет при первом показе засеивается сохранённым значением, поэтому
    поле не пустеет после перехода между страницами.
    """
    if has_mms_cookie():
        st.success(t("cookie_set"))
    else:
        st.warning(t("cookie_not_set"))

    # Сообщение об успешном сохранении переживает st.rerun через флаг.
    if st.session_state.pop("cookie_saved_flag", False):
        st.success(t("cookie_saved"))

    st.caption(t("cookie_where"))

    widget_key = f"cookie_input_{context}"
    if widget_key not in st.session_state:
        st.session_state[widget_key] = st.session_state.get(_KEY, "")
    val = st.text_area(
        t("cookie_input_label"),
        key=widget_key,
        height=100,
        placeholder="loginName=...; SESSION=...; JSESSIONID=...",
    )
    if st.button(t("cookie_save_btn"), key=f"cookie_save_{context}"):
        if val.strip():
            set_mms_cookie(val)
            st.session_state["cookie_saved_flag"] = True
            st.rerun()
        else:
            st.warning(t("cookie_empty_warn"))

    if with_steps:
        _help_block(context)


def render_cookie_sidebar() -> None:
    """Сайдбар, общий для всех страниц: язык наверху, ниже поле ввода куки."""
    with st.sidebar:
        render_language_selector()
        st.markdown(f"### {t('sidebar_cookie_header')}")
        render_cookie_controls("sidebar", with_steps=False)
