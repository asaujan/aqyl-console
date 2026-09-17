"""Переводы интерфейса RU/EN.

Текущий язык хранится в st.session_state["lang"] ("ru" по умолчанию).
t(key) возвращает перевод для текущего языка, при отсутствии ключа
падает обратно на русский, затем на сам ключ. Поддерживает подстановки:
t("rows_found", n=10) применяет str.format к тексту.

Данные из БД (регионы, platform_type, тексты ответов) не переводятся,
только элементы интерфейса.
"""
import streamlit as st

DEFAULT_LANG = "ru"

TRANSLATIONS = {
    "ru": {
        # --- Навигация (боковое меню, app.py) ---
        "nav_home": "Главная",
        "nav_sync": "Просмотр синхронизации",
        "nav_repush": "Массовый репуш",
        "nav_billing": "Проверка в Billing",
        "nav_stats": "Статистика",
        "nav_equral": "Проверка e-Qural",

        # --- Общее ---
        "lang_label": "Язык / Language",
        "all_option": "Все",
        "query_error": "Ошибка запроса: {e}",
        "rows_found": "Найдено строк: {n}",
        "export_excel": "⬇ Экспорт в Excel",
        "filter_region": "Регион",
        "filter_platform": "Тип платформы",
        "filter_http": "HTTP статус",
        "filter_device": "Счётчик (device_no)",
        "filter_date_from": "Дата с",
        "filter_date_to": "Дата по",
        "filter_limit": "Лимит строк",
        "btn_show": "Показать",
        "btn_show_records": "Показать записи",
        "mode_table": "По выбору из таблицы",
        "mode_file": "Из файла",
        "no_records": "Записи не найдены.",
        "checked_of": "Отмечено: {sel} из {total}",
        "col_type_short": "Тип",
        "col_date_short": "Дата",
        "no_dev_col": "Не нашёл столбец device_no / ПУ в файле.",
        "unique_devices": "Уникальных device_no: {n}",
        "file_label": "Файл",
        "val_yes": "Да",
        "val_no": "Нет",

        # --- Главная (app.py) ---
        "app_caption": "Внутренний пульт по интеграции MMS · Billing · e-Qural",
        "app_db_ok": "БД device_life: подключено ({host})",
        "app_db_err": "БД: {msg}",
        "app_equral_no_creds": "e-Qural (mds): креды не заданы",
        "app_equral_ok": "БД e-Qural (mds): подключено ({host})",
        "app_equral_err": "e-Qural: {msg}",
        "app_cookie_set": "MMS cookie: задан",
        "app_cookie_missing": "MMS cookie: не задан (нужен для репуша)",
        "app_billing_ok": "Billing: креды заданы",
        "app_billing_missing": "Billing: креды не заданы",
        "app_sections_md": """
    ### Разделы (слева в меню):
    1. **Просмотр синхронизации**: таблица dl_device_sync с фильтрами и экспортом
    2. **Массовый репуш**: загрузка списка, автоподбор id, прогон с логом
    3. **Проверка в Billing**: статус ПУ и ЛС в 1С, сверка ожидаемого с фактическим
    4. **Статистика**: дашборд по dl_device_sync (динамика, регионы, платформы, ошибки Billing)
    5. **Проверка e-Qural**: реальная установка в БД mds (одиночная, по выбору, из файла)

    Настройки подключения: в файле `.env` (скопировать из `.env.example`).
    """,

        # --- Куки (core/session.py) ---
        "sidebar_cookie_header": "MMS куки",
        "cookie_set": "Куки заданы",
        "cookie_not_set": "Куки не заданы",
        "cookie_saved": "Куки сохранены",
        "cookie_where": "Где взять: DevTools, вкладка Network, Request Headers, строка Cookie.",
        "cookie_input_label": "Строка Cookie из DevTools",
        "cookie_save_btn": "Сохранить куки",
        "cookie_empty_warn": "Поле пустое, вставь строку Cookie.",
        "cookie_help_toggle": "Как получить куки",
        "cookie_help_steps": """
1. Открой http://lifecycle-mgmt.ktga.kz:32068/ в браузере (VPN GlobalProtect включён, hosts прописан).
2. Если разлогинило, войди (admin / eslink@2026).
3. Правая кнопка на странице, Просмотреть код (или Cmd+Option+I на маке).
4. Вкладка Network, фильтр Fetch/XHR.
5. Нажми Query на странице чтобы появился запрос.
6. Клик на строку device-sync-records, вкладка Headers.
7. Прокрути до Request Headers, найди строку Cookie.
8. Скопируй всё значение и вставь в поле выше.
""",

        # --- Смысл HTTP-кодов (core/status_meaning.py) ---
        "http_billing_200": "Успешно принято Billing",
        "http_billing_400": "Отклонено Billing (см. текст)",
        "http_401": "Сессия истекла",
        "http_billing_500": "Внутренняя ошибка 1С",
        "http_billing_502": "Billing недоступен",
        "http_equral_204": "Успешно (No Content)",
        "http_equral_400": "Отклонено e-Qural (проверь реестр)",
        "http_equral_500": "Ошибка сервера",
        "http_kazgas_200": "Успешно",
        "status_no_code": "нет кода",

        # --- Категории ошибок Billing (core/status_meaning.py) ---
        "err_dup": "Дубликат в 1С",
        "err_dup_desc": "Счётчик числится в 1С, хотя на MMS дубля нет. Разбирается на стороне Billing.",
        "err_point_busy": "Точка учёта занята",
        "err_point_busy_desc": "Старый счётчик не снят, точка занята. Нужно снятие в 1С.",
        "err_no_meter": "ПУ не найден в 1С",
        "err_no_meter_desc": "Счётчика нет в 1С по этому номеру.",
        "err_no_account": "ЛС не найден в 1С",
        "err_no_account_desc": "Лицевой счёт отсутствует в 1С.",
        "err_remove_fail": "Внутренняя ошибка 1С при снятии",
        "err_remove_fail_desc": "Сбой на стороне 1С при обработке снятия.",
        "err_other": "Прочее",

        # --- Колонки dl_device_sync ---
        "col_id": "ID",
        "col_device_no": "Счётчик (ПУ)",
        "col_platform_type": "Тип платформы",
        "col_status": "Статус",
        "col_response_status": "HTTP",
        "col_region_code": "Регион",
        "col_create_time": "Создано",
        "col_update_time": "Обновлено",
        "col_result_msg": "Сообщение",
        "col_push_count": "Кол-во пушей",
        "col_response_body": "Ответ",
        "col_request_body": "Запрос",
        "col_api_url": "API URL",

        # --- Страница 1: просмотр синхронизации ---
        "page1_title": "Просмотр синхронизации",
        "col_status_meaning": "Смысл статуса",
        "col_error_category": "Категория ошибки",

        # --- Страница 2: массовый репуш ---
        "page2_title": "Массовый репуш",
        "cookie_expander": "Настройки сессии (куки)",
        "no_cookie_warn": "MMS куки не заданы, репуш вернёт 401. Вставь куки в блоке выше.",
        "col_meaning_short": "смысл",
        "done_ok_fail": "Готово. OK={ok} FAIL={fail}",
        "download_log": "⬇ Скачать лог",
        "repush_running": "Идёт репуш, не трогайте страницу до завершения.",
        "processed_of": "Обработано {i} из {total}",
        "last_repush_header": "Результат последнего репуша",
        "btn_check_all": "Выделить все",
        "btn_uncheck_all": "Снять все",
        "btn_only_failed": "Только неуспешные",
        "col_repush_q": "Репуш?",
        "delay_label": "Задержка между запросами (сек)",
        "btn_repush_selected": "🚀 Репушнуть выбранные ({n})",
        "mode_repush_label": "Способ репуша",
        "mode_single_m": "Одиночный",
        "single_repush_header": "Одиночный репуш",
        "kind_label": "Что введено",
        "value_label": "Значение",
        "value_placeholder": "например 123456 или KZ00123456",
        "platform_for_id": "Тип операции для подбора id",
        "btn_repush": "🚀 Репушнуть",
        "id_must_be_number": "id должен быть числом.",
        "not_found_by_dev": "Не нашёл записей по device_no={dev} и типу {pt}.",
        "found_id_info": "Найден id={rid} (device_no={dev}, тип {pt}, HTTP {http}, дата {dt}).",
        "sending_repush": "Отправляю репуш...",
        "empty_response": "(пустой ответ)",
        "table_repush_header": "Подбор записей по фильтрам, выбор галочками",
        "file_repush_header": "Загрузка из файла",
        "file_step1": "**Шаг 1.** Загрузи Excel/CSV со столбцом `device_no` (или `id`).",
        "platform_for_file": "Тип операции для подбора id (если в файле только device_no)",
        "only_failed_label": "Только неуспешные (400/500) последние попытки",
        "loaded_rows": "Загружено строк: {n}. Колонки: {cols}",
        "file_has_ids": "В файле есть id, беру напрямую ({n}).",
        "matched_records": "Подобрано записей: {n}",
        "file_step2": "**Шаг 2.** Отметь галочками и запусти репуш.",

        # --- Страница 3: проверка в Billing ---
        "page3_title": "Проверка в Billing (1С)",
        "tab_single_check": "Одиночная проверка",
        "tab_bulk_check": "Массовая сверка",
        "billing_intro": "Что реально стоит на лицевом счёте в 1С.",
        "account_label": "Лицевой счёт (ЛС)",
        "nomer_label": "Счётчик (ПУ), опционально, для статуса",
        "btn_check": "Проверить",
        "on_account_info": "На ЛС стоит: **{pu}** ({model}, {maker})",
        "no_value": "нет",
        "no_pu_on_account": "На ЛС нет привязанного ПУ в 1С.",
        "crosscheck_intro": "Загрузи файл со столбцами `ЛС` (account) и `ПУ ожидаемый` (device_no). Сверю с фактическим ПУ в 1С.",
        "crosscheck_file": "Файл сверки",
        "ls_col_label": "Столбец ЛС",
        "pu_col_label": "Столбец ожидаемого ПУ",
        "delay_short": "Задержка (сек)",
        "btn_crosscheck": "Сверить",
        "verdict_match": "СОВПАДАЕТ",
        "verdict_mismatch": "НЕ СОВПАДАЕТ",
        "verdict_no_pu": "НЕТ ПУ НА ЛС",
        "col_ls": "ЛС",
        "col_expected": "Ожидали",
        "col_actual_1c": "Факт в 1С",
        "col_model": "Модель",
        "col_verdict": "Итог",
        "matched_n": "Совпало: {m} / {n}",
        "download_result": "⬇ Скачать результат",

        # --- Страница 4: статистика ---
        "page4_title": "Статистика синхронизации",
        "page4_caption": "Сводка по таблице dl_device_sync: запросы, успех (Billing 200, e-Qural 204), регионы, платформы, ошибки Billing.",
        "btn_build": "Построить",
        "stats_hint": "Задай период и нажми «Построить».",
        "no_data_period": "За выбранный период данных нет.",
        "metric_total_requests": "Всего запросов",
        "metric_ok": "Успешных",
        "metric_rate": "Процент успеха",
        "metric_billing_errors": "Ошибок Billing",
        "daily_header": "Динамика по дням",
        "requests_count_caption": "Количество запросов",
        "col_requests": "Запросы",
        "success_rate_caption": "Процент успеха (Billing 200, e-Qural 204), %",
        "by_region_header": "По регионам",
        "no_data": "Нет данных.",
        "no_region_code": "нет кода",
        "col_region": "Регион",
        "col_success_pct": "Успех, %",
        "col_total": "Всего",
        "col_ok": "Успешных",
        "by_platform_header": "По типу платформы",
        "no_platform_type": "нет типа",
        "top_errors_header": "Топ ошибок Billing по паттернам",
        "top_errors_caption": "Ошибки (не 200) по платформам {platforms}, сгруппированные по тексту ответа.",
        "no_billing_errors": "Ошибок Billing за период нет.",
        "col_category": "Категория",
        "col_count": "Количество",
        "col_share_pct": "Доля, %",
        "samples_expander": "Примеры сообщений по категориям",

        # --- Страница 5: проверка e-Qural ---
        "page5_title": "Проверка установки в e-Qural",
        "page5_caption": "Истина в базе mds: реально установлен = статус Installed и есть привязка к абоненту.",
        "col_device_no_full": "Счётчик (device_no)",
        "col_status_mds": "Статус mds",
        "col_really_installed": "Реально установлен",
        "col_region_kato": "Регион (КАТО)",
        "col_block_flag": "Флаг блокировки",
        "col_created": "Создан",
        "col_updated": "Обновлён",
        "col_equral_verdict": "Вердикт e-Qural",
        "verdict_installed": "Установлен в e-Qural",
        "verdict_awaiting": "Не прошёл: ждёт в реестре, физически не установлен",
        "verdict_no_consumer": "Проблема: установлен без привязки к абоненту",
        "verdict_deleted": "Удалён из e-Qural",
        "verdict_blocked": "Заблокирован в e-Qural",
        "verdict_absent": "Не прошёл: отсутствует в e-Qural",
        "summary_header": "Сводка",
        "metric_checked": "Всего проверено",
        "metric_failed": "Не прошло / проблемы",
        "breakdown_md": "**Разбивка не прошедших по причинам:**",
        "col_reason": "Причина",
        "no_data_show": "Нет данных для показа.",
        "mode_check_label": "Способ проверки",
        "mode_single_f": "Одиночная",
        "single_check_header": "Одиночная проверка",
        "device_placeholder": "например 0123456789",
        "btn_check_equral": "Проверить в e-Qural",
        "equral_query_error": "Ошибка запроса к e-Qural: {e}",
        "empty_input": "Пустой ввод.",
        "verdict_is": "Вердикт: {v}",
        "not_in_mds": "нет в mds",
        "label_consumer_link": "Привязка к абоненту",
        "label_account": "Лицевой счёт (ЛС)",
        "label_region": "Регион",
        "label_created": "Создан",
        "label_updated": "Обновлён",
        "val_present": "есть",
        "val_none": "нет",
        "no_kato": "нет КАТО",
        "table_check_header": "Подбор записей EQURAL по фильтрам, выбор галочками",
        "table_check_caption": "Отмеченные device_no проверяются в mds. response_status тут только для справки.",
        "col_check_q": "Проверить?",
        "btn_check_selected": "Проверить выбранные ({n})",
        "checking_spinner": "Проверяю в e-Qural...",
        "file_check_intro": "Загрузи Excel/CSV со столбцом `device_no`. Дубли и пробелы уберу сам.",
        "checking_one_request": "Проверяю в e-Qural одним запросом...",
        "checked_n": "Проверено device_no: {n}",
    },

    "en": {
        # --- Navigation (sidebar menu, app.py) ---
        "nav_home": "Home",
        "nav_sync": "Sync viewer",
        "nav_repush": "Bulk repush",
        "nav_billing": "Billing check",
        "nav_stats": "Statistics",
        "nav_equral": "e-Qural check",

        # --- Common ---
        "lang_label": "Язык / Language",
        "all_option": "All",
        "query_error": "Query error: {e}",
        "rows_found": "Rows found: {n}",
        "export_excel": "⬇ Export to Excel",
        "filter_region": "Region",
        "filter_platform": "Platform type",
        "filter_http": "HTTP status",
        "filter_device": "Meter (device_no)",
        "filter_date_from": "Date from",
        "filter_date_to": "Date to",
        "filter_limit": "Row limit",
        "btn_show": "Show",
        "btn_show_records": "Show records",
        "mode_table": "Select from table",
        "mode_file": "From file",
        "no_records": "No records found.",
        "checked_of": "Selected: {sel} of {total}",
        "col_type_short": "Type",
        "col_date_short": "Date",
        "no_dev_col": "Could not find a device_no / meter column in the file.",
        "unique_devices": "Unique device_no: {n}",
        "file_label": "File",
        "val_yes": "Yes",
        "val_no": "No",

        # --- Home (app.py) ---
        "app_caption": "Internal dashboard for MMS · Billing · e-Qural integration",
        "app_db_ok": "device_life DB: connected ({host})",
        "app_db_err": "DB: {msg}",
        "app_equral_no_creds": "e-Qural (mds): credentials not set",
        "app_equral_ok": "e-Qural DB (mds): connected ({host})",
        "app_equral_err": "e-Qural: {msg}",
        "app_cookie_set": "MMS cookie: set",
        "app_cookie_missing": "MMS cookie: not set (required for repush)",
        "app_billing_ok": "Billing: credentials set",
        "app_billing_missing": "Billing: credentials not set",
        "app_sections_md": """
    ### Sections (menu on the left):
    1. **Sync viewer**: dl_device_sync table with filters and export
    2. **Bulk repush**: list upload, automatic id lookup, run with a live log
    3. **Billing check**: meter and account status in 1C, expected vs actual comparison
    4. **Statistics**: dashboard over dl_device_sync (trends, regions, platforms, Billing errors)
    5. **e-Qural check**: actual installation in the mds DB (single, from table, from file)

    Connection settings: in the `.env` file (copy from `.env.example`).
    """,

        # --- Cookies (core/session.py) ---
        "sidebar_cookie_header": "MMS cookies",
        "cookie_set": "Cookies are set",
        "cookie_not_set": "Cookies are not set",
        "cookie_saved": "Cookies saved",
        "cookie_where": "Where to get it: DevTools, Network tab, Request Headers, the Cookie line.",
        "cookie_input_label": "Cookie string from DevTools",
        "cookie_save_btn": "Save cookies",
        "cookie_empty_warn": "The field is empty, paste the Cookie string.",
        "cookie_help_toggle": "How to get cookies",
        "cookie_help_steps": """
1. Open http://lifecycle-mgmt.ktga.kz:32068/ in a browser (GlobalProtect VPN on, hosts entry in place).
2. If you were logged out, log in (admin / eslink@2026).
3. Right-click the page, Inspect (or Cmd+Option+I on a Mac).
4. Network tab, Fetch/XHR filter.
5. Press Query on the page so a request appears.
6. Click the device-sync-records row, Headers tab.
7. Scroll to Request Headers, find the Cookie line.
8. Copy the whole value and paste it into the field above.
""",

        # --- HTTP code meanings (core/status_meaning.py) ---
        "http_billing_200": "Accepted by Billing",
        "http_billing_400": "Rejected by Billing (see message)",
        "http_401": "Session expired",
        "http_billing_500": "Internal 1C error",
        "http_billing_502": "Billing unavailable",
        "http_equral_204": "Success (No Content)",
        "http_equral_400": "Rejected by e-Qural (check the registry)",
        "http_equral_500": "Server error",
        "http_kazgas_200": "Success",
        "status_no_code": "no code",

        # --- Billing error categories (core/status_meaning.py) ---
        "err_dup": "Duplicate in 1C",
        "err_dup_desc": "The meter is registered in 1C although MMS has no duplicate. Handled on the Billing side.",
        "err_point_busy": "Metering point occupied",
        "err_point_busy_desc": "The old meter was not removed, the point is occupied. Removal in 1C is required.",
        "err_no_meter": "Meter not found in 1C",
        "err_no_meter_desc": "There is no meter with this number in 1C.",
        "err_no_account": "Account not found in 1C",
        "err_no_account_desc": "The personal account is missing in 1C.",
        "err_remove_fail": "Internal 1C error during removal",
        "err_remove_fail_desc": "A failure on the 1C side while processing the removal.",
        "err_other": "Other",

        # --- dl_device_sync columns ---
        "col_id": "ID",
        "col_device_no": "Meter (PU)",
        "col_platform_type": "Platform type",
        "col_status": "Status",
        "col_response_status": "HTTP",
        "col_region_code": "Region",
        "col_create_time": "Created",
        "col_update_time": "Updated",
        "col_result_msg": "Message",
        "col_push_count": "Push count",
        "col_response_body": "Response",
        "col_request_body": "Request",
        "col_api_url": "API URL",

        # --- Page 1: sync viewer ---
        "page1_title": "Sync viewer",
        "col_status_meaning": "Status meaning",
        "col_error_category": "Error category",

        # --- Page 2: bulk repush ---
        "page2_title": "Bulk repush",
        "cookie_expander": "Session settings (cookies)",
        "no_cookie_warn": "MMS cookies are not set, repush will return 401. Paste the cookies in the block above.",
        "col_meaning_short": "meaning",
        "done_ok_fail": "Done. OK={ok} FAIL={fail}",
        "download_log": "⬇ Download log",
        "repush_running": "Repush in progress, do not interact with the page until it finishes.",
        "processed_of": "Processed {i} of {total}",
        "last_repush_header": "Last repush result",
        "btn_check_all": "Select all",
        "btn_uncheck_all": "Clear all",
        "btn_only_failed": "Only failed",
        "col_repush_q": "Repush?",
        "delay_label": "Delay between requests (sec)",
        "btn_repush_selected": "🚀 Repush selected ({n})",
        "mode_repush_label": "Repush mode",
        "mode_single_m": "Single",
        "single_repush_header": "Single repush",
        "kind_label": "Input type",
        "value_label": "Value",
        "value_placeholder": "e.g. 123456 or KZ00123456",
        "platform_for_id": "Operation type for id lookup",
        "btn_repush": "🚀 Repush",
        "id_must_be_number": "id must be a number.",
        "not_found_by_dev": "No records found for device_no={dev} and type {pt}.",
        "found_id_info": "Found id={rid} (device_no={dev}, type {pt}, HTTP {http}, date {dt}).",
        "sending_repush": "Sending repush...",
        "empty_response": "(empty response)",
        "table_repush_header": "Filter records, select with checkboxes",
        "file_repush_header": "Upload from file",
        "file_step1": "**Step 1.** Upload an Excel/CSV file with a `device_no` (or `id`) column.",
        "platform_for_file": "Operation type for id lookup (if the file has only device_no)",
        "only_failed_label": "Only failed (400/500) latest attempts",
        "loaded_rows": "Rows loaded: {n}. Columns: {cols}",
        "file_has_ids": "The file has an id column, using it directly ({n}).",
        "matched_records": "Records matched: {n}",
        "file_step2": "**Step 2.** Tick the checkboxes and run the repush.",

        # --- Page 3: Billing check ---
        "page3_title": "Billing check (1C)",
        "tab_single_check": "Single check",
        "tab_bulk_check": "Bulk cross-check",
        "billing_intro": "What is actually installed on the personal account in 1C.",
        "account_label": "Personal account (LS)",
        "nomer_label": "Meter (PU), optional, for status",
        "btn_check": "Check",
        "on_account_info": "Installed on the account: **{pu}** ({model}, {maker})",
        "no_value": "none",
        "no_pu_on_account": "No meter is linked to this account in 1C.",
        "crosscheck_intro": "Upload a file with `LS` (account) and `expected PU` (device_no) columns. It will be compared with the actual meter in 1C.",
        "crosscheck_file": "Cross-check file",
        "ls_col_label": "Account column",
        "pu_col_label": "Expected meter column",
        "delay_short": "Delay (sec)",
        "btn_crosscheck": "Cross-check",
        "verdict_match": "MATCH",
        "verdict_mismatch": "MISMATCH",
        "verdict_no_pu": "NO METER ON ACCOUNT",
        "col_ls": "Account",
        "col_expected": "Expected",
        "col_actual_1c": "Actual in 1C",
        "col_model": "Model",
        "col_verdict": "Result",
        "matched_n": "Matched: {m} / {n}",
        "download_result": "⬇ Download result",

        # --- Page 4: statistics ---
        "page4_title": "Sync statistics",
        "page4_caption": "Summary over dl_device_sync: requests, success (Billing 200, e-Qural 204), regions, platforms, Billing errors.",
        "btn_build": "Build",
        "stats_hint": "Set the period and press \"Build\".",
        "no_data_period": "No data for the selected period.",
        "metric_total_requests": "Total requests",
        "metric_ok": "Successful",
        "metric_rate": "Success rate",
        "metric_billing_errors": "Billing errors",
        "daily_header": "Daily trend",
        "requests_count_caption": "Request count",
        "col_requests": "Requests",
        "success_rate_caption": "Success rate (Billing 200, e-Qural 204), %",
        "by_region_header": "By region",
        "no_data": "No data.",
        "no_region_code": "no code",
        "col_region": "Region",
        "col_success_pct": "Success, %",
        "col_total": "Total",
        "col_ok": "Successful",
        "by_platform_header": "By platform type",
        "no_platform_type": "no type",
        "top_errors_header": "Top Billing errors by pattern",
        "top_errors_caption": "Errors (non-200) for platforms {platforms}, grouped by response text.",
        "no_billing_errors": "No Billing errors for the period.",
        "col_category": "Category",
        "col_count": "Count",
        "col_share_pct": "Share, %",
        "samples_expander": "Sample messages by category",

        # --- Page 5: e-Qural check ---
        "page5_title": "e-Qural installation check",
        "page5_caption": "Source of truth is the mds database: really installed = status Installed and linked to a consumer.",
        "col_device_no_full": "Meter (device_no)",
        "col_status_mds": "mds status",
        "col_really_installed": "Really installed",
        "col_region_kato": "Region (KATO)",
        "col_block_flag": "Blocked flag",
        "col_created": "Created",
        "col_updated": "Updated",
        "col_equral_verdict": "e-Qural verdict",
        "verdict_installed": "Installed in e-Qural",
        "verdict_awaiting": "Failed: waiting in the registry, not physically installed",
        "verdict_no_consumer": "Problem: installed without a consumer link",
        "verdict_deleted": "Deleted from e-Qural",
        "verdict_blocked": "Blocked in e-Qural",
        "verdict_absent": "Failed: not present in e-Qural",
        "summary_header": "Summary",
        "metric_checked": "Total checked",
        "metric_failed": "Failed / problems",
        "breakdown_md": "**Breakdown of failures by reason:**",
        "col_reason": "Reason",
        "no_data_show": "No data to display.",
        "mode_check_label": "Check mode",
        "mode_single_f": "Single",
        "single_check_header": "Single check",
        "device_placeholder": "e.g. 0123456789",
        "btn_check_equral": "Check in e-Qural",
        "equral_query_error": "e-Qural query error: {e}",
        "empty_input": "Empty input.",
        "verdict_is": "Verdict: {v}",
        "not_in_mds": "not in mds",
        "label_consumer_link": "Consumer link",
        "label_account": "Personal account (LS)",
        "label_region": "Region",
        "label_created": "Created",
        "label_updated": "Updated",
        "val_present": "yes",
        "val_none": "none",
        "no_kato": "no KATO",
        "table_check_header": "Filter EQURAL records, select with checkboxes",
        "table_check_caption": "Selected device_no are checked in mds. response_status here is for reference only.",
        "col_check_q": "Check?",
        "btn_check_selected": "Check selected ({n})",
        "checking_spinner": "Checking in e-Qural...",
        "file_check_intro": "Upload an Excel/CSV file with a `device_no` column. Duplicates and spaces are cleaned automatically.",
        "checking_one_request": "Checking in e-Qural in a single query...",
        "checked_n": "Checked device_no: {n}",
    },
}

