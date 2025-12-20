#!/usr/bin/env python3
from flask import Flask, render_template, jsonify, request
import subprocess, time

app = Flask(__name__)

SERVERS = {
    "server1": {
        "name": "1.21.10",
        "service": "mc-fabric-12110.service"
    },
    "server2": {
        "name": "1.20.4",
        "service": "mc-fabric-1204.service"
    }
}

def systemctl(cmd, service):
    """Führt systemctl-Befehle aus und gibt Ausgabe zurück"""
    try:
        result = subprocess.run(
            ["systemctl", "--user", cmd, service],
            capture_output=True, text=True
        )
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)

def is_active(service):
    """Prüft ob Service läuft"""
    result = subprocess.run(
        ["systemctl", "--user", "is-active", service],
        capture_output=True, text=True
    )
    return result.stdout.strip() == "active"

@app.route("/")
def index():
    return render_template("index.html", servers=SERVERS)

@app.route("/<server>/status")
def status(server):
    svc = SERVERS[server]["service"]
    running = is_active(svc)
    return jsonify({
        "running": running,
        "service": svc
    })

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
    dir_map = {
        "server1": "/home/leon/mc-server/fabric-1.21.10/backup.sh",
        "server2": "/home/leon/mc-server/fabric-1.20.4/backup.sh"
    }
    backup_script = dir_map[server]
    try:
        result = subprocess.run(["bash", backup_script], capture_output=True, text=True)
        return jsonify({"output": result.stdout + result.stderr})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
