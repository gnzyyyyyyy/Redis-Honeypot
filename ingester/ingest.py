import time
import json
import requests

LOGFILE = "/logs/redis.log"
CLICKHOUSE_URL = "http://default:mypassword123@clickhouse:8123"
TABLE = "honeypot.redis_events"

def follow(file):
    file.seek(0, 2)
    while True:
        line = file.readline()
        if not line:
            time.sleep(0.2)
            continue
        yield line

def clean_record(rec):
    rec.setdefault("ip", "")
    rec.setdefault("cmd", "")

    # Convert time to ClickHouse compatible format
    if rec.get("time"):
        rec["time"] = rec["time"].replace("T", " ").replace("Z", "")

    # Escape command safely
    rec["cmd"] = rec["cmd"].replace("\r", "\\r").replace("\n", "\\n")

    return rec

def send_to_clickhouse(rec):
    rec = clean_record(rec)
    data = json.dumps(rec)
    query = f"INSERT INTO {TABLE} FORMAT JSONEachRow"
    r = requests.post(CLICKHOUSE_URL, params={"query": query}, data=data)
    print("ClickHouse:", r.text)

def main():
    print("Ingester started, waiting for logs...")
    with open(LOGFILE) as f:
        for line in follow(f):
            try:
                rec = json.loads(line)
                send_to_clickhouse(rec)
            except Exception as e:
                print("Error:", e)

if __name__ == "__main__":
    main()
