#!/usr/bin/env python3
from flask import Flask, render_template, jsonify, request
import subprocess, os, shlex

app = Flask(__name__)

# === Server Configuration ===
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

# Helper functions
def run(cmd, wait=True):
    if wait:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True)
    else:
        return subprocess.Popen(cmd, shell=True)

def is_running(screen):
    result = run(f"screen -ls | grep {shlex.quote(screen)}")
    return result.returncode == 0

def server_path(server, script):
    return os.path.join(SERVERS[server]["dir"], script)

# ===== Routes =====
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/<server>/status")
def status(server):
    try:
        screen_name = SERVERS[server]["screen"]
        running = is_running(screen_name)
        return jsonify(running=running, detected_screen=screen_name)
    except Exception as e:
        return jsonify(running=False, error=str(e)), 500

@app.route("/<server>/start")
def start(server):
    start_script = server_path(server, "start.sh")
    if os.path.exists(start_script) and os.access(start_script, os.X_OK):
        run(f"bash {shlex.quote(start_script)}")
        return "Starting server..."
    return "Start script missing or not executable!", 500

@app.route("/<server>/stop")
def stop(server):
    stop_script = server_path(server, "stop.sh")
    screen_name = SERVERS[server]["screen"]
    if os.path.exists(stop_script) and os.access(stop_script, os.X_OK):
        run(f"bash {shlex.quote(stop_script)}")
        return "Stopping server..."
    elif is_running(screen_name):
        run(f'screen -S {shlex.quote(screen_name)} -X stuff "stop\n"')
        return f"Stopping server (screen: {screen_name})..."
    return "No server screen found!", 500

@app.route("/<server>/backup")
def backup(server):
    backup_script = server_path(server, "backup.sh")
    if os.path.exists(backup_script) and os.access(backup_script, os.X_OK):
        run(f"bash {shlex.quote(backup_script)}")
        return "Backup started..."
    return "Backup script missing!", 404

@app.route("/<server>/logs")
def logs(server):
    """
    Reads the entire latest.log file
    """
    log_file = os.path.join(SERVERS[server]["dir"], "logs", "latest.log")
    if os.path.exists(log_file):
        with open(log_file, "r", errors="ignore") as f:
            content = f.read()
        return content, 200, {"Content-Type": "text/plain; charset=utf-8"}
    return "latest.log not found!", 404

@app.route("/<server>/console", methods=["POST"])
def console(server):
    cmd = request.json.get("command")
    screen_name = SERVERS[server]["screen"]
    if not is_running(screen_name):
        return jsonify({"status": "error", "msg": "Server not running"}), 400
    if cmd:
        run(f'screen -S {shlex.quote(screen_name)} -X stuff "{cmd}\n"')
        return f"Sent: {cmd}"
    return "No command provided", 400

# ===== Main =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
