from flask import Flask, redirect, render_template, request, session, url_for
import requests 

app = Flask(__name__)
# secret ชั่วคราวสำหรับ session — ยังไม่เน้นความปลอดภัย
app.secret_key = "restore-web-dev-not-secure"
# ต้องใส่เป็น url ของ backend
BACKEND_URL = "http://172.20.56.115:8000"

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
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=True
    )

