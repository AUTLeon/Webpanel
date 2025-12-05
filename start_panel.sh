#!/bin/bash

SCREEN_NAME="mc-panel"
APP_DIR="$HOME/mc-server/webpanel"

# Prüfen, ob die Session schon läuft
if screen -list | grep -q "$SCREEN_NAME"; then
    echo "Panel läuft bereits!"
else
    echo "Starte Minecraft Panel..."
    # Mit cd ins richtige Verzeichnis wechseln und Flask starten
    screen -dmS $SCREEN_NAME bash -c "cd $APP_DIR && python3 app.py"
    echo "Panel gestartet!"
fi
