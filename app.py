import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_socketio import SocketIO
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
import secrets
import smtplib, ssl
from cryptography.fernet import Fernet
from models import db, User, Log

# ---------------------------------------------------------
# Initial configuration
# ---------------------------------------------------------
ITALY_TZ = timezone(timedelta(hours=2))  # UTC+2
load_dotenv()
SETTINGS_FILE = ".env"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///logs.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')

socketio = SocketIO(app, cors_allowed_origins="*")
db.init_app(app)

LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", "7"))

with app.app_context():
    db.create_all()

# ---------------------------------------------------------
# Utility functions (.env management + encryption)
# ---------------------------------------------------------
def update_env_variable(key: str, value: str):
    """Update or add a variable to the .env file"""
    lines = []
    updated = False
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            for line in f:
                if line.startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    updated = True
                else:
                    lines.append(line)
    if not updated:
        lines.append(f"{key}={value}\n")
    with open(SETTINGS_FILE, "w") as f:
        f.writelines(lines)
    load_dotenv(SETTINGS_FILE, override=True)


def encrypt_value(value: str) -> str:
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise ValueError("ENCRYPTION_KEY missing in .env")
    f = Fernet(key.encode())
    return "ENCRYPTED:" + f.encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    key = os.getenv("ENCRYPTION_KEY")
    if not key or not value.startswith("ENCRYPTED:"):
        return value
    f = Fernet(key.encode())
    token = value.replace("ENCRYPTED:", "")
    return f.decrypt(token.encode()).decode()


def get_env_value(key: str, default=None):
    value = os.getenv(key, default)
    if value and value.startswith("ENCRYPTED:"):
        try:
            return decrypt_value(value)
        except Exception:
            return "[DECRYPTION ERROR]"
    return value

# ---------------------------------------------------------
# Home — Display logs
# ---------------------------------------------------------
@app.route('/')
def index():
    user_id = request.args.get("user_id", type=int)
    users = User.query.order_by(User.name.asc()).all()
    query = Log.query.order_by(Log.created_at.desc())
    if user_id:
        query = query.filter(Log.user_id == user_id)
    logs = query.limit(100).all()

    selected_user_name = None
    if user_id:
        user = db.session.get(User, user_id)
        if user:
            selected_user_name = user.name

    return render_template(
        'index.html',
        logs=logs,
        users=users,
        selected_user_id=user_id,
        selected_user_name=selected_user_name
    )

# ---------------------------------------------------------
# Log reception
# ---------------------------------------------------------
@app.route('/log', methods=['POST'])
def receive_log():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing token"}), 401

    token = auth_header.split("Bearer ")[1].strip()
    user = User.query.filter_by(token=token).first()
    if not user:
        return jsonify({"error": "Invalid token"}), 403

    data = request.get_json() or {}
    message = data.get('message', '').strip() or 'Empty log'
    level = (data.get('level') or 'info').lower()

    log_entry = Log(message=message, level=level, user=user)
    db.session.add(log_entry)
    db.session.commit()

    send_log_email(user, level, message)

    socketio.emit('new_log', {
        'message': message,
        'level': level,
        'user': user.name,
        'created_at': (log_entry.created_at + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
    })

    print(f"Saved log {level.upper()} from {user.name}")
    return jsonify({'status': 'ok'}), 200

# ---------------------------------------------------------
# Send log via email
# ---------------------------------------------------------
def send_log_email(user, level, message):
    """Send an email to the user if SMTP is configured"""
    if not user.email:
        print("User email not found.")
        return

    if os.getenv("SMTP_ENABLED", "false").lower() != "true":
        print("Email forwarding disabled.")
        return

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = get_env_value("SMTP_PASSWORD", "")
    smtp_from = os.getenv("SMTP_FROM_EMAIL", smtp_user)
    smtp_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    if not smtp_host or not smtp_user or not smtp_pass:
        print("SMTP not fully configured, no email sent.")
        return

    subject = f"[{level.upper()}] New log for {user.name}"
    body = f"""Hello {user.name},

You have received a new log:

- Level: {level.upper()}
- Message:

{message}


Regards,
Flask Log Monitor
"""
    email_text = f"From: {smtp_from}\r\nTo: {user.email}\r\nSubject: {subject}\r\n\r\n{body}"

    try:
        if smtp_port == 465 and not smtp_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=10) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, [user.email], email_text)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.ehlo()
                if smtp_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    server.ehlo()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, [user.email], email_text)
                server.quit()

        print(f"Log email successfully sent to {user.email}")

    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP authentication error ({e.smtp_code}): {e.smtp_error.decode()}")
    except smtplib.SMTPResponseException as e:
        print(f"SMTP error ({e.smtp_code}): {e.smtp_error.decode()}")
    except Exception as e:
        print(f"General email sending error: {e}")

