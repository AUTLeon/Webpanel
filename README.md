# 🌐 Minecraft Server – Webpanel & Serververwaltung

Ein leichtes Webpanel zur Verwaltung eines Minecraft-Fabric-Servers.  
Beinhaltet Start/Stop-Funktionen, Loganzeige, Backups und RCON-Unterstützung.

---

## 📦 Inhalt
- MCRCON Befehl  
- Webpanel starten  
- Server-Skripte (start/stop/backup)  
- Webpanel-Dateien  
- Panel-Startskripte  
- Projektstruktur  
- Hinweise & Voraussetzungen  

---

## 🔌 MCRCON – Minecraft Konsole

Nutze diesen Befehl, um dich mit der Minecraft-Konsole zu verbinden:
```bash
mcrcon -H 127.0.0.1 -P 25575 -p 9071
```
Stelle sicher, dass **RCON in der server.properties aktiviert** ist.

---

## 🌐 Webpanel starten

### 📄 Start Files
- start_panel.sh
- stop_panel.sh

### ▶️ Manuell starten

```bash
cd ~/mc-server/webpanel
python3 app.py
```
---
## 📂 Projektstruktur
```bash
mc-server/
└── fabric-1.21.10/
    ├── start.sh
    ├── stop.sh
    ├── backup.sh
    └──README.md
webpanel/
├── app.py
├──start_panel.sh
└──stop_panel.sh
```
---
## ⚙️ Voraussetzungen
- Python 3 installiert
- Flask im Webpanel vorhanden
- RCON aktiviert im Minecraft-Server:

```bash
enable-rcon=true
rcon.password=9071
rcon.port=25575
```
## 📄 Lizenz / Nutzung  
Dieses Setup ist privat und für den Betrieb eigener Minecraft-Server gedacht.
Du kannst das Projekt frei anpassen und erweitern.
