#!/bin/bash

# Nome della sessione screen
SCREEN_SESSION="monitor_transmission"

# Percorso completo al tuo script Python
SCRIPT_PATH="/home/pi/monitor_transmission/monitor_transmission.py"

# Controlla se la sessione screen è già in esecuzione
if screen -list | grep -q "$SCREEN_SESSION"; then
    echo "La sessione screen '$SCREEN_SESSION' è già in esecuzione."
else
    # Avvia una nuova sessione screen in modalità detached
#    screen -dmS "$SCREEN_SESSION" /usr/bin/python3 "$SCRIPT_PATH"
    /usr/bin/screen -dmS "$SCREEN_SESSION" /usr/bin/python3 "$SCRIPT_PATH"
    echo "Avviata la sessione screen '$SCREEN_SESSION' con lo script Python."
fi

