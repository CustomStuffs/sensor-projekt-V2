"""POST /api/time — sync RTC before each upload."""

import json
import urequests
import time
import machine


def sync(server_url, device_id, uptime_ms, timeout_s=10):
    """
    POST /api/time, set RTC from response, return interval_s from config.
    Returns None on failure (caller should proceed with stale time).
    """
    url = server_url.rstrip("/") + "/api/time"
    payload = json.dumps({"device_id": device_id, "uptime_ms": uptime_ms})
    try:
        resp = urequests.post(url, data=payload,
                              headers={"Content-Type": "application/json"},
                              timeout=timeout_s)
        if resp.status_code != 200:
            resp.close()
            return None
        data = resp.json()
        resp.close()

        unix_ts = data.get("unix_ts")
        if unix_ts:
            t = time.gmtime(unix_ts)
            machine.RTC().datetime((t[0], t[1], t[2], t[6], t[3], t[4], t[5], 0))

        return data.get("config", {})
    except Exception as e:
        print("time_sync error:", e)
        return None