# Порядок и ключи колонок dl_device_sync для человекочитаемых заголовков.
SYNC_COLUMN_KEYS = {
    "id": "col_id",
    "device_no": "col_device_no",
    "platform_type": "col_platform_type",
    "status": "col_status",
    "response_status": "col_response_status",
    "region_code": "col_region_code",
    "create_time": "col_create_time",
    "update_time": "col_update_time",
    "result_msg": "col_result_msg",
    "push_count": "col_push_count",
    "response_body": "col_response_body",
    "request_body": "col_request_body",
    "api_url": "col_api_url",
}


def get_lang() -> str:
    """Текущий язык из session_state, по умолчанию русский."""
    try:
        lang = st.session_state.get("lang", DEFAULT_LANG)
    except Exception:
        return DEFAULT_LANG
    return lang if lang in TRANSLATIONS else DEFAULT_LANG


def t(key: str, **kwargs) -> str:
    """Перевод по ключу для текущего языка.

    Нет ключа в текущем языке: берём русский, нет и там: возвращаем сам ключ.
    kwargs подставляются через str.format (безопасно, при ошибке формата
    возвращается текст без подстановки).
    """
    text = TRANSLATIONS[get_lang()].get(key)
    if text is None:
        text = TRANSLATIONS[DEFAULT_LANG].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


def sync_columns() -> dict:
    """Словарь rename для колонок dl_device_sync на текущем языке."""
    return {field: t(key) for field, key in SYNC_COLUMN_KEYS.items()}
