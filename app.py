#!/usr/bin/env python3
from flask import Flask, render_template, jsonify, request
import subprocess, shlex, time

app = Flask(__name__)

# === Server Konfiguration ===
SERVERS = {
    "server12110": {
        "name": "1.21.10",
        "service": "mc-fabric-12110.service"
    },
    "server1204": {
        "name": "1.20.4",
        "service": "mc-fabric-1204.service"
    }
}

# ===== Helper Funktionen =====
def systemctl_status(service):
    """Gibt den Status des Systemd-Services zurück"""
    cmd = f"systemctl is-active {shlex.quote(service)}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def systemctl_action(service, action):
    """Start/Stop/Restart eines Systemd-Services"""
    cmd = f"sudo systemctl {action} {shlex.quote(service)}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

# ===== Routes =====
@app.route("/")
def index():
    """Hauptseite"""
    statuses = {}
    for sid, cfg in SERVERS.items():
        statuses[sid] = systemctl_status(cfg["service"])
    return render_template("index.html", statuses=statuses, servers=SERVERS)

@app.route("/<server>/status")
def status(server):
    if server not in SERVERS:
        return jsonify({"error": "Unknown server"}), 404
    status_str = systemctl_status(SERVERS[server]["service"])
    running = status_str == "active"
    return jsonify({"running": running, "status": status_str})

@app.route("/<server>/start")
def start(server):
    if server not in SERVERS:
        return jsonify({"error": "Unknown server"}), 404
    code, out, err = systemctl_action(SERVERS[server]["service"], "start")
    success = code == 0
    return jsonify({"success": success, "stdout": out, "stderr": err})

@app.route("/<server>/stop")
def stop(server):
    if server not in SERVERS:
        return jsonify({"error": "Unknown server"}), 404
    code, out, err = systemctl_action(SERVERS[server]["service"], "stop")
    success = code == 0
    return jsonify({"success": success, "stdout": out, "stderr": err})

@app.route("/<server>/restart")
def restart(server):
    if server not in SERVERS:
        return jsonify({"error": "Unknown server"}), 404
    code, out, err = systemctl_action(SERVERS[server]["service"], "restart")
    success = code == 0
    return jsonify({"success": success, "stdout": out, "stderr": err})

@app.route("/<server>/backup")
def backup(server):
    """Backup-Skript ausführen"""
    import os
    if server not in SERVERS:
        return jsonify({"error": "Unknown server"}), 404
    # Backup Pfad
    if server == "server12110":
        script = os.path.expanduser("~/mc-server/fabric-1.21.10/backup.sh")
    else:
        script = os.path.expanduser("~/mc-server/fabric-1.20.4/backup.sh")
    
    if not os.path.exists(script) or not os.access(script, os.X_OK):
        return jsonify({"error": "Backup script missing or not executable"}), 404
    
    result = subprocess.run(f"bash {shlex.quote(script)}", shell=True, capture_output=True, text=True)
    success = result.returncode == 0
    return jsonify({"success": success, "stdout": result.stdout, "stderr": result.stderr})

# ===== Main =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
