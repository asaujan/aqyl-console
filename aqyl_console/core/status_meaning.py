"""Расшифровка HTTP-кодов и категоризация ошибок Billing по тексту ответа.

Смысл кода зависит от платформы: у EQURAL успех это 204 (No Content),
у Billing успех это 200. Тексты без длинного тире (стиль проекта).
Человекочитаемые расшифровки хранятся ключами переводов (core.i18n),
поэтому язык вывода следует за переключателем RU/EN.
"""
import pandas as pd

from aqyl_console.core.i18n import t

# Ключ перевода смысла HTTP-кода в разрезе платформы. Ключи внешнего словаря
# совпадают с platform_type в dl_device_sync.
HTTP_MEANING_KEYS = {
    "BILING-INSTALL": {
        200: "http_billing_200",
        400: "http_billing_400",
        401: "http_401",
        500: "http_billing_500",
        502: "http_billing_502",
    },
    "BILING-REMOVE": {
        200: "http_billing_200",
        400: "http_billing_400",
        401: "http_401",
        500: "http_billing_500",
        502: "http_billing_502",
    },
    "EQURAL": {
        204: "http_equral_204",
        400: "http_equral_400",
        500: "http_equral_500",
    },
    "KAZGAS_IOT": {
        200: "http_kazgas_200",
    },
}

# Какой HTTP-код считается успехом для платформы.
SUCCESS_CODE = {
    "BILING-INSTALL": 200,
    "BILING-REMOVE": 200,
    "EQURAL": 204,
    "KAZGAS_IOT": 200,
}


def _to_int(code):
    """HTTP-код может прийти строкой/float/NaN, приводим к int или None."""
    if code is None or (not isinstance(code, (int, str)) and pd.isna(code)):
        return None
    try:
        return int(code)
    except (ValueError, TypeError):
        return None


def http_meaning(platform, code) -> str:
    """Смысл HTTP-кода для платформы. Неизвестное сочетание даёт 'HTTP N'."""
    c = _to_int(code)
    plat = str(platform).strip() if platform is not None else ""
    table = HTTP_MEANING_KEYS.get(plat, {})
    if c is None:
        return t("status_no_code")
    if c in table:
        return t(table[c])
    return f"HTTP {c}"


def is_success(platform, code) -> bool:
    """Успех с учётом платформы: EQURAL это 204, остальные 200."""
    c = _to_int(code)
    if c is None:
        return False
    plat = str(platform).strip() if platform is not None else ""
    return c == SUCCESS_CODE.get(plat, 200)


# Категории ошибок Billing по подстрокам в тексте ответа. Порядок важен,
# первое совпадение определяет категорию. Значение: ключи перевода
# (метка, пояснение). Подстроки не переводятся, ответы Billing всегда русские.
_BILLING_RULES = [
    (["уже есть в системе"], ("err_dup", "err_dup_desc")),
    (["точка учета не заполнена", "заблокирована", "уже установлен"],
     ("err_point_busy", "err_point_busy_desc")),
    (["не найден прибор учета"], ("err_no_meter", "err_no_meter_desc")),
    (["не найден абонент", "лицевой счет"], ("err_no_account", "err_no_account_desc")),
    (["ошибка при снятии", "context method"], ("err_remove_fail", "err_remove_fail_desc")),
]


def classify_billing_error(text) -> tuple[str, str]:
    """Категория и пояснение ошибки Billing по тексту ответа.

    text может быть NaN/None/не строкой, безопасно приводим к str.
    Возвращает (Прочее/Other, первые 100 символов) если ничего не подошло.
    """
    if text is None or (not isinstance(text, str) and pd.isna(text)):
        return (t("err_other"), "")
    s = str(text)
    low = s.lower()
    if not low.strip() or low.strip() == "nan":
        return (t("err_other"), "")
    for needles, (label_key, desc_key) in _BILLING_RULES:
        if any(n in low for n in needles):
            return (t(label_key), t(desc_key))
    return (t("err_other"), s[:100])
