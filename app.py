#!/usr/bin/env python3
from flask import Flask, render_template, jsonify, request
import subprocess, os, shlex, time

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
def run(cmd, wait=True, cwd=None):
    if wait:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    else:
        return subprocess.Popen(cmd, shell=True, cwd=cwd)

def is_running(screen):
    """Überprüft ob ein Screen läuft - verbesserte Version"""
    try:
        # Methode 1: Direkt screen -list
        result1 = subprocess.run(
            f"screen -list",
            shell=True,
            capture_output=True,
            text=True,
            stderr=subprocess.DEVNULL
        )
        
        # Prüfe ob der Screen-Name in der Ausgabe erscheint
        if screen in result1.stdout:
            return True
        
        # Methode 2: Mit grep (ignoriere Fehler wenn screen nicht läuft)
        result2 = subprocess.run(
            f"screen -list | grep -i {shlex.quote(screen)}",
            shell=True,
            capture_output=True,
            text=True,
            stderr=subprocess.DEVNULL
        )
        
        if result2.returncode == 0 and screen in result2.stdout:
            return True
        
        # Methode 3: Prüfe Java-Prozess
        result3 = subprocess.run(
            f"ps aux | grep -v grep | grep java | grep -i {shlex.quote(screen)}",
            shell=True,
            capture_output=True,
            text=True
        )
        
        return result3.returncode == 0
        
    except Exception as e:
        print(f"Error checking screen {screen}: {e}")
        return False

def server_path(server, script):
    return os.path.join(SERVERS[server]["dir"], script)

