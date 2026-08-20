"""
app.py — Flask เสิร์ฟ HTML + ต่อ SQLite

"""

from flask import Flask, redirect, render_template, request, session, url_for
import sqlite3

from db import (
    count_users,
    create_user,
    delete_user,
    get_user_by_id,
    get_user_by_username,
    init_db,
    list_users,
    update_user_role,
)

app = Flask(__name__)
# secret ชั่วคราวสำหรับ session — ยังไม่เน้นความปลอดภัย
app.secret_key = "restore-web-dev-not-secure"


def current_user():
    """อ่าน user จาก session ถ้ายังไม่ login คืน None"""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_user_by_id(user_id)


def is_super(user):
    """เจ้าของระบบ — ตั้งแอดมินได้ ลบแอดมินได้ ลบตัวเองไม่ได้"""
    return user is not None and user["role"] == "super"


def is_staff(user):
    """เข้าหน้าหลังบ้านได้: เจ้าของ หรือ แอดมิน"""
    return user is not None and user["role"] in ("super", "admin")


def render_admin(user, error=None):
    """วาดหน้า admin พร้อมรายชื่อล่าสุด"""
    return render_template(
        "admin.html",
        user=user,
        users=list_users(),
        total=count_users(),
        error=error,
        owner=is_super(user),
    )


@app.route("/")
def index():
    """หน้าแรกส่งไป login หรือ home ถ้า login อยู่แล้ว"""
    if current_user():
        return redirect(url_for("home"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """สมัครสมาชิก — Create user ลง SQLite"""
    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        try:
            if not username or not password:
                error = "กรอกชื่อกับรหัสก่อน"
            elif get_user_by_username(username):
                error = "ชื่อนี้มีคนใช้แล้ว"
            elif create_user(username, password, role="user"):
                return redirect(url_for("login"))
            else:
                error = "สมัครไม่สำเร็จ"
        except sqlite3.OperationalError:
            error = "ฐานข้อมูลถูกล็อก — ปิด DB Browser for SQLite แล้วลองใหม่"

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    """เข้าสู่ระบบ — Read user แล้วเทียบรหัสแบบ plaintext"""
    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = get_user_by_username(username)

        if user is None or user["password"] != password:
            error = "ชื่อหรือรหัสไม่ถูกต้อง"
        else:
            session["user_id"] = user["id"]
            return redirect(url_for("home"))

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    """ออกจากระบบ — ล้าง session"""
    session.clear()
    return redirect(url_for("login"))


@app.route("/home")
def home():
    """หน้าหลัง login — ยังเป็น placeholder เครื่องมือรูปมาทีหลัง"""
    user = current_user()
    if user is None:
        return redirect(url_for("login"))
    return render_template("home.html", user=user, staff=is_staff(user))


@app.route("/admin")
def admin():
    """หน้า admin — ดูรายชื่อ user ทั้งหมด"""
    user = current_user()
    if user is None:
        return redirect(url_for("login"))
    if not is_staff(user):
        return redirect(url_for("home"))

    return render_admin(user)


@app.route("/admin/delete", methods=["POST"])
def admin_delete():
    """ลบคนตามสิทธิ์: แอดมินลบได้แค่ user, เจ้าของลบได้ทั้ง user และแอดมิน"""
    user = current_user()
    if user is None or not is_staff(user):
        return redirect(url_for("login"))

    target_id = request.form.get("user_id", type=int)
    target = get_user_by_id(target_id) if target_id else None
    if target is None:
        return redirect(url_for("admin"))
    if target["id"] == user["id"]:
        return render_admin(user, error="ลบตัวเองไม่ได้")
    if target["role"] == "super":
        return render_admin(user, error="ลบเจ้าของระบบไม่ได้")
    if user["role"] == "admin" and target["role"] != "user":
        return render_admin(user, error="แอดมินลบได้แค่ผู้ใช้ธรรมดา")

    delete_user(target_id)
    return redirect(url_for("admin"))


@app.route("/admin/role", methods=["POST"])
def admin_toggle_role():
    """เจ้าของเท่านั้นที่ตั้ง/ถอดแอดมิน — สร้างเจ้าของคนใหม่จากฟอร์มไม่ได้"""
    user = current_user()
    if user is None:
        return redirect(url_for("login"))
    if not is_super(user):
        return redirect(url_for("admin") if is_staff(user) else url_for("home"))

    target_id = request.form.get("user_id", type=int)
    new_role = request.form.get("role")
    target = get_user_by_id(target_id) if target_id else None
    if target is None or target["id"] == user["id"] or target["role"] == "super":
        return redirect(url_for("admin"))

    update_user_role(target_id, new_role)
    return redirect(url_for("admin"))


if __name__ == "__main__":
    init_db()
    # host 0.0.0.0 ไว้ให้เครื่องอื่นในแลนเปิดดูได้ทีหลัง
    app.run(host="0.0.0.0", port=5000, debug=True)
