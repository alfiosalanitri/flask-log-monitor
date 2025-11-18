# Flask Log Monitor

![Docker Build](https://github.com/alfiosalanitri/flask-log-monitor/actions/workflows/docker-build.yml/badge.svg)
![AppImage Build](https://github.com/alfiosalanitri/flask-log-monitor/actions/workflows/appimage-build.yml/badge.svg)
[![Latest Release](https://img.shields.io/github/v/release/alfiosalanitri/flask-log-monitor)](https://github.com/alfiosalanitri/flask-log-monitor/releases/latest)
[![Download AppImage](https://img.shields.io/badge/Download-Latest%20AppImage-green?style=for-the-badge&logo=linux)](https://github.com/alfiosalanitri/flask-log-monitor/releases/latest)
![GHCR](https://img.shields.io/badge/GHCR-Container%20Registry-2496ED?logo=docker)
![AppImage Size](https://img.shields.io/github/download-size/alfiosalanitri/flask-log-monitor/latest/FlaskLogMonitor.AppImage?label=AppImage%20Size)

**Flask Log Monitor** is a **Python + Flask** web app designed to receive, display, store, and forward logs via email from any external application (for example, **Laravel**).
Logs are stored in a database and displayed live via **Flask-SocketIO**, with per-user log isolation and optional email forwarding.

---

# 🚀 How to Use

You can use Flask Log Monitor in **two different ways**:

---

# 🖥️ 1) Desktop Application (AppImage) — Zero Installation

The Desktop Edition bundles:

✔ Flask backend  
✔ Embedded Python runtime  
✔ Electron UI  
✔ Your `.env`  
✔ Portable single-file executable  

👉 **Download the latest AppImage:**  
https://github.com/alfiosalanitri/flask-log-monitor/releases/latest

### Run on Linux

```bash
chmod +x FlaskLogMonitor*.AppImage
./FlaskLogMonitor*.AppImage
````

This automatically starts:

* the embedded Flask backend (port 5000)
* the Electron UI
* no dependencies required

Perfect for developer workstations.

---

# 🐋 2) How to Use with Docker (Recommended for Servers)

### Create and configure the `.env` file

```bash
vim .env

# ==========================================================
# BASE CONFIGURATION — FLASK LOG MONITOR
# ==========================================================
APP_PORT=5000
APP_DEBUG=False
DATABASE_URL=sqlite:///logs.db
FLASK_ENV=production
SECRET_KEY=super-secret-key-123

# ==========================================================
# SMTP PASSWORD ENCRYPTION
# ==========================================================
# Generate a key with:
# docker run --rm ghcr.io/alfiosalanitri/docker-fernet-key-generator:latest
ENCRYPTION_KEY=

# ==========================================================
# LOG RETENTION
# ==========================================================
LOG_RETENTION_DAYS=7

# ==========================================================
# EMAIL SETTINGS (SMTP)
# ==========================================================
SMTP_ENABLED=false
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=ENCRYPTED:...
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=
```

### Run using Docker

```bash
docker run -d \
  -p 5000:5000 \
  --env-file .env \
  ghcr.io/alfiosalanitri/flask-log-monitor:latest
```

Open:

```
http://localhost:5000
```

---

# 🖼 Screenshots

### Homepage

![home](screenshots/home.png)

### Manage Users

![users](screenshots/users.png)

### Settings

![settings](screenshots/settings.png)

### Send Mail

![send mail](screenshots/send-mail.png)

---

# ⚠️ Security Notice

> By default, the home page displays all logs from all users **without authentication**.
> Flask Log Monitor is designed for **development, staging, or testing** — **not production**.

If deploying publicly, **protect it**:

* Reverse Proxy + Basic Auth
* HTTPS only
* VPN-only access (WireGuard, Tailscale)

---

# 🚀 Main Features

* Receive logs via authenticated HTTP POST (Bearer token)
* Real-time updates with Flask-SocketIO
* Modern UI (TailwindCSS + Lucide icons)
* Per-user log separation & unique tokens
* Automatic SMTP email forwarding
* Encrypted SMTP password storage
* Daily cleanup cron + manual cleanup
* Laravel-native integration

---

# ⚙️ Installation (Standalone Mode) for Development

### Clone

```bash
git clone https://github.com/alfiosalanitri/flask-log-monitor.git
cd flask-log-monitor
```

### Install Python dependencies

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

### Configure `.env`

```bash
cp .env.example .env
APP_DEBUG=True
```

### Generate ENCRYPTION_KEY

```bash
docker run --rm ghcr.io/alfiosalanitri/docker-fernet-key-generator:latest
```

### Run

```bash
python ./app.py
```

---

# 🧑‍💻 Web Interface Overview

### Home

Real-time logs (latest 100).

### User Management

Create/view/delete users, each with individual tokens.

### Email Forwarding

Automatic SMTP log delivery if configured.

### Settings

Modify log retention, SMTP config, encryption.

### Cleanup Commands

```bash
flask --app app cleanup
```

---

# 🧩 Laravel Integration

Package:
👉 [https://github.com/alfiosalanitri/laravel-flask-logger](https://github.com/alfiosalanitri/laravel-flask-logger)

### Install

```bash
composer require alfiosalanitri/laravel-flask-logger
```

### Configure

```env
LOG_CHANNEL=stack
LOG_STACK=flask,daily
LOG_FLASK_URL=http://localhost:5000
LOG_FLASK_TOKEN=token
LOG_FLASK_LEVEL=debug
```

### Test

```php
Log::info('Hello from Laravel!');
Log::error('Something went wrong!');
```

---

# 📡 Send Logs Manually

```bash
curl -X POST http://localhost:5000/log \
  -H "Authorization: Bearer 1234" \
  -H "Content-Type: application/json" \
  -d '{"level": "warning", "message": "Manual log test"}'
```

---

# 🐳 Docker Compose Examples

(Same as your original README)

---

# 💡 Tips

* Set `SMTP_ENABLED=false` to temporarily disable emails
* Passwords updated in `/settings` are auto-encrypted
* Logs appear live via WebSockets

---

# 🔒 Secure Deployment Checklist

Use one of the following:

* Nginx reverse proxy + Basic Auth
* HTTPS
* VPN access only

---

# 📄 License

MIT — see LICENSE.

```