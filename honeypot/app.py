import socket
import threading
import json
import datetime

# Log file inside mounted volume
LOG_FILE = "/logs/redis.log"

def log_event(event, ip=None, cmd=None):
    entry = {
        "event": event,
        "time": datetime.datetime.utcnow().isoformat() + "Z"
    }
    if ip:
        entry["ip"] = ip
    if cmd:
        # preserve your original safe formatting
        safe_cmd = cmd.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r")
        entry["cmd"] = safe_cmd

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


# --- FAKE REDIS DATA + RESP HELPERS ---
redis_db = {
    "config:secret": '{"api_key":"sk_test_1a2b","smtp_pass":"TXlTZXN0"}',
    "user:1001": '{"name":"alice","role":"admin"}',
    "ssh:keys": "ssh-ed25519 AAAAC3Nza...",
    "session:3fa2ee": "user=1001;expires=1700000000"
}

fake_info = """# Server
redis_version:7.0.0
redis_mode:standalone
os:Linux 5.15.0 x86_64
uptime_in_days:1
"""

def resp_bulk(s):
    return f"${len(s)}\r\n{s}\r\n".encode()

def resp_array(items):
    resp = f"*{len(items)}\r\n"
    for i in items:
        resp += f"${len(i)}\r\n{i}\r\n"
    return resp.encode()

def parse_resp(buf: bytes):
    """Parse RESP packets (redis-cli)"""
    lines = buf.split(b"\r\n")
    if not lines[0].startswith(b"*"):
        return []

    num = int(lines[0][1:])
    items = []
    idx = 1

    for _ in range(num):
        if idx >= len(lines) or not lines[idx].startswith(b"$"):
            return []
        strlen = int(lines[idx][1:])
        val = lines[idx + 1][:strlen].decode(errors="ignore")
        items.append(val)
        idx += 2

    return items


# --- CONNECTION HANDLER ---
def handle(conn, addr):
    ip = addr[0]
    log_event("connect", ip=ip)

    while True:
        raw = conn.recv(4096)
        if not raw:
            break

        # Log the EXACT RESP packet the attacker sent
        log_event("command", ip=ip, cmd=raw.decode(errors="ignore"))

        cmd_list = parse_resp(raw)
        if not cmd_list:
            conn.send(b"+OK\r\n")
            continue

        op = cmd_list[0].upper()

        # --- Enhanced behavior from your teammate ---

        # INFO
        if op == "INFO":
            conn.send(resp_bulk(fake_info))
            continue

        # GET key
        if op == "GET" and len(cmd_list) >= 2:
            key = cmd_list[1]
            val = redis_db.get(key, "")
            conn.send(resp_bulk(val))
            continue

        # KEYS *
        if op == "KEYS":
            keys = list(redis_db.keys())
            conn.send(resp_array(keys))
            continue

        # SET key value
        if op == "SET" and len(cmd_list) >= 3:
            redis_db[cmd_list[1]] = cmd_list[2]
            conn.send(b"+OK\r\n")
            continue

        # DEFAULT fallback
        conn.send(b"+OK\r\n")

    conn.close()


# --- MAIN ---
def main():
    log_event("started", cmd="Redis honeypot listening on 6379")

    s = socket.socket()
    s.bind(("0.0.0.0", 6379))
    s.listen(200)

    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
