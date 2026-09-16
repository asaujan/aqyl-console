"""Проверка установки счётчиков в e-Qural (БД mds, PostgreSQL).

Доменная логика выверена на реальной БД, см. CLAUDE.md:
- device_no = BTRIM("DeviceId") в public."MeteringDevices" (SerialNumber там NULL).
- DeviceId не уникален, берём свежую запись через DISTINCT ON по DateUpdate.
- Реально установлен: IsDeleted = false AND MeteringDeviceStatus = 0 AND
  ConsumerId IS NOT NULL.
- IsBlocked это отдельный ручной флаг, в критерий установки НЕ входит.
"""
import pandas as pd

from aqyl_console.core import db

# Расшифровка MeteringDeviceStatus
STATUS_NAMES = {0: "Installed", 1: "Deleted", 2: "Awaiting", 3: "Blocked"}

# Выверенный на реальной БД запрос. device_list передаётся питоновским списком
# строк через параметр device_list (psycopg2 стиль %(name)s, ANY для IN-списка).
LOOKUP_SQL = """
SELECT DISTINCT ON (BTRIM(md."DeviceId"))
  BTRIM(md."DeviceId")              AS device_no,
  md."MeteringDeviceStatus"         AS status_code,
  CASE md."MeteringDeviceStatus"
    WHEN 0 THEN 'Installed'
    WHEN 1 THEN 'Deleted'
    WHEN 2 THEN 'Awaiting'
    WHEN 3 THEN 'Blocked'
  END                                AS status_name,
  (md."ConsumerId" IS NOT NULL)      AS has_consumer,
  (md."MeteringDeviceStatus" = 0
     AND md."ConsumerId" IS NOT NULL) AS really_installed,
  md."IsBlocked"                      AS is_blocked_flag,
  cons."PersonalAccount"             AS personal_account,
  reg."Code"                          AS region_kato,
  reg."NameRu"                        AS region_name,
  to_char(md."DateCreate" AT TIME ZONE 'UTC','YYYY-MM-DD HH24:MI:SS') AS date_create,
  to_char(md."DateUpdate" AT TIME ZONE 'UTC','YYYY-MM-DD HH24:MI:SS') AS date_update
FROM "MeteringDevices" md
LEFT JOIN "Consumers" cons
  ON cons."Id" = md."ConsumerId" AND cons."IsDeleted" = false
LEFT JOIN "DicRegions" reg
  ON reg."Id" = md."RegionId" AND reg."IsDeleted" = false
WHERE md."IsDeleted" = false
  AND BTRIM(md."DeviceId") = ANY(%(device_list)s)
ORDER BY BTRIM(md."DeviceId"), md."DateUpdate" DESC NULLS LAST, md."Id";
"""

# Тексты вердиктов e-Qural (на основе данных mds, не response_status).
V_INSTALLED = "Установлен в e-Qural"
V_AWAITING = "Не прошёл: ждёт в реестре, физически не установлен"
V_NO_CONSUMER = "Проблема: установлен без привязки к абоненту"
V_DELETED = "Удалён из e-Qural"
V_BLOCKED = "Заблокирован в e-Qural"
V_ABSENT = "Не прошёл: отсутствует в e-Qural"

# Цвет вердикта для UI: green / yellow / red
VERDICT_COLOR = {
    V_INSTALLED: "green",
    V_NO_CONSUMER: "yellow",
    V_AWAITING: "red",
    V_DELETED: "red",
    V_BLOCKED: "red",
    V_ABSENT: "red",
}


def lookup(device_list) -> pd.DataFrame:
    """Возвращает свежие записи mds по списку device_no.

    device_list: список/кортеж строк. Пустой ввод даёт пустой DataFrame.
    """
    devices = [str(d).strip() for d in device_list if str(d).strip()]
    if not devices:
        return pd.DataFrame()
    return db.run_equral_query(LOOKUP_SQL, {"device_list": devices})


def verdict_from_row(row) -> str:
    """Вердикт e-Qural по одной строке результата mds."""
    status = row.get("status_code")
    has_consumer = bool(row.get("has_consumer"))
    if pd.isna(status):
        return V_ABSENT
    status = int(status)
    if status == 0:
        return V_INSTALLED if has_consumer else V_NO_CONSUMER
    if status == 2:
        return V_AWAITING
    if status == 1:
        return V_DELETED
    if status == 3:
        return V_BLOCKED
    return V_ABSENT


def verdict_absent() -> str:
    """Вердикт для device_no, не найденного в mds."""
    return V_ABSENT


def check_devices(device_list) -> pd.DataFrame:
    """Массовая проверка: сверяет весь список с mds и проставляет вердикт.

    На вход список device_no (может содержать дубли и пробелы). На выходе
    строка на каждый уникальный device_no из входа, найденные обогащены
    данными mds, ненайденные помечены вердиктом "отсутствует в e-Qural".
    """
    wanted = []
    seen = set()
    for d in device_list:
        s = str(d).strip()
        if s and s not in seen:
            seen.add(s)
            wanted.append(s)
    if not wanted:
        return pd.DataFrame()

    found = lookup(wanted)
    found_map = {}
    if not found.empty:
        found_map = {str(r["device_no"]).strip(): r for _, r in found.iterrows()}

    rows = []
    for dev in wanted:
        if dev in found_map:
            r = found_map[dev].to_dict()
            r["Вердикт e-Qural"] = verdict_from_row(found_map[dev])
            rows.append(r)
        else:
            rows.append({
                "device_no": dev,
                "status_code": None,
                "status_name": None,
                "has_consumer": None,
                "really_installed": None,
                "is_blocked_flag": None,
                "personal_account": None,
                "region_kato": None,
                "region_name": None,
                "date_create": None,
                "date_update": None,
                "Вердикт e-Qural": verdict_absent(),
            })
    return pd.DataFrame(rows)
