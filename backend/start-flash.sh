#!/usr/bin/env bash
set -e

# Entra nella cartella backend
cd "$(dirname "$0")"

# Carica variabili dal .env se presente
if [[ -f .env ]]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "Starting Flask backend on port ${APP_PORT:-5000}..."

python3 app.py