# ===== Routes =====
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/<server>/status")
def status(server):
    """Verbesserter Status-Check mit mehr Debug-Info"""
    try:
        screen_name = SERVERS[server]["screen"]
        server_dir = SERVERS[server]["dir"]
        
        # Prüfe ob Server-Verzeichnis existiert
        dir_exists = os.path.exists(server_dir)
        
        # Prüfe ob Start-Script existiert
        start_script = os.path.join(server_dir, "start.sh")
        script_exists = os.path.exists(start_script) and os.access(start_script, os.X_OK)
        
        # Prüfe ob server.jar existiert
        jar_exists = os.path.exists(os.path.join(server_dir, "server.jar"))
        
        # Prüfe ob Screen läuft
        screen_running = is_running(screen_name)
        
        # Debug-Info
        debug_info = {
            "screen_name": screen_name,
            "server_dir": server_dir,
            "dir_exists": dir_exists,
            "script_exists": script_exists,
            "jar_exists": jar_exists,
            "screen_running": screen_running,
            "timestamp": time.time()
        }
        
        # Prüfe zusätzlich ob Minecraft-Server antwortet (optional)
        port_check = False
        if screen_running:
            try:
                # Prüfe auf lauschenden Port (standard 25565)
                result = subprocess.run(
                    f"netstat -tlnp 2>/dev/null | grep :25565 || ss -tlnp 2>/dev/null | grep :25565",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                port_check = ":25565" in result.stdout
                debug_info["port_check"] = port_check
            except:
                pass
        
        return jsonify(
            running=screen_running,
            status="running" if screen_running else "stopped",
            **debug_info
        )
        
    except Exception as e:
        return jsonify(
            running=False,
            status="error",
            error=str(e),
            timestamp=time.time()
        ), 500

@app.route("/<server>/start")
def start(server):
    """Verbesserte Start-Funktion"""
    try:
        screen_name = SERVERS[server]["screen"]
        server_dir = SERVERS[server]["dir"]
        
        # Prüfe ob Verzeichnis existiert
        if not os.path.exists(server_dir):
            return f"Error: Server directory {server_dir} not found!", 404
        
        # Prüfe ob Server bereits läuft
        if is_running(screen_name):
            return "Server is already running!", 400
        
        start_script = os.path.join(server_dir, "start.sh")
        
        # Methode 1: Start-Script verwenden
        if os.path.exists(start_script) and os.access(start_script, os.X_OK):
            # Führe Start-Script in Screen aus
            cmd = f"cd {shlex.quote(server_dir)} && screen -dmS {shlex.quote(screen_name)} bash {shlex.quote(start_script)}"
            result = run(cmd, wait=False)
            
            # Warte kurz und prüfe ob gestartet
            time.sleep(2)
            if is_running(screen_name):
                return f"Server started successfully in screen '{screen_name}'!"
            else:
                # Versuche alternative Methode
                pass
        
        # Methode 2: Direktes Starten mit server.jar
        jar_path = os.path.join(server_dir, "server.jar")
        if os.path.exists(jar_path):
            # Finde Java-Befehl
            java_cmd = "java"
            
            # Standard Minecraft Start-Kommando
            cmd = f"cd {shlex.quote(server_dir)} && screen -dmS {shlex.quote(screen_name)} {java_cmd} -Xmx2G -Xms1G -jar server.jar nogui"
            result = run(cmd, wait=False)
            
            time.sleep(2)
            if is_running(screen_name):
                return f"Server started with Java in screen '{screen_name}'!"
            else:
                return "Failed to start server. Check server logs.", 500
        
        # Methode 3: Start-Script ohne Screen versuchen
        if os.path.exists(start_script):
            cmd = f"cd {shlex.quote(server_dir)} && bash {shlex.quote(start_script)} &"
            result = run(cmd, wait=False)
            return "Server start command sent (running in background)."
        
        return "No start script or server.jar found!", 404
        
    except Exception as e:
        return f"Error starting server: {str(e)}", 500

@app.route("/<server>/stop")
def stop(server):
    """Verbesserte Stop-Funktion"""
    try:
        screen_name = SERVERS[server]["screen"]
        
        if not is_running(screen_name):
            return "Server is not running!", 400
        
        # Methode 1: Stop-Script verwenden
        stop_script = server_path(server, "stop.sh")
        if os.path.exists(stop_script) and os.access(stop_script, os.X_OK):
            run(f"bash {shlex.quote(stop_script)}")
            time.sleep(2)
            
        # Methode 2: Stop-Befehl an Screen senden
        elif is_running(screen_name):
            # Versuche graceful shutdown
            run(f'screen -S {shlex.quote(screen_name)} -X stuff "stop\\n"')
            time.sleep(3)
            
            # Wenn immer noch läuft, kill screen
            if is_running(screen_name):
                run(f'screen -S {shlex.quote(screen_name)} -X quit')
                time.sleep(1)
            
            # Falls nötig, Java-Prozess killen
            if is_running(screen_name):
                run(f"pkill -f {shlex.quote(screen_name)}")
        
        # Prüfe ob wirklich gestoppt
        time.sleep(2)
        if not is_running(screen_name):
            return "Server stopped successfully!"
        else:
            return "Server might still be running. Please check manually.", 500
            
    except Exception as e:
        return f"Error stopping server: {str(e)}", 500

@app.route("/<server>/backup")
def backup(server):
    """Backup-Funktion"""
    backup_script = server_path(server, "backup.sh")
    if os.path.exists(backup_script) and os.access(backup_script, os.X_OK):
        result = run(f"bash {shlex.quote(backup_script)}")
        if result.returncode == 0:
            return "Backup completed successfully!"
        else:
            return f"Backup failed: {result.stderr}", 500
    return "Backup script missing or not executable!", 404

@app.route("/<server>/logs")
def logs(server):
    """
    Reads the entire latest.log file
    """
    log_file = os.path.join(SERVERS[server]["dir"], "logs", "latest.log")
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", errors="ignore") as f:
                content = f.read()
            return content, 200, {"Content-Type": "text/plain; charset=utf-8"}
        except Exception as e:
            return f"Error reading log file: {str(e)}", 500
    return "latest.log not found!", 404

@app.route("/<server>/console", methods=["POST"])
def console(server):
    """Send command to server console"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "msg": "No JSON data"}), 400
            
        cmd = data.get("command")
        if not cmd:
            return jsonify({"status": "error", "msg": "No command provided"}), 400
            
        screen_name = SERVERS[server]["screen"]
        if not is_running(screen_name):
            return jsonify({"status": "error", "msg": "Server not running"}), 400
        
        # Escape special characters for screen
        escaped_cmd = cmd.replace('"', '\\"').replace("'", "\\'")
        
        # Send command to screen
        run(f'screen -S {shlex.quote(screen_name)} -X stuff "{escaped_cmd}\\n"')
        
        # Optional: Warte für Ausgabe
        time.sleep(0.5)
        
        return jsonify({"status": "success", "msg": f"Command sent: {cmd}"})
        
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

@app.route("/<server>/restart")
def restart(server):
    """Restart server"""
    try:
        # Zuerst stoppen
        stop_response = stop(server)
        
        # Warte 3 Sekunden
        time.sleep(3)
        
        # Dann starten
        start_response = start(server)
        
        return "Restart command sent. Stopping and starting server..."
        
    except Exception as e:
        return f"Error during restart: {str(e)}", 500

@app.route("/<server>/force-stop")
def force_stop(server):
    """Force stop server (kill processes)"""
    try:
        screen_name = SERVERS[server]["screen"]
        
        # Kill screen session
        run(f"screen -S {shlex.quote(screen_name)} -X quit 2>/dev/null", wait=False)
        time.sleep(1)
        
        # Kill Java processes with this screen name
        run(f"pkill -9 -f {shlex.quote(screen_name)}", wait=False)
        time.sleep(1)
        
        # Kill any remaining Java processes in the directory
        server_dir = SERVERS[server]["dir"]
        run(f"pkill -9 -f {shlex.quote(server_dir)}", wait=False)
        
        time.sleep(2)
        
        if not is_running(screen_name):
            return "Server force-stopped successfully!"
        else:
            return "Warning: Some processes might still be running.", 500
            
    except Exception as e:
        return f"Error force-stopping: {str(e)}", 500

# ===== Main =====
if __name__ == "__main__":
    print("=" * 50)
    print("Minecraft Server Panel")
    print("=" * 50)
    
    # Teste Server-Konfiguration
    for server_id, config in SERVERS.items():
        print(f"\nChecking {server_id} ({config['name']}):")
        print(f"  Directory: {config['dir']}")
        print(f"  Screen: {config['screen']}")
        
        if os.path.exists(config['dir']):
            print(f"  ✓ Directory exists")
            
            # Prüfe Start-Script
            start_script = os.path.join(config['dir'], "start.sh")
            if os.path.exists(start_script):
                print(f"  ✓ Start script found")
            else:
                print(f"  ✗ Start script not found")
                
            # Prüfe server.jar
            jar_file = os.path.join(config['dir'], "server.jar")
            if os.path.exists(jar_file):
                print(f"  ✓ server.jar found")
            else:
                print(f"  ✗ server.jar not found")
        else:
            print(f"  ✗ Directory does not exist!")
    
    print("\n" + "=" * 50)
    print("Starting web panel on http://0.0.0.0:8080")
    print("=" * 50 + "\n")
    
    app.run(host="0.0.0.0", port=8080, debug=True)