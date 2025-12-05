#!/bin/bash

SCREEN_NAME="mc-panel"

if screen -list | grep -q "$SCREEN_NAME"; then
    screen -S $SCREEN_NAME -X quit
    echo "Panel gestoppt!"
else
    echo "Panel läuft nicht."
fi
