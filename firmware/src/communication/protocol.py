"""Build JSON payloads and POST/GET to the server with retry."""

import json
import urequests
import time


def _post(url, payload, timeout_s, retries, retry_delay_s):
    for attempt in range(retries):
        try:
            resp = urequests.post(url, data=payload,
                                  headers={"Content-Type": "application/json"},
                                  timeout=timeout_s)
            code = resp.status_code
            body = resp.json()
            resp.close()
            return code, body
        except Exception as e:
            print(f"POST attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(retry_delay_s)
    return None, None


def _get(url, timeout_s, retries, retry_delay_s):
    for attempt in range(retries):
        try:
            resp = urequests.get(url, timeout=timeout_s)
            code = resp.status_code
            body = resp.json()
            resp.close()
            return code, body
        except Exception as e:
            print(f"GET attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(retry_delay_s)
    return None, None


def upload_readings(server_url, device_id, fw_version, vsys_mv, readings, cfg):
    """
    POST /api/readings. readings is a list of dicts.
    Returns number of stored rows on success, None on failure.
    """
    payload = json.dumps({
        "device_id": device_id,
        "fw": fw_version,
        "vbus_mv": vsys_mv,
        "readings": readings,
    })
    url = server_url.rstrip("/") + "/api/readings"
    code, body = _post(url, payload, cfg["timeout_s"], cfg["retry_count"], cfg["retry_delay_s"])
    if code == 200 and body and body.get("ok"):
        return body.get("stored", 0)
    return None


def poll_commands(server_url, device_id, cfg):
    """
    GET /api/commands?device_id=...
    Returns list of command dicts, or empty list on failure.
    """
    url = server_url.rstrip("/") + f"/api/commands?device_id={device_id}"
    code, body = _get(url, cfg["timeout_s"], cfg["retry_count"], cfg["retry_delay_s"])
    if code == 200 and body:
        return body.get("commands", [])
    return []


def ack_command(server_url, cmd_id, cfg):
    """POST /api/commands/<id>/ack."""
    url = server_url.rstrip("/") + f"/api/commands/{cmd_id}/ack"
    payload = json.dumps({})
    _post(url, payload, cfg["timeout_s"], cfg["retry_count"], cfg["retry_delay_s"])


def vsys_mv():
    """Read VSYS voltage via Pico W ADC3 (internal 3:1 voltage divider)."""
    try:
        from machine import ADC
        adc = ADC(29)  # GPIO29 = VSYS/3 divider on Pico W
        v = adc.read_u16() * 3.3 / 65535 * 3
        return round(v * 1000)
    except Exception:
        return None
