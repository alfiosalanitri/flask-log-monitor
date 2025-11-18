#!/usr/bin/env bash
set -e

echo "Launching Flask + Electron Desktop App"

# Root folder of the project
ROOT=$(dirname "$(dirname "$0")")

cd "$ROOT"

# Start Flask backend
./backend/start-flask.sh &
FLASK_PID=$!

echo "Waiting for Flask to be ready..."

# Wait for localhost:5000 to respond
until curl -s http://127.0.0.1:5000 > /dev/null; do
  sleep 0.3
done

echo "Flask backend is ready!"

# Start Electron app
npm --prefix desktop-app start

# When Electron closes → kill Flask
kill $FLASK_PID
echo "Flask backend stopped"
