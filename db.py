"""
db.py — คุยกับ SQLite ตามเลคเชอร์หน้า 99 (CRUD)
ยังไม่ hash รหัส ยังไม่ใช้ SQLAlchemy
"""

import sqlite3
from pathlib import Path

# ไฟล์ DB อยู่โฟลเดอร์เดียวกับสคริปต์นี้
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "users.db"

# บัญชีเจ้าของเริ่มต้น (plaintext ตามที่ตกลง)
SEED_OWNER_USERNAME = "super"
SEED_OWNER_PASSWORD = "super"
# role ที่ใช้: super = เจ้าของ, admin = แอดมิน, user = ผู้ใช้


def get_db():
    """เปิดไฟล์ SQLite แล้วคืน connection — ใช้ row_factory ให้ดึงค่าแบบ row['username'] ได้"""
    # timeout: ถูกล็อกอยู่ให้รอก่อน แทนพังทันที (เช่น DB Browser เปิดไฟล์ค้าง)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db():
    """Create: สร้างตาราง users ถ้ายังไม่มี แล้วใส่เจ้าของคนแรกถ้าตารางว่าง"""
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
        """
    )
    conn.commit()

    row = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()
    if row["n"] == 0:
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (SEED_OWNER_USERNAME, SEED_OWNER_PASSWORD, "super"),
        )
        conn.commit()
    else:
        # ย้ายบัญชีเก่าชื่อ admin มาเป็น super / super
        old_admin = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            ("admin",),
        ).fetchone()
        new_owner = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (SEED_OWNER_USERNAME,),
        ).fetchone()
        if old_admin and not new_owner:
            conn.execute(
                """
                UPDATE users
                SET username = ?, password = ?, role = 'super'
                WHERE username = ?
                """,
                (SEED_OWNER_USERNAME, SEED_OWNER_PASSWORD, "admin"),
            )
            conn.commit()
        elif new_owner:
            conn.execute(
                "UPDATE users SET role = 'super' WHERE username = ?",
                (SEED_OWNER_USERNAME,),
            )
            conn.commit()

    conn.close()


def create_user(username, password, role="user"):
    """Create: สมัคร user ใหม่ คืน True ถ้าสำเร็จ คืน False ถ้าชื่อซ้ำ"""
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password, role),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user_by_username(username):
    """Read: หา user จากชื่อ ใช้ตอน login — fetchone ตามสไลด์หน้า 106"""
    conn = get_db()
    row = conn.execute(
        "SELECT id, username, password, role FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id):
    """Read: หา user จาก id ใช้ตอนอ่าน session"""
    conn = get_db()
    row = conn.execute(
        "SELECT id, username, password, role FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return row


def list_users():
    """Read: ดึง user ทั้งหมด ใช้หน้า admin — fetchall ตามสไลด์หน้า 106"""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, username, role FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return rows


def count_users():
    """Read: นับจำนวน user โชว์บนหัวตาราง admin"""
    conn = get_db()
    row = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()
    conn.close()
    return row["n"]


def update_user_role(user_id, role):
    """Update: สลับได้แค่ user กับ admin — ตั้ง super จากฟอร์มไม่ได้"""
    if role not in ("user", "admin"):
        return False
    target = get_user_by_id(user_id)
    if target is None or target["role"] == "super":
        return False
    conn = get_db()
    conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    conn.commit()
    conn.close()
    return True


def delete_user(user_id):
    """Delete: ลบ user ตาม id ใช้ตอน admin กดลบ"""
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
