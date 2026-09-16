"""Billing (RCKU 1C) check services."""
import base64
import requests
from aqyl_console.core import config

_AUTH = "Basic " + base64.b64encode(
    f"{config.BILLING_USER}:{config.BILLING_PASSWORD}".encode()
).decode()


def _get(path: str, timeout: int = 15) -> tuple[int, str]:
    url = f"{config.BILLING_BASE}{path}"
    try:
        r = requests.get(url, headers={"Authorization": _AUTH}, timeout=timeout)
        return r.status_code, r.text
    except Exception as e:
        return 0, f"ERR: {type(e).__name__}: {e}"


def client_data(account: str):
    """GET /mmsclientdata?account=, what meter sits on this account in 1C."""
    return _get(f"/mmsclientdata?account={account}")


def check_meter_status(account: str, nomer: str):
    """GET /mmscheckmeterstatus?account=&nomerPU=, meter status in 1C."""
    return _get(f"/mmscheckmeterstatus?account={account}&nomerPU={nomer}")
