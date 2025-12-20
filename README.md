# 🌐 Minecraft Server – Webpanel & Server Management

A lightweight web panel for managing a **Minecraft Fabric server**.
Includes start/stop functions, log viewing, backups, and **RCON support**.

---

## 📦 Contents

* **MCRCON Command**
* **Webpanel Launch**
* **Server Scripts** (start/stop/backup)
* **Project Structure**
* **Notes & Prerequisites**

---

## 🔌 MCRCON – Minecraft Remote Console

Use this command to connect to the Minecraft server's remote console:

```bash
mcrcon -H 127.0.0.1 -P 25575 -p 9071
```
## 🌐 Webpanel Launch

### 📄 Start/Stop Scripts
The following scripts are used to manage the web panel:
- stop_panel.sh
- start_panel.sh
### ▶️ Manual Start
You can manually start the web panel by navigating to its directory and running the main Python file:
```bash
cd ~/mc-server/webpanel
python3 app.py
```

## 📂 Project Structure
This directory structure includes setups for two different Minecraft versions, showing how the server and panel components are organized.
### Key Components
| Directory/File                | Description                                                         |
|-------------------------------|---------------------------------------------------------------------|
| mc-server/                    | Root directory for the entire project.                              |
| fabric-1.20.4/                | Directory for the 1.20.4 Minecraft server instance.                 |
| fabric-1.21.10/               | Directory for the 1.21.10 Minecraft server instance.                |
| webpanel/                     | Contains the Python Flask application and its files.                |
| start.sh, stop.sh, backup.sh  | Server management scripts (located inside the version directories). |
| app.py                        | The main Python file for the web panel application.                 |
| start_panel.sh, stop_panel.sh | Scripts for managing the web panel application.                     |
| webpanel/templates/           | HTML templates for the web interface (e.g., index.html).            |
| webpanel/static/              | Static assets for the web interface (e.g., style.css).              |
| mcrcon/                       | Directory likely containing the MCRCON binary or related files.     |
```bash
mc-server/
├── fabric-1.20.4/
│   ├── .fabric/
│   ├── backups/
│   ├── config/
│   ├── ...
│   ├── start.sh
│   ├── stop.sh
│   ├── backup.sh
│   ├── eula.txt
│   ├── fabric-server-mc.1.20.4.jar
│   └── server.properties
├── fabric-1.21.10/
│   ├── start.sh
│   ├── stop.sh
│   ├── backup.sh
│   ├── ...
│   └── server.properties
├── webpanel/
│   ├── __pycache__/
│   ├── static/
│   ├── templates/
│   ├── venv/
│   ├── app.py
│   ├── README.md
│   ├── start_panel.sh
│   └── stop_panel.sh
└── mcrcon/
```
## ⚙️ Prerequisites
To run the web panel and connect to the server, ensure the following are installed and configured:
- Python 3 is installed.
- The Flask library (and any other dependencies) is available within the webpanel/ environment (likely in venv/).
- RCON is correctly configured in your Minecraft server's server.properties file:
```bash
enable-rcon=true
rcon.password=9071
rcon.port=25575
```
## Systemd
- systemctl start/stop/status/restart wepanel
- systemctl start/stop/status/restart mc-fabric-1204
- systemctl start/stop/status/restart mc-fabric-12110
## 📄 License / Usage
This setup is intended for private use to operate your own Minecraft servers. You are free to modify and expand the project as needed.
