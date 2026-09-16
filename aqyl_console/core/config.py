"""Central config loaded from .env."""
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "10.20.38.49")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "device_life")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "device_life")

# e-Qural (PostgreSQL, mds). Роль read-only bts_digital_ro, юзер и пароль
# впишет пользователь сам в .env. ВАЖНО: база mds, не postgres (там пусто).
EQURAL_DB_HOST = os.getenv("EQURAL_DB_HOST", "10.20.43.58")
EQURAL_DB_PORT = int(os.getenv("EQURAL_DB_PORT", "5432"))
EQURAL_DB_NAME = os.getenv("EQURAL_DB_NAME", "mds")
EQURAL_DB_USER = os.getenv("EQURAL_DB_USER", "")
EQURAL_DB_PASSWORD = os.getenv("EQURAL_DB_PASSWORD", "")

MMS_BASE = os.getenv("MMS_BASE", "http://lifecycle-mgmt.ktga.kz:32068")
# Значение по умолчанию. В UI куки можно переопределить через session_state
# (см. core/session.get_mms_cookie).
MMS_COOKIE = os.getenv("MMS_COOKIE", "")

BILLING_BASE = os.getenv("BILLING_BASE", "http://su.rcku.kz:82")
BILLING_USER = os.getenv("BILLING_USER", "mms_integration")
BILLING_PASSWORD = os.getenv("BILLING_PASSWORD", "")

# Region codes
REGIONS = {
    15: "Актобе",
    19: "Талдыкорган",
    23: "Атырау",
    27: "Орал",
    31: "Тараз",
    35: "Караганда",
    39: "Костанай",
    43: "Кызылорда",
    47: "Актау",
    61: "Туркестан",
    63: "Оскемен",
    71: "Астана",
    79: "Шымкент",
}

# Человекочитаемые названия колонок dl_device_sync переехали в core/i18n.py
# (ключи col_*, функция sync_columns), чтобы следовать за языком интерфейса.
