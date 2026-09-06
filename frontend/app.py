from flask import Flask, jsonify, redirect, render_template, request, session, url_for
import requests 

app = Flask(__name__)
# secret ชั่วคราวสำหรับ session — ยังไม่เน้นความปลอดภัย
app.secret_key = "restore-web-dev-not-secure"
# ต้องใส่เป็น url ของ backend
BACKEND_URL = "http://172.20.56.115:8000" 
# BACKEND_URL = "http://127.0.0.1:8000" 

@app.route("/")
def index():
    """ถ้า login แล้วไป Home ถ้ายังไม่ login ไป Login"""
    if session.get("user"):
        return redirect(url_for("home"))

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """รับ Login จากหน้าเว็บ แล้วส่งไป Backend"""

    if request.method == "POST":

        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        try:
            # ส่งข้อมูลไป Backend REST API
            response = requests.post(
                f"{BACKEND_URL}/api/login",
                json={
                    "username": username,
                    "password": password
                },
                timeout=10
            )

            result = response.json()

            if result.get("success"):

                # เก็บข้อมูล User ที่ Backend ส่งกลับมา
                session["user"] = result["user"]

                return redirect(url_for("home"))

            return render_template(
                "login.html",
                error=result.get("message", "เข้าสู่ระบบไม่สำเร็จ")
            )

        except requests.RequestException:
            return render_template(
                "login.html",
                error="ไม่สามารถเชื่อมต่อ Backend ได้"
            )

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """รับข้อมูลสมัครสมาชิก แล้วส่งไป Backend"""

    if request.method == "POST":

        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        try:
            # ส่งข้อมูลไป Backend
            response = requests.post(
                f"{BACKEND_URL}/api/register",
                json={
                    "username": username,
                    "password": password
                },
                timeout=10
            )

            result = response.json()

            if result.get("success"):
                return redirect(url_for("login"))

            return render_template(
                "register.html",
                error=result.get("message", "สมัครสมาชิกไม่สำเร็จ")
            )

        except requests.RequestException:
            return render_template(
                "register.html",
                error="ไม่สามารถเชื่อมต่อ Backend ได้"
            )

    return render_template("register.html")


@app.route("/home")
def home():
    """แสดงหน้า Home"""

    user = session.get("user")

    if user is None:
        return redirect(url_for("login"))

    # ตรวจสอบว่าเป็น super หรือ admin หรือไม่
    staff = user.get("role") in ["super", "admin"]

    return render_template(
        "home.html",
        user=user,
        staff=staff
    )


@app.route("/logout")
def logout():
    """ออกจากระบบ"""

    session.clear()

    return redirect(url_for("login"))

@app.route("/admin")
def admin():
    """แสดงหน้า Admin"""

    user = session.get("user")

    if user is None:
        return redirect(url_for("login"))

    # ตรวจสอบว่าเป็น super หรือ admin หรือไม่
    if user.get("role") not in ["super", "admin"]:
        return redirect(url_for("home"))

    return render_template(
        "admin.html",
        user=user,
        users=[],
        total=0,
        error=None,
        owners=user.get("role") == "super"
    )

@app.route("/api/process-image", methods=["POST"])
def process_image():
    """รับไฟล์รูปภาพจากหน้าเว็บ แล้วส่งไป Backend"""

    user = session.get("user")

    if user is None:
        return jsonify({"success": False, "message": "กรุณาเข้าสู่ระบบ"}), 401

    image = request.files.get("image")
    model = request.form.get("model") or "stub"

    if not image:
        return jsonify({"success": False, "message": "กรุณาเลือกไฟล์รูปภาพ"}), 400

    try:
        # ส่งไฟล์ไป Backend
        response = requests.post(
            f"{BACKEND_URL}/api/process",
            files={
                "file": (
                    image.filename,
                    image.read(),
                    image.mimetype or "application/octet-stream"
                    )
                },
            data={
                "user_id": user["id"],
                "model": model
            },
            timeout=30
        )

        result = response.json()

        if result.get("status") == "ok":
            return jsonify({"success": True, "note": result.get("note")}), 200
        return jsonify({"success": False, "message": result.get("note", "เกิดข้อผิดพลาด")}), 500
    except requests.RequestException:
        return jsonify({"success": False, "message": "ไม่สามารถเชื่อมต่อ Backend ได้"}), 500
   
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

