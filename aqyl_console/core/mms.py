"""MMS Backend Management repush client."""
import requests
from aqyl_console.core import config, session


def repush(record_id: int, timeout: int = 30) -> tuple[int, str]:
    """POST /api/device-sync-records/{id}/repush. Returns (http_status, body)."""
    url = f"{config.MMS_BASE}/api/device-sync-records/{record_id}/repush"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Length": "0",
        "Cookie": session.get_mms_cookie(),
        "Origin": config.MMS_BASE,
        "Referer": f"{config.MMS_BASE}/device-sync",
        "User-Agent": "aqyl-console",
    }
    try:
        r = requests.post(url, headers=headers, timeout=timeout)
        return r.status_code, r.text[:300]
    except Exception as e:
        return 0, f"ERR: {type(e).__name__}: {e}"
