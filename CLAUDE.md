# Aqyl Console: контекст для Claude Code

Streamlit-пульт для интеграционной команды QGA/Goldcard. Работает локально через VPN.

## Архитектура
- `aqyl_console/app.py`: главная страница (статус подключений)
- `aqyl_console/pages/`: вкладки Streamlit (нумерованные файлы = порядок в меню)
- `aqyl_console/core/`: логика:
  - `config.py`: чтение .env, справочники (регионы, русские названия колонок)
  - `db.py`: SQLAlchemy + pymysql к MySQL `device_life`, expanding IN для tuple-параметров
  - `mms.py`: клиент репуша `/api/device-sync-records/{id}/repush`
  - `billing.py`: сервисы 1С (`mmsclientdata`, `mmscheckmeterstatus`)
  - `session.py`: MMS-куки в session_state. `get_mms_cookie()` берёт куки из UI,
    иначе из `config.MMS_COOKIE` (.env). Поле ввода: expander на странице репуша
    и поле в сайдбаре (`render_cookie_sidebar`).

## Ключевые факты домена
- Таблица `dl_device_sync`: лог запросов MMS→Billing/e-Qural. Поля: id, device_no,
  platform_type (BILING-INSTALL/BILING-REMOVE/EQURAL/KAZGAS_IOT), response_status,
  response_body (msg), request_body (JSON с account), region_code (43/61/79), create_time.
- Репуш повторно отправляет запрос по внутреннему id. Cookie сессии протухает, тогда 401.
- Billing `mmsclientdata?account=` возвращает текущий ПУ на ЛС в 1С.
- Регионы: 43=Кызылорда, 61=Туркестан, 79=Шымкент.

### Как получить куки (при 401)
1. Открой http://lifecycle-mgmt.ktga.kz:32068/ в браузере (VPN GlobalProtect включён, hosts прописан).
2. Если разлогинило, войди (admin / eslink@2026).
3. Правая кнопка на странице, Просмотреть код (или Cmd+Option+I на маке).
4. Вкладка Network, фильтр Fetch/XHR.
5. Нажми Query на странице чтобы появился запрос.
6. Клик на строку device-sync-records, вкладка Headers.
7. Прокрути до Request Headers, найди строку Cookie.
8. Скопируй всё значение и вставь в поле в UI (сайдбар или страница репуша) либо в `.env`.

## Стиль
- Русский UI. Без em-dash в текстах, только запятые/двоеточия/скобки.
- Rate limiting на репуш обязателен (delay между запросами), чтобы не положить Billing.

## Backlog (см. README)
Дашборд статистики, категоризатор ошибок, ручное снятие через /mmsremoval,
проверка e-Qural, таймлайн по ПУ, Telegram-алерты, Redis-кэш.
