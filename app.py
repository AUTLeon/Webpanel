#!/usr/bin/env python3
from flask import Flask, render_template, jsonify, request
import subprocess
import os
import shlex

app = Flask(__name__)

# === Pfade ===
FABRIC_DIR = os.path.expanduser("~/mc-server/fabric-1.21.10")
START_SCRIPT = os.path.join(FABRIC_DIR, "start.sh")
STOP_SCRIPT = os.path.join(FABRIC_DIR, "stop.sh")
BACKUP_SCRIPT = os.path.join(FABRIC_DIR, "backup.sh")
SERVER_PID_FILE = os.path.join(FABRIC_DIR, "server.pid")
SERVER_LOG = os.path.join(FABRIC_DIR, "server.log")

# Panel-screen (nicht als Minecraft-Server interpretieren)
PANEL_SCREEN_NAME = "mc-panel"
LIKELY_SERVER_KEYWORDS = ("mc-server", "minecraft", "fabric", "paper", "server")


# === Helferfunktionen ===
def run(cmd, wait=True):
    if wait:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True)
    else:
        return subprocess.Popen(cmd, shell=True)


def list_screens():
    res = run("screen -ls")
    return (res.stdout or "") + (res.stderr or "")


def find_screens():
    out = list_screens()
    screens = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        for p in parts:
            if "." in p and p.split(".", 1)[0].isdigit():
                name = p.split(".", 1)[1]
                screens.append(name)
    return screens


def detect_server_screen():
    screens = find_screens()
    for s in screens:
        if s == PANEL_SCREEN_NAME:
            continue
        lname = s.lower()
        for kw in LIKELY_SERVER_KEYWORDS:
            if kw in lname:
                return s
    non_panel = [s for s in screens if s != PANEL_SCREEN_NAME]
    if len(non_panel) == 1:
        return non_panel[0]
    return None


def is_server_running():
    # PID check
    if os.path.exists(SERVER_PID_FILE):
        try:
            with open(SERVER_PID_FILE, "r") as f:
                pid = f.read().strip()
            if pid.isdigit():
                res = run(f"ps -p {pid} -o comm=", wait=True)
                if res.returncode == 0 and res.stdout.strip():
                    return True
        except Exception:
            pass

    # Java process check
    res = run("pgrep -af java", wait=True)
    for proc in (res.stdout or "").splitlines():
        if any(key in proc.lower() for key in ("fabric", "minecraft", "server", "paper")):
            return True

    # Screen check
    screens = find_screens()
    for s in screens:
        if s != PANEL_SCREEN_NAME and any(kw in s.lower() for kw in LIKELY_SERVER_KEYWORDS):
            return True

    return False


# === Flask-Routen ===
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/status")
def status():
    try:
        running = is_server_running()
        detected = detect_server_screen()
        return jsonify(running=running, detected_screen=detected)
    except Exception as e:
        return jsonify(running=False, error=str(e)), 500


@app.route("/start")
def start():
    if os.path.exists(START_SCRIPT) and os.access(START_SCRIPT, os.X_OK):
        run(f"bash {shlex.quote(START_SCRIPT)}")
        return "Starte Server..."
    else:
        return "Start-Skript fehlt oder nicht ausführbar!", 500


@app.route("/stop")
def stop():
    if os.path.exists(STOP_SCRIPT) and os.access(STOP_SCRIPT, os.X_OK):
        run(f"bash {shlex.quote(STOP_SCRIPT)}")
        return "Stoppe Server..."
    else:
        server_screen = detect_server_screen()
        if server_screen:
            run(f'screen -S {shlex.quote(server_screen)} -X stuff "stop\\n"')
            return f"Stoppe Server (screen: {server_screen})..."
        else:
            return "Kein Server-Screen gefunden und kein stop.sh vorhanden!", 500


@app.route("/backup")
def backup():
    if os.path.exists(BACKUP_SCRIPT) and os.access(BACKUP_SCRIPT, os.X_OK):
        run(f"bash {shlex.quote(BACKUP_SCRIPT)}")
        return "Backup wird gestartet..."
    else:
        return "Kein Backup-Skript gefunden!", 404


@app.route("/screens")
def screens():
    try:
        return jsonify(screens=find_screens())
    except Exception as e:
        return jsonify(screens=[], error=str(e)), 500


@app.route("/logs")
def logs():
    n = request.args.get("lines", "200")
    try:
        n_int = int(n)
    except ValueError:
        n_int = 200
    if os.path.exists(SERVER_LOG):
        try:
            with open(SERVER_LOG, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                return "".join(lines[-n_int:]), 200, {"Content-Type": "text/plain; charset=utf-8"}
        except Exception as e:
            return f"Fehler beim Lesen der Logdatei: {e}", 500
    else:
        return "server.log nicht gefunden!", 404


# === 🟦 NEUE KONSOLE: HTML-Seite ===
@app.route("/console")
def console():
    return render_template("console.html")


# === 🟦 NEUE KONSOLE: Befehl senden ===
@app.route("/console/send", methods=["POST"])
def console_send():
    cmd = request.json.get("cmd")
    screen = detect_server_screen()

    if not screen:
        return jsonify({"status": "error", "msg": "Kein Server-Screen gefunden"}), 400

    if cmd:
        run(f'screen -S {shlex.quote(screen)} -X stuff "{cmd}\\n"')
        return jsonify({"status": "ok", "sent": cmd})

    return jsonify({"status": "error", "msg": "Kein Command"}), 400


# === 🟦 NEUE KONSOLE: Live-Logs ===
@app.route("/console/log")
def console_log():
    try:
        if os.path.exists(SERVER_LOG):
            with open(SERVER_LOG, "r", errors="ignore") as f:
                lines = f.readlines()[-200:]
            return jsonify({"log": "".join(lines)})
        else:
            return jsonify({"log": "server.log nicht gefunden!"})
    except Exception as e:
        return jsonify({"log": f"Fehler: {e}"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
