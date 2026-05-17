import requests
import json
import os
import sys
from datetime import datetime, timezone

URL = os.environ.get("MONITOR_URL", "").strip()
DATA_FILE = "data/checks.json"
MAX_RECORDS = 1440  # 10 dias × 24h × 6 checks/h

if not URL:
    print("❌ Variável MONITOR_URL não definida. Configure em Settings > Variables.")
    sys.exit(1)


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"url": URL, "checks": []}


def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, separators=(",", ":"))


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HealthMonitor/1.0)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

def check_health(url):
    try:
        start = datetime.now()
        response = requests.get(url, timeout=30, allow_redirects=True, headers=HEADERS)
        elapsed_ms = round((datetime.now() - start).total_seconds() * 1000)
        return {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": response.status_code,
            "ms": elapsed_ms,
            "ok": response.status_code < 400,
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": 0,
            "ms": 0,
            "ok": False,
            "err": "connection_error",
        }
    except requests.exceptions.Timeout:
        return {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": 0,
            "ms": 30000,
            "ok": False,
            "err": "timeout",
        }
    except Exception as e:
        return {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": 0,
            "ms": 0,
            "ok": False,
            "err": str(e)[:80],
        }


def main():
    data = load_data()
    data["url"] = URL

    check = check_health(URL)
    data["checks"].append(check)
    data["checks"] = data["checks"][-MAX_RECORDS:]
    data["updated"] = check["ts"]

    save_data(data)

    icon = "✅" if check["ok"] else "❌"
    print(f"{icon} {check['ts']} | HTTP {check['status']} | {check['ms']}ms | {URL}")


if __name__ == "__main__":
    main()