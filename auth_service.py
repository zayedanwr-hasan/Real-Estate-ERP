import hashlib
import hmac
import os
from typing import Any, Dict, Optional

from db_connection import get_connection


PBKDF2_ITERATIONS = 200_000
VALID_ROLES = {"admin", "accountant", "viewer"}


def _hash_password(password: str, salt: bytes) -> str:
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return hashed.hex()


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = _hash_password(password, salt)
    return f"{salt.hex()}${digest}"


def verify_password(password: str, stored_password: str) -> bool:
    try:
        salt_hex, digest_hex = stored_password.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = _hash_password(password, salt)
        return hmac.compare_digest(expected, digest_hex)
    except Exception:
        return False


def ensure_auth_schema() -> None:
    conn = get_connection()
    if not conn:
        raise RuntimeError("تعذر الاتصال بقاعدة البيانات")

    bootstrap_password = os.getenv("APP_BOOTSTRAP_ADMIN_PASSWORD", "admin123")
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("CREATE SCHEMA IF NOT EXISTS finance")
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS finance.users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(80) UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role VARCHAR(20) NOT NULL DEFAULT 'viewer',
                        is_active BOOLEAN NOT NULL DEFAULT TRUE,
                        must_change_password BOOLEAN NOT NULL DEFAULT TRUE,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cur.execute("SELECT COUNT(*) FROM finance.users WHERE username = %s", ("admin",))
                exists = cur.fetchone()[0] > 0
                if not exists:
                    cur.execute(
                        """
                        INSERT INTO finance.users (username, password_hash, role, is_active, must_change_password)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        ("admin", hash_password(bootstrap_password), "admin", True, True),
                    )
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    if not conn:
        raise RuntimeError("تعذر الاتصال بقاعدة البيانات")

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, username, password_hash, role, is_active, must_change_password
                    FROM finance.users
                    WHERE username = %s
                    """,
                    (username.strip(),),
                )
                row = cur.fetchone()
                if not row:
                    return None

                user_id, user_name, password_hash_value, role, is_active, must_change_password = row
                if not is_active:
                    return None
                if not verify_password(password, password_hash_value):
                    return None

                return {
                    "id": user_id,
                    "username": user_name,
                    "role": role,
                    "must_change_password": bool(must_change_password),
                }
    finally:
        conn.close()


def change_password(user_id: int, new_password: str) -> None:
    conn = get_connection()
    if not conn:
        raise RuntimeError("تعذر الاتصال بقاعدة البيانات")

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE finance.users
                    SET password_hash = %s,
                        must_change_password = FALSE
                    WHERE id = %s
                    """,
                    (hash_password(new_password), user_id),
                )
    finally:
        conn.close()


def _validate_role(role: str) -> str:
    normalized = (role or "").strip().lower()
    if normalized not in VALID_ROLES:
        raise ValueError("الدور غير صالح")
    return normalized


def _active_admin_count(cur) -> int:
    cur.execute(
        """
        SELECT COUNT(*)
        FROM finance.users
        WHERE role = 'admin' AND is_active = TRUE
        """
    )
    return int(cur.fetchone()[0] or 0)


def create_user(username: str, password: str, role: str = "viewer") -> None:
    clean_username = (username or "").strip()
    clean_password = (password or "").strip()
    clean_role = _validate_role(role)

    if not clean_username:
        raise ValueError("اسم المستخدم مطلوب")
    if len(clean_password) < 6:
        raise ValueError("كلمة المرور يجب ألا تقل عن 6 أحرف")

    conn = get_connection()
    if not conn:
        raise RuntimeError("تعذر الاتصال بقاعدة البيانات")

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM finance.users WHERE username = %s", (clean_username,))
                if int(cur.fetchone()[0] or 0) > 0:
                    raise ValueError("اسم المستخدم موجود بالفعل")

                cur.execute(
                    """
                    INSERT INTO finance.users (username, password_hash, role, is_active, must_change_password)
                    VALUES (%s, %s, %s, TRUE, TRUE)
                    """,
                    (clean_username, hash_password(clean_password), clean_role),
                )
    finally:
        conn.close()


def list_users() -> list[Dict[str, Any]]:
    conn = get_connection()
    if not conn:
        raise RuntimeError("تعذر الاتصال بقاعدة البيانات")

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, username, role, is_active, must_change_password, created_at
                    FROM finance.users
                    ORDER BY username
                    """
                )
                rows = cur.fetchall() or []
                return [
                    {
                        "id": row[0],
                        "username": row[1],
                        "role": row[2],
                        "is_active": bool(row[3]),
                        "must_change_password": bool(row[4]),
                        "created_at": row[5].strftime("%Y-%m-%d %H:%M") if row[5] else "",
                    }
                    for row in rows
                ]
    finally:
        conn.close()


def set_user_active(user_id: int, is_active: bool) -> None:
    conn = get_connection()
    if not conn:
        raise RuntimeError("تعذر الاتصال بقاعدة البيانات")

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT role, is_active FROM finance.users WHERE id = %s", (user_id,))
                row = cur.fetchone()
                if not row:
                    raise ValueError("المستخدم غير موجود")

                role = row[0]
                current_active = bool(row[1])
                next_active = bool(is_active)

                if role == "admin" and current_active and not next_active and _active_admin_count(cur) <= 1:
                    raise ValueError("لا يمكن تعطيل آخر مدير نشط")

                cur.execute("UPDATE finance.users SET is_active = %s WHERE id = %s", (next_active, user_id))
    finally:
        conn.close()


def change_user_role(user_id: int, new_role: str) -> None:
    role_value = _validate_role(new_role)

    conn = get_connection()
    if not conn:
        raise RuntimeError("تعذر الاتصال بقاعدة البيانات")

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT role, is_active FROM finance.users WHERE id = %s", (user_id,))
                row = cur.fetchone()
                if not row:
                    raise ValueError("المستخدم غير موجود")

                old_role = row[0]
                is_active = bool(row[1])

                if old_role == "admin" and role_value != "admin" and is_active and _active_admin_count(cur) <= 1:
                    raise ValueError("لا يمكن تغيير دور آخر مدير نشط")

                cur.execute("UPDATE finance.users SET role = %s WHERE id = %s", (role_value, user_id))
    finally:
        conn.close()


def reset_user_password(user_id: int, new_password: str) -> None:
    clean_password = (new_password or "").strip()
    if len(clean_password) < 6:
        raise ValueError("كلمة المرور يجب ألا تقل عن 6 أحرف")

    conn = get_connection()
    if not conn:
        raise RuntimeError("تعذر الاتصال بقاعدة البيانات")

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE finance.users
                    SET password_hash = %s,
                        must_change_password = TRUE
                    WHERE id = %s
                    """,
                    (hash_password(clean_password), user_id),
                )
                if cur.rowcount == 0:
                    raise ValueError("المستخدم غير موجود")
    finally:
        conn.close()


def has_permission(user: Dict[str, Any], permission: str) -> bool:
    role = (user or {}).get("role", "viewer")
    role_map = {
        "admin": {"settings", "reports", "vouchers", "masters", "users"},
        "accountant": {"reports", "vouchers", "masters"},
        "viewer": {"reports"},
    }
    return permission in role_map.get(role, set())

