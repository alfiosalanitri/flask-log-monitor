from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from cryptography.fernet import Fernet

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=True)
    logs = db.relationship('Log', backref='user', lazy=True, cascade="all, delete-orphan")

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(32), nullable=False)
    message = db.Column(db.Text, nullable=False)
    context = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    smtp_host = db.Column(db.String(120), nullable=False)
    smtp_port = db.Column(db.Integer, default=587)
    smtp_user = db.Column(db.String(120), nullable=False)
    smtp_password = db.Column(db.String(255), nullable=False)  # encrypted
    use_tls = db.Column(db.Boolean, default=True)
    from_email = db.Column(db.String(120), nullable=False)

    def set_password(self, raw_password, secret_key):
        f = Fernet(secret_key)
        self.smtp_password = f.encrypt(raw_password.encode()).decode()

    def get_password(self, secret_key):
        f = Fernet(secret_key)
        return f.decrypt(self.smtp_password.encode()).decode()