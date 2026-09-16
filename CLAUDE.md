# Aqyl Console: контекст для Claude Code

Streamlit-пульт для интеграционной команды QGA/Goldcard. Работает локально через VPN.

## Архитектура
- `aqyl_console/app.py`: точка входа. Программная навигация: st.navigation + st.Page,
  заголовки меню из переводов (`t("nav_*")`), сайдбар (язык, куки) общий для всех страниц
- `aqyl_console/views/`: страницы (home, sync, repush, billing, stats, equral),
  порядок и заголовки задаются в app.py, имена файлов в меню не участвуют
- `aqyl_console/core/`: логика:
  - `config.py`: чтение .env, справочники (регионы, русские названия колонок)
  - `db.py`: SQLAlchemy + pymysql к MySQL `device_life`, expanding IN для tuple-параметров
  - `mms.py`: клиент репуша `/api/device-sync-records/{id}/repush`
  - `billing.py`: сервисы 1С (`mmsclientdata`, `mmscheckmeterstatus`)
  - `i18n.py`: переводы RU/EN, `t(key)` читает язык из st.session_state["lang"]
  - `session.py`: язык и MMS-куки в фиксированных ключах session_state
    ("lang", "mms_cookie"), виджеты живут под своими ключами и синхронизируются
    через on_change/посев, поэтому значения переживают переход между страницами.
    `get_mms_cookie()` берёт куки из UI, иначе из `config.MMS_COOKIE` (.env).
    Поле ввода: expander на странице репуша и поле в сайдбаре.

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
