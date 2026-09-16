"""Расшифровка HTTP-кодов и категоризация ошибок Billing по тексту ответа.

Смысл кода зависит от платформы: у EQURAL успех это 204 (No Content),
у Billing успех это 200. Тексты без длинного тире (стиль проекта).
"""
import pandas as pd

# Смысл HTTP-кода в разрезе платформы. Ключи внешнего словаря совпадают
# с platform_type в dl_device_sync.
HTTP_MEANING = {
    "BILING-INSTALL": {
        200: "Успешно принято Billing",
        400: "Отклонено Billing (см. текст)",
        401: "Сессия истекла",
        500: "Внутренняя ошибка 1С",
        502: "Billing недоступен",
    },
    "BILING-REMOVE": {
        200: "Успешно принято Billing",
        400: "Отклонено Billing (см. текст)",
        401: "Сессия истекла",
        500: "Внутренняя ошибка 1С",
        502: "Billing недоступен",
    },
    "EQURAL": {
        204: "Успешно (No Content)",
        400: "Отклонено e-Qural (проверь реестр)",
        500: "Ошибка сервера",
    },
    "KAZGAS_IOT": {
        200: "Успешно",
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
    table = HTTP_MEANING.get(plat, {})
    if c is None:
        return "нет кода"
    if c in table:
        return table[c]
    return f"HTTP {c}"


def is_success(platform, code) -> bool:
    """Успех с учётом платформы: EQURAL это 204, остальные 200."""
    c = _to_int(code)
    if c is None:
        return False
    plat = str(platform).strip() if platform is not None else ""
    return c == SUCCESS_CODE.get(plat, 200)


# Категории ошибок Billing по подстрокам в тексте ответа. Порядок важен,
# первое совпадение определяет категорию.
_BILLING_RULES = [
    (["уже есть в системе"],
     ("Дубликат в 1С",
      "Счётчик числится в 1С, хотя на MMS дубля нет. Разбирается на стороне Billing.")),
    (["точка учета не заполнена", "заблокирована", "уже установлен"],
     ("Точка учёта занята",
      "Старый счётчик не снят, точка занята. Нужно снятие в 1С.")),
    (["не найден прибор учета"],
     ("ПУ не найден в 1С",
      "Счётчика нет в 1С по этому номеру.")),
    (["не найден абонент", "лицевой счет"],
     ("ЛС не найден в 1С",
      "Лицевой счёт отсутствует в 1С.")),
    (["ошибка при снятии", "context method"],
     ("Внутренняя ошибка 1С при снятии",
      "Сбой на стороне 1С при обработке снятия.")),
]


def classify_billing_error(text) -> tuple[str, str]:
    """Категория и пояснение ошибки Billing по тексту ответа.

    text может быть NaN/None/не строкой, безопасно приводим к str.
    Возвращает ('Прочее', первые 100 символов) если ничего не подошло.
    """
    if text is None or (not isinstance(text, str) and pd.isna(text)):
        return ("Прочее", "")
    s = str(text)
    low = s.lower()
    if not low.strip() or low.strip() == "nan":
        return ("Прочее", "")
    for needles, result in _BILLING_RULES:
        if any(n in low for n in needles):
            return result
    return ("Прочее", s[:100])
