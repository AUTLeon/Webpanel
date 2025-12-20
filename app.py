#!/usr/bin/env python3
from flask import Flask, render_template, jsonify, request
import subprocess
import os
import shlex
import time

app = Flask(__name__)

# ==================================================
# Server Configuration
# ==================================================
SERVERS = {
    "server1": {
        "name": "Fabric 1.21.10",
        "dir": "/home/leon/mc-server/fabric-1.21.10",
        "screen": "mc-server",
        "port": 25565
    },
    "server2": {
        "name": "Fabric 1.20.4",
        "dir": "/home/leon/mc-server/fabric-1.20.4",
        "screen": "mc-1204",
        "port": 25565
    }
}

# ==================================================
# Helper Functions
# ==================================================
def run(cmd, wait=True):
    if wait:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True)
    else:
        return subprocess.Popen(cmd, shell=True)


def java_running_in_dir(server_dir):
    """
    ✅ ZUVERLÄSSIGER STATUS:
    Server läuft, wenn ein Java-Prozess existiert,
    dessen Commandline im Server-Verzeichnis liegt
    """
    cmd = (
        "ps aux | grep java | grep -v grep | "
        f"grep {shlex.quote(server_dir)}"
    )
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0


def screen_exists(screen_name):
    result = subprocess.run(
        f"screen -list | grep -q {shlex.quote(screen_name)}",
        shell=True
    )
    return result.returncode == 0


def port_open(port):
    cmd = (
        f"ss -tln | grep :{port} "
        f"|| netstat -tln 2>/dev/null | grep :{port}"
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return f":{port}" in result.stdout


# ==================================================
# Routes
# ==================================================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/<server>/status")
def status(server):
    cfg = SERVERS[server]
    server_dir = cfg["dir"]

    java_running = java_running_in_dir(server_dir)
    screen_running = screen_exists(cfg["screen"])
    port_running = port_open(cfg["port"])

    if java_running:
        state = "RUNNING"
    else:
        state = "STOPPED"

    return jsonify(
        server=cfg["name"],
        status=state,
        java=java_running,
        screen=screen_running,
        port=port_running,
        timestamp=time.time()
    )


@app.route("/<server>/start")
def start(server):
    cfg = SERVERS[server]

    if java_running_in_dir(cfg["dir"]):
        return "Server läuft bereits!", 400

    start_script = os.path.join(cfg["dir"], "start.sh")
    if not os.path.exists(start_script):
        return "start.sh nicht gefunden!", 404

    run(f"bash {shlex.quote(start_script)}", wait=False)
    return "Start-Befehl gesendet."


@app.route("/<server>/stop")
def stop(server):
    cfg = SERVERS[server]

    if not java_running_in_dir(cfg["dir"]):
        return "Server läuft nicht.", 400

    stop_script = os.path.join(cfg["dir"], "stop.sh")
    if os.path.exists(stop_script):
        run(f"bash {shlex.quote(stop_script)}")
    else:
        # Fallback: graceful stop über screen
        run(
            f'screen -S {shlex.quote(cfg["screen"])} '
            f'-X stuff "stop\\n"'
        )

    time.sleep(3)
    return "Stop-Befehl gesendet."


@app.route("/<server>/restart")
def restart(server):
    stop(server)
    time.sleep(3)
    start(server)
    return "Restart ausgeführt."


@app.route("/<server>/force-stop")
def force_stop(server):
    cfg = SERVERS[server]

    run(f"screen -S {shlex.quote(cfg['screen'])} -X quit", wait=False)
    run(f"pkill -9 -f {shlex.quote(cfg['dir'])}", wait=False)

    return "Server wurde hart gestoppt."


@app.route("/<server>/logs")
def logs(server):
    cfg = SERVERS[server]
    log_file = os.path.join(cfg["dir"], "logs", "latest.log")

    if not os.path.exists(log_file):
        return "Logfile nicht gefunden.", 404

    with open(log_file, "r", errors="ignore") as f:
        return f.read(), 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.route("/<server>/console", methods=["POST"])
def console(server):
    cfg = SERVERS[server]
    data = request.get_json()
    cmd = data.get("command")

    if not cmd:
        return jsonify(error="Kein Befehl"), 400

    if not screen_exists(cfg["screen"]):
        return jsonify(error="Screen läuft nicht"), 400

    escaped = cmd.replace('"', '\\"')
    run(
        f'screen -S {shlex.quote(cfg["screen"])} '
        f'-X stuff "{escaped}\\n"'
    )
    return jsonify(success=True)


# ==================================================
# Main
# ==================================================
if __name__ == "__main__":
    print("=" * 50)
    print("Minecraft Webpanel")
    print("=" * 50)

    for sid, cfg in SERVERS.items():
        print(f"\n{sid}: {cfg['name']}")
        print(f"Dir: {cfg['dir']}")
        print(f"Java läuft: {java_running_in_dir(cfg['dir'])}")
        print(f"Screen: {screen_exists(cfg['screen'])}")

    print("\nWebpanel läuft auf http://0.0.0.0:8080\n")
    app.run(host="0.0.0.0", port=8080, debug=False)
