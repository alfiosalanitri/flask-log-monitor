# Flask Log Monitor

**Flask Log Monitor** is a **Python + Flask** web app designed to receive, display, store, and forward logs via email from other applications (for example, **Laravel**).
Each log is saved in a database and displayed live through **WebSocket**, powered by **Flask-SocketIO**.
Each user has their own token and separate logs, with the option to receive notifications by email.

---

## ⚠️ Security Notice

> The **home page displays all logs from all users without any authentication or protection**.
> For this reason, **Flask Log Monitor is intended exclusively for development, testing, or staging environments** — **not for production use**.
>
> If you plan to deploy it in production, you must implement an **authentication system** or protect it via a **reverse proxy (such as Basic Auth or VPN access)**.

---

## 🚀 Main Features

* Receive logs via authenticated **HTTP POST** (Bearer token)
* Real-time dashboard with **Socket.IO**
* Modern UI using **TailwindCSS + Lucide Icons**
* Multi-user management with unique tokens
* Automatic **email forwarding (SMTP)**
* Encrypted SMTP password stored in `.env`
* Automatic old log cleanup via **daily cron job**
* Native integration with **Laravel Monolog**

---

## ⚙️ Installation (Standalone Mode)

### Clone the project

```bash
git clone https://github.com/your-username/flask-log-monitor.git
cd flask-log-monitor
```

### Create a virtual environment

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

### Configure the `.env` file

```bash
cp .env.example .env
```

---

## 🧑‍💻 Using the Web Interface

### **Home**

Displays all logs (up to the latest 100), filterable by user.
Each log card shows:

* User name (with icon)
* Date and time (UTC+2)
* Log level (info, warning, error, critical)
* Message text

Logs are updated **live** in real time via **Socket.IO**.

---

### 👥 **User Management**

Go to **/users** or click “Users” in the navbar:

* Create a new user by specifying a **name** and **email** → a token is automatically generated.
* You can **view** or **delete** a user (including their logs).
* The email field is optional, but if provided, the user will receive logs via SMTP.

---

### ✉️ **Email Log Forwarding**

If the user has an email address and SMTP is correctly configured:

* Every new log received via API is automatically forwarded to the user.
* SMTP credentials are encrypted in the `.env` file using **Fernet Encryption**.
* You can edit host, port, username, and sender directly from **/settings**.

---

### ⚙️ **Settings**

The `/settings` section allows you to:

* Set log retention days (`LOG_RETENTION_DAYS`)
* Configure SMTP (host, port, user, password, from, TLS)
* Enable or disable email sending (`SMTP_ENABLED`)
* The password is **automatically encrypted** in `.env`

---

### 🧹 **Automatic Cleanup**

A built-in cron job automatically deletes logs older than `LOG_RETENTION_DAYS` every day at **03:00**.
You can also run it manually:

```bash
flask --app app cleanup
```

---

## 🧩 Laravel Integration

### 1️⃣ Configure the channel in Laravel’s `.env`

```env
LOG_CHANNEL=stack
LOG_FLASK_URL=http://localhost:5000
LOG_FLASK_TOKEN=token-generated-from-app
LOG_FLASK_LEVEL=debug
```

### 2️⃣ Edit `config/logging.php`

```php
'flask' => [
    'driver' => 'monolog',
    'level' => env('LOG_FLASK_LEVEL', 'debug'),
    'url' => env('LOG_FLASK_URL', 'http://localhost:5000'),
    'token' => env('LOG_FLASK_TOKEN', '1234'),
    'handler' => \App\Logging\FlaskLogHandler::class,
],

'stack' => [
    'driver' => 'stack',
    'channels' => ['daily', 'flask'],
],
```

### 3️⃣ `app/Logging/FlaskLogHandler.php`

```php
<?php

namespace App\Logging;

use Illuminate\Support\Facades\Http;
use Monolog\Handler\AbstractProcessingHandler;
use Monolog\Level;
use Monolog\LogRecord;

class FlaskLogHandler extends AbstractProcessingHandler
{
    protected string $url;
    protected string $token;

    public function __construct($level = Level::Debug, bool $bubble = true)
    {
        parent::__construct($level, $bubble);
        $this->url = config('logging.channels.flask.url') . '/log';
        $this->token = config('logging.channels.flask.token');
    }

    protected function write(array|LogRecord $record): void
    {
        try {
            Http::withToken($this->token)
                ->timeout(2)
                ->post($this->url, [
                    'level' => $record['level_name'],
                    'message' => $record['message'],
                ]);
        } catch (\Throwable $e) {
            \Log::channel('daily')->debug('Error sending log to Flask: ' . $e->getMessage());
        }
    }
}
```

### 4️⃣ Test it!

```php
Log::info('Hello from Laravel!');
Log::error('Something went wrong!');
```

➡️ You’ll see the messages appear live — and receive an email if configured.

---

## 📡 Send Logs Manually (via `curl`)

```bash
curl -X POST http://localhost:5000/log \
  -H "Authorization: Bearer 1234" \
  -H "Content-Type: application/json" \
  -d '{"level": "warning", "message": "Manual log test via curl"}'
```

---

## 🐳 Docker Compose

### `docker-compose.yml`

```bash
docker compose up -d --build
```

---

## 💡 Tips

* You can temporarily disable emails by setting `SMTP_ENABLED=false`
* Generate the encryption key once:

  ```bash
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
* Passwords updated from the web interface are **automatically encrypted**
* New logs appear live and remain visible until manually deleted

---

## 🔒 Secure Deployment (Optional)

If you plan to expose Flask Log Monitor on a public server:

1. Protect access using **Basic Auth** (e.g., via Nginx reverse proxy)

   ```nginx
   auth_basic "Restricted Access";
   auth_basic_user_file /etc/nginx/.htpasswd;
   ```

2. Or restrict access to a **VPN network** (e.g., WireGuard or Tailscale)

3. Always serve via **HTTPS** and disable direct public access to port `5000`.

These simple steps ensure that sensitive log data is not exposed publicly.

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details. 📜