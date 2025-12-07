#!/usr/bin/env python3
from flask import Flask, render_template, jsonify, request
import subprocess, os, shlex

app = Flask(__name__)

# === Server Konfiguration ===
SERVERS = {
    "server1": {
        "name": "1.21.10",
        "dir": os.path.expanduser("~/mc-server/fabric-1.21.10"),
        "screen": "mc-server"
    },
    "server2": {
        "name": "1.20.4",
        "dir": os.path.expanduser("~/mc-server/fabric-1.20.4"),
        "screen": "mc-1204"
    }
}

def run(cmd, wait=True):
    if wait:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True)
    else:
        return subprocess.Popen(cmd, shell=True)

def is_running(screen):
    res = run(f"screen -ls | grep {shlex.quote(screen)}")
    return res.returncode == 0

def server_path(server, script):
    return os.path.join(SERVERS[server]["dir"], script)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/<server>/status")
def status(server):
    try:
        scr = SERVERS[server]["screen"]
        running = is_running(scr)
        return jsonify(running=running, detected_screen=scr)
    except Exception as e:
        return jsonify(running=False, error=str(e)), 500

@app.route("/<server>/start")
def start(server):
    start_sh = server_path(server, "start.sh")
    if os.path.exists(start_sh) and os.access(start_sh, os.X_OK):
        run(f"bash {shlex.quote(start_sh)}")
        return "Starte Server..."
    return "Start-Skript fehlt oder nicht ausführbar!", 500

@app.route("/<server>/stop")
def stop(server):
    stop_sh = server_path(server, "stop.sh")
    scr = SERVERS[server]["screen"]
    if os.path.exists(stop_sh) and os.access(stop_sh, os.X_OK):
        run(f"bash {shlex.quote(stop_sh)}")
        return "Stoppe Server..."
    elif is_running(scr):
        run(f'screen -S {shlex.quote(scr)} -X stuff "stop\n"')
        return f"Stoppe Server (screen: {scr})..."
    return "Kein Server-Screen gefunden!", 500

@app.route("/<server>/backup")
def backup(server):
    backup_sh = server_path(server, "backup.sh")
    if os.path.exists(backup_sh) and os.access(backup_sh, os.X_OK):
        run(f"bash {shlex.quote(backup_sh)}")
        return "Backup wird gestartet..."
    return "Backup-Skript fehlt!", 404

@app.route("/<server>/logs")
def logs(server):
    log_file = os.path.join(SERVERS[server]["dir"], "server.log")
    n = int(request.args.get("lines", "200"))
    if os.path.exists(log_file):
        with open(log_file,"r",errors="ignore") as f:
            lines = f.readlines()
        return "".join(lines[-n:]), 200, {"Content-Type":"text/plain; charset=utf-8"}
    return "server.log nicht gefunden!", 404

@app.route("/<server>/console", methods=["POST"])
def console(server):
    cmd = request.json.get("command")
    scr = SERVERS[server]["screen"]
    if not is_running(scr):
        return jsonify({"status":"error","msg":"Server nicht gestartet"}),400
    if cmd:
        run(f'screen -S {shlex.quote(scr)} -X stuff "{cmd}\n"')
        return f"Gesendet: {cmd}"
    return "Kein Command", 400

if __name__=="__main__":
    app.run(host="0.0.0.0", port=8080)
