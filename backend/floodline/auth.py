from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import timedelta
from uuid import uuid4

from .config import stamp, wall_now


def password_hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 310_000).hex()


def create_moderator(db, connection, username: str, password: str):
    existing = db.one(connection, "SELECT id FROM users WHERE username = ?", (username,))
    if existing:
        return existing["id"]
    user_id, salt = uuid4().hex, secrets.token_hex(16)
    db.execute(connection, "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
               (user_id, username, "moderator", salt, password_hash(password, salt), stamp(wall_now())))
    return user_id


def create_session(db, connection, user_id: str, hours: int):
    token = secrets.token_urlsafe(36)
    now = wall_now()
    db.execute(connection, "INSERT INTO sessions VALUES (?, ?, ?, ?)",
               (hashlib.sha256(token.encode()).hexdigest(), user_id, stamp(now), stamp(now + timedelta(hours=hours))))
    return token


def current_user(db, token: str | None):
    if not token:
        return None
    digest = hashlib.sha256(token.encode()).hexdigest()
    with db.transaction() as connection:
        row = db.one(connection, "SELECT users.id, users.username, users.role FROM sessions "
                     "JOIN users ON users.id = sessions.user_id WHERE sessions.token_hash = ? "
                     "AND sessions.expires_at > ?", (digest, stamp(wall_now())))
    return row


def check_login(db, connection, username: str, password: str):
    row = db.one(connection, "SELECT * FROM users WHERE username = ? AND role = 'moderator'", (username,))
    # Perform an expensive comparison even for an unknown account.
    salt = row["password_salt"] if row else "0" * 32
    expected = row["password_hash"] if row else "0" * 64
    valid = hmac.compare_digest(password_hash(password, salt), expected)
    return row if row and valid else None
