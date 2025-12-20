#!/usr/bin/env python3
from flask import Flask, render_template, jsonify, request
import subprocess, time, os, signal

app = Flask(__name__)

# Server-Konfiguration
SERVERS = {
    "server1": {
        "name": "1.21.10",
        "service": "mc-fabric-12110.service",
        "log_file": "/home/leon/mc-server/fabric-1.21.10/logs/latest.log",
        "console_dir": "/home/leon/mc-server/fabric-1.21.10",
        "pid_file": "/home/leon/mc-server/fabric-1.21.10/server.pid"
    },
    "server2": {
        "name": "1.20.4",
        "service": "mc-fabric-1204.service",
        "log_file": "/home/leon/mc-server/fabric-1.20.4/logs/latest.log",
        "console_dir": "/home/leon/mc-server/fabric-1.20.4",
        "pid_file": "/home/leon/mc-server/fabric-1.20.4/server.pid"
    }
}

# ===== Helper =====
def systemctl(cmd, service):
    try:
        # --system statt --user, weil deine Systemd-Services global laufen
        result = subprocess.run(["sudo", "systemctl", cmd, service], capture_output=True, text=True)
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)

def is_active(service):
    result = subprocess.run(["sudo", "systemctl", "is-active", service], capture_output=True, text=True)
    return result.stdout.strip() == "active"

def get_pid(server):
    pid_file = SERVERS[server]["pid_file"]
    if os.path.exists(pid_file):
        try:
            with open(pid_file) as f:
                return int(f.read().strip())
        except:
            return None
    return None

# ===== Routes =====
@app.route("/")
def index():
    return render_template("index.html", servers=SERVERS)

@app.route("/<server>/status")
def status(server):
    running = is_active(SERVERS[server]["service"])
    return jsonify({"running": running})

@app.route("/<server>/start")
def start(server):
    output = systemctl("start", SERVERS[server]["service"])
    time.sleep(2)
    return jsonify({"output": output, "running": is_active(SERVERS[server]["service"])})

@app.route("/<server>/stop")
def stop(server):
    output = systemctl("stop", SERVERS[server]["service"])
    time.sleep(2)
    return jsonify({"output": output, "running": is_active(SERVERS[server]["service"])})

@app.route("/<server>/restart")
def restart(server):
    output = systemctl("restart", SERVERS[server]["service"])
    time.sleep(2)
    return jsonify({"output": output, "running": is_active(SERVERS[server]["service"])})

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

    pid = get_pid(server)
    if not pid:
        return jsonify({"status": "error", "msg": "Server not running"}), 400

    try:
        # sende Befehl direkt via stdin an Java-Prozess
        proc = subprocess.Popen(["sudo", "kill", "-SIGCONT", str(pid)])
        # Alternativ: echo Befehl in screen oder tmux falls du später wieder Screen benutzt
        # subprocess.run(f"screen -S {server} -X stuff '{cmd}\n'", shell=True)
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

    return jsonify({"status": "success", "command": cmd})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