# ---------------------------------------------------------
# User management
# ---------------------------------------------------------
@app.route('/users', methods=['GET'])
def list_users():
    users = User.query.order_by(User.name.asc()).all()
    return render_template('users.html', users=users)

@app.route('/users', methods=['POST'])
def create_user_web():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip() or None
    if not name:
        return jsonify({"error": "Missing name"}), 400

    token = secrets.token_hex(16)
    user = User(name=name, token=token, email=email)
    db.session.add(user)
    db.session.commit()

    print(f"Created user {name} ({email or 'no email'}) with token {token}")
    return jsonify({"success": True})

@app.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    print(f"Deleted user {user.name}")
    return redirect(url_for('list_users'))

# ---------------------------------------------------------
# Log management
# ---------------------------------------------------------
@app.route('/logs/<int:user_id>')
def logs_by_user(user_id):
    user = User.query.get_or_404(user_id)
    logs = Log.query.filter_by(user_id=user.id).order_by(Log.created_at.desc()).limit(100).all()
    return render_template('user_logs.html', user=user, logs=logs)

@app.route('/logs/<int:user_id>/delete', methods=['POST'])
def delete_user_logs(user_id):
    user = User.query.get_or_404(user_id)
    deleted = Log.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    flash(f"Removed {deleted} logs from {user.name}", "success")
    return redirect(url_for('logs_by_user', user_id=user.id))

@app.route('/logs/delete_all', methods=['POST'])
def delete_all_logs():
    deleted = Log.query.delete()
    db.session.commit()
    flash(f"Removed all logs ({deleted} total)", "success")
    return redirect(url_for('index'))

# ---------------------------------------------------------
# Settings (log + SMTP)
# ---------------------------------------------------------
@app.route('/settings', methods=['GET'])
def settings():
    return render_template(
        'settings.html',
        retention_days=LOG_RETENTION_DAYS,
        smtp_enabled=os.getenv("SMTP_ENABLED", "false").lower() == "true",
        smtp_host=os.getenv("SMTP_HOST", ""),
        smtp_port=os.getenv("SMTP_PORT", "587"),
        smtp_user=os.getenv("SMTP_USER", ""),
        smtp_password=get_env_value("SMTP_PASSWORD", ""),
        smtp_from=os.getenv("SMTP_FROM_EMAIL", ""),
        smtp_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    )

@app.route('/settings', methods=['POST'])
def save_settings():
    global LOG_RETENTION_DAYS
    data = request.get_json() or {}

    new_value = int(data.get('retention_days', LOG_RETENTION_DAYS))
    LOG_RETENTION_DAYS = new_value
    update_env_variable("LOG_RETENTION_DAYS", str(new_value))

    update_env_variable("SMTP_ENABLED", str(data.get("smtp_enabled", "false")).lower())
    update_env_variable("SMTP_HOST", data.get("smtp_host", ""))
    update_env_variable("SMTP_PORT", data.get("smtp_port", "587"))
    update_env_variable("SMTP_USER", data.get("smtp_user", ""))
    update_env_variable("SMTP_FROM_EMAIL", data.get("smtp_from", ""))
    update_env_variable("SMTP_USE_TLS", str(data.get("smtp_tls", "true")).lower())

    smtp_password = data.get("smtp_password")
    if smtp_password and not smtp_password.startswith("ENCRYPTED:"):
        update_env_variable("SMTP_PASSWORD", encrypt_value(smtp_password))

    print("Settings updated (LOG + SMTP)")
    return jsonify({"success": True})

# ---------------------------------------------------------
# CLI command — delete old logs
# ---------------------------------------------------------
@app.cli.command('cleanup')
def cleanup_old_logs():
    cutoff = datetime.utcnow() - timedelta(days=LOG_RETENTION_DAYS)
    deleted = Log.query.filter(Log.created_at < cutoff).delete()
    db.session.commit()
    print(f"Removed {deleted} logs older than {LOG_RETENTION_DAYS} days.")

# ---------------------------------------------------------
# App startup
# ---------------------------------------------------------
if __name__ == '__main__':
    port = int(os.getenv("APP_PORT", 5000))
    print(f"Flask Log Monitor running on http://127.0.0.1:{port}")
    socketio.run(app, host='0.0.0.0', port=port)