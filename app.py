#!/usr/bin/env python3
from flask import Flask, render_template, jsonify, request
import subprocess, time, os

app = Flask(__name__)

# Server-Konfiguration
SERVERS = {
    "server1": {
        "name": "1.21.10",
        "service": "mc-fabric-12110.service",
        "log_file": "/home/leon/mc-server/fabric-1.21.10/logs/latest.log",
        "console_dir": "/home/leon/mc-server/fabric-1.21.10"
    },
    "server2": {
        "name": "1.20.4",
        "service": "mc-fabric-1204.service",
        "log_file": "/home/leon/mc-server/fabric-1.20.4/logs/latest.log",
        "console_dir": "/home/leon/mc-server/fabric-1.20.4"
    }
}

# ===== Helper =====
def systemctl(cmd, service):
    try:
        result = subprocess.run(["systemctl", "--user", cmd, service], capture_output=True, text=True)
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)

def is_active(service):
    result = subprocess.run(["systemctl", "--user", "is-active", service], capture_output=True, text=True)
    return result.stdout.strip() == "active"

# ===== Routes =====
@app.route("/")
def index():
    return render_template("index.html", servers=SERVERS)

@app.route("/<server>/status")
def status(server):
    svc = SERVERS[server]["service"]
    running = is_active(svc)
    return jsonify({"running": running})

@app.route("/<server>/start")
def start(server):
    svc = SERVERS[server]["service"]
    output = systemctl("start", svc)
    time.sleep(2)
    return jsonify({"output": output, "running": is_active(svc)})

@app.route("/<server>/stop")
def stop(server):
    svc = SERVERS[server]["service"]
    output = systemctl("stop", svc)
    time.sleep(2)
    return jsonify({"output": output, "running": is_active(svc)})

@app.route("/<server>/restart")
def restart(server):
    svc = SERVERS[server]["service"]
    output = systemctl("restart", svc)
    time.sleep(2)
    return jsonify({"output": output, "running": is_active(svc)})

@app.route("/<server>/backup")
def backup(server):
    backup_script = os.path.join(SERVERS[server]["console_dir"], "backup.sh")
    try:
        result = subprocess.run(["bash", backup_script], capture_output=True, text=True)
        return jsonify({"output": result.stdout + result.stderr})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/<server>/logs")
def logs(server):
    log_file = SERVERS[server]["log_file"]
    if not os.path.exists(log_file):
        return "Log file not found", 404
    with open(log_file, "r", errors="ignore") as f:
        content = f.read()
    return content, 200, {"Content-Type": "text/plain; charset=utf-8"}

@app.route("/<server>/console", methods=["POST"])
def console(server):
    data = request.get_json()
    cmd = data.get("command")
    if not cmd:
        return jsonify({"status": "error", "msg": "No command provided"}), 400
    dir_ = SERVERS[server]["console_dir"]
    # Sende Kommando an die laufende Java-Instanz über screen (wenn vorhanden)
    screen_name = SERVERS[server]["service"].replace(".service","")
    subprocess.run(f'screen -S {screen_name} -X stuff "{cmd}\n"', shell=True, cwd=dir_)
    return jsonify({"status": "success", "command": cmd})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
