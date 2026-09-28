import sys  # ใช้จัดการ Python path เพื่อให้ import ไฟล์ในโปรเจกต์ได้
from pathlib import Path  # ใช้จัดการ path ของโฟลเดอร์และไฟล์

from flask import (
    Flask,     # ใช้สร้าง Flask application
    request,   # ใช้รับข้อมูลจากผู้ใช้หรือ Frontend
    jsonify,   # ใช้ส่งข้อมูล JSON กลับ
    redirect,  # ใช้เปลี่ยนหน้า
    render_template,  # ใช้แสดง HTML template
    session,   # ใช้เก็บข้อมูลผู้ใช้ระหว่างการเข้าสู่ระบบ
    url_for,   # ใช้สร้าง URL ของ route
)

from flask_cors import CORS  # ใช้เปิด CORS ให้สามารถเรียก API ได้

ROOT = Path(__file__).resolve().parent.parent  # หาโฟลเดอร์หลักของโปรเจกต์ Image-Processing
sys.path.insert(0, str(ROOT))  # เพิ่มโฟลเดอร์หลักเข้าไปใน Python path


from backend.db import (   # import ฟังก์ชันที่ใช้ติดต่อ SQLite
    init_db,               # สร้างและเตรียม database
    get_user_by_username,  # ค้นหา user จาก username
    create_user,           # สร้าง user ใหม่
)

from ai.process import process  # import ฟังก์ชัน AI สำหรับประมวลผลรูปภาพ


app = Flask(   # สร้าง Flask application
    __name__,  # ระบุชื่อ application
    template_folder=str(ROOT / "frontend" / "templates"), # กำหนดตำแหน่ง HTML ของ Frontend
    static_folder=str(ROOT / "frontend" / "static"),      # กำหนดตำแหน่ง CSS และ JavaScript ของ Frontend
)

app.secret_key = "restore-web-dev-not-secure"  # ใช้เก็บข้อมูล session ของผู้ใช้

CORS(app)  # อนุญาตให้สามารถเรียก API ของ Backend ได้


# =========================================================
# ฟังก์ชันแสดงหน้าแรก
# =========================================================
@app.route("/")  # สร้าง route สำหรับหน้าแรก
def index():     # ฟังก์ชันเปลี่ยนไปยังหน้า Home
    return redirect(url_for("home"))  # เปลี่ยนไปหน้า Home


# =========================================================
# ฟังก์ชันตรวจสอบสถานะ Backend
# =========================================================
@app.route("/api/health", methods=["GET"])  # สร้าง API สำหรับตรวจสอบว่า Backend ทำงานอยู่หรือไม่
def health():  # ฟังก์ชันตรวจสอบสถานะ Backend
    return jsonify({"ok": True})  # ส่ง JSON กลับไปบอกว่า Backend ทำงานอยู่


# =========================================================
# ฟังก์ชัน Login
# =========================================================
@app.route("/login", methods=["GET", "POST"])  # สร้าง route สำหรับหน้า Login
def login():  # ฟังก์ชันรับข้อมูล Login จากหน้าเว็บ

    if request.method == "POST":  # ตรวจสอบว่าผู้ใช้ส่งข้อมูล Login มาหรือไม่

        username = (request.form.get("username") or "").strip()  # รับ username จากหน้าเว็บ
        password = request.form.get("password") or ""            # รับ password จากหน้าเว็บ

        user = get_user_by_username(username)  # ค้นหา user จาก SQLite

        if user is None or user["password"] != password:  # ตรวจสอบ username และ password
            return render_template(       # แสดงหน้า Login พร้อมข้อความแจ้งเตือน
                "login.html",             # ใช้หน้า login.html
                error="ชื่อหรือรหัสไม่ถูกต้อง"  # ส่งข้อความแจ้งเตือน
            )

        session["user"] = {    # เก็บข้อมูล user ลงใน session
            "id": user["id"],  # เก็บ id ของ user
            "username": user["username"],  # เก็บ username
            "role": user["role"],          # เก็บ role
        }

        return redirect(url_for("image"))  # Login สำเร็จแล้วไปหน้า Image

    return render_template("login.html")   # แสดงหน้า Login


# =========================================================
# ฟังก์ชันสมัครสมาชิก
# =========================================================
@app.route("/register", methods=["GET", "POST"])  # สร้าง route สำหรับหน้าสมัครสมาชิก
def register():  # ฟังก์ชันรับข้อมูลสมัครสมาชิก

    if request.method == "POST":  # ตรวจสอบว่าผู้ใช้ส่งข้อมูลสมัครสมาชิกมาหรือไม่

        username = (request.form.get("username") or "").strip()  # รับ username จากหน้าเว็บ
        password = request.form.get("password") or ""  # รับ password จากหน้าเว็บ

        if not username or not password:  # ตรวจสอบว่ากรอกข้อมูลครบหรือไม่
            return render_template(       # แสดงหน้า Register พร้อมข้อความแจ้งเตือน
                "register.html",          # ใช้หน้า register.html
                error="กรอกชื่อกับรหัสก่อน"   # ส่งข้อความแจ้งเตือน
            )

        if get_user_by_username(username):  # ตรวจสอบว่า username มีอยู่ใน database แล้วหรือไม่
            return render_template(         # แสดงหน้า Register พร้อมข้อความแจ้งเตือน
                "register.html",            # ใช้หน้า register.html
                error="ชื่อนี้มีคนใช้แล้ว"        # แจ้งว่า username ซ้ำ
            )

        if not create_user(username, password, role="user"):  # สร้าง user ใหม่ใน SQLite
            return render_template(  # แสดงหน้า Register พร้อมข้อความแจ้งเตือน
                "register.html",     # ใช้หน้า register.html
                error="สมัครไม่สำเร็จ"  # แจ้งว่าสมัครไม่สำเร็จ
            )

        return redirect(url_for("login"))    # สมัครสำเร็จแล้วกลับไปหน้า Login

    return render_template("register.html")  # แสดงหน้า Register


# =========================================================
# ฟังก์ชันแสดงหน้า Home
# =========================================================
@app.route("/home")  # สร้าง route สำหรับหน้า Home
def home():  # ฟังก์ชันแสดงหน้า Home

    user = session.get("user")  # อ่านข้อมูล user จาก session

    staff = False  # กำหนดค่าเริ่มต้นว่าไม่ใช่ staff

    if user:  # ตรวจสอบว่ามี user Login อยู่หรือไม่
        staff = user.get("role") in ["super", "admin"]  # ตรวจสอบ role ของ user

    return render_template(  # แสดงหน้า Home
        "home.html",         # ใช้หน้า home.html
        user=user,           # ส่งข้อมูล user ไปให้หน้าเว็บ
        staff=staff          # ส่งสถานะ staff ไปให้หน้าเว็บ
    )


# =========================================================
# ฟังก์ชัน Logout
# =========================================================
@app.route("/logout")  # สร้าง route สำหรับ Logout
def logout():  # ฟังก์ชันออกจากระบบ

    session.clear()  # ลบข้อมูล session ของผู้ใช้

    return redirect(url_for("login"))  # กลับไปหน้า Login


# =========================================================
# ฟังก์ชันแสดงหน้า Admin
# =========================================================
@app.route("/admin")  # สร้าง route สำหรับหน้า Admin
def admin():  # ฟังก์ชันแสดงหน้า Admin

    user = session.get("user")  # อ่านข้อมูล user จาก session

    if user is None:  # ตรวจสอบว่าผู้ใช้ Login หรือยัง
        return redirect(url_for("login"))  # ถ้ายังไม่ได้ Login ให้กลับไปหน้า Login

    if user.get("role") not in ["super", "admin"]:  # ตรวจสอบว่าเป็น super หรือ admin หรือไม่
        return redirect(url_for("image"))  # ถ้าไม่ใช่ให้กลับไปหน้า Image

    return render_template(  # แสดงหน้า Admin
        "admin.html",        # ใช้หน้า admin.html
        user=user,           # ส่งข้อมูล user ไปให้หน้าเว็บ
        users=[],            # ส่งข้อมูล users ตามโครงสร้างเดิม
        total=0,             # ส่งจำนวน user ตามโครงสร้างเดิม
        error=None,          # ไม่มี error
        owner=user.get("role") == "super"  # ตรวจสอบว่าเป็นเจ้าของระบบหรือไม่
    )


# =========================================================
# ฟังก์ชันรับข้อมูลและรูปภาพ
# =========================================================
@app.route("/api/upload", methods=["POST"])  # สร้าง API สำหรับรับ username password และรูปภาพ
def upload():  # ฟังก์ชันรับข้อมูลและรูปภาพจาก Frontend

    username = request.form.get("username", "")  # รับ username จาก Form
    password = request.form.get("password", "")  # รับ password จาก Form
    file = request.files.get("file")             # รับไฟล์รูปภาพจาก Form

    if file is None:      # ตรวจสอบว่ามีไฟล์ถูกส่งมาหรือไม่
        return jsonify({  # ส่งข้อความแจ้งเตือนกลับไป
            "ok": False,  # บอกว่าการรับข้อมูลไม่สำเร็จ
            "message": "ไม่พบไฟล์รูปภาพ",  # แจ้งว่าไม่มีรูปภาพ
        }), 400  # ส่ง HTTP status 400

    data = file.read()  # อ่านข้อมูลรูปภาพเป็น bytes

    return jsonify({    # ส่งข้อมูลที่ Backend ได้รับกลับไป
        "ok": True,     # บอกว่า Backend รับข้อมูลสำเร็จ
        "username": username,  # ส่ง username กลับไป
        "password": password,  # ส่ง password กลับไป
        "filename": file.filename,  # ส่งชื่อไฟล์กลับไป
        "size": len(data),     # ส่งขนาดไฟล์กลับไป
    })


# =========================================================
# ฟังก์ชันประมวลผลรูปภาพด้วย AI
# =========================================================
@app.route("/api/process", methods=["POST"])  # สร้าง API สำหรับส่งรูปไปประมวลผลด้วย AI
def api_process():  # ฟังก์ชันประมวลผลรูปภาพ

    file = request.files.get("file")                 # รับรูปภาพจาก Frontend
    user_id = request.form.get("user_id", type=int)  # รับ user_id และแปลงเป็น integer
    model = request.form.get("model", "stub")        # รับชื่อ AI model ถ้าไม่มีให้ใช้ stub

    if file is None:            # ตรวจสอบว่ามีรูปภาพหรือไม่
        return jsonify({        # ส่งข้อความแจ้งเตือนกลับไป
            "status": "error",  # ระบุว่าเกิดข้อผิดพลาด
            "note": "ไม่พบไฟล์รูปภาพ",  # แจ้งว่าไม่มีรูป
        }), 400  # ส่ง HTTP status 400

    if user_id is None:   # ตรวจสอบว่ามี user_id หรือไม่
        return jsonify({  # ส่งข้อความแจ้งเตือนกลับไป
            "status": "error",       # ระบุว่าเกิดข้อผิดพลาด
            "note": "ไม่พบ user_id",  # แจ้งว่าไม่มี user_id
        }), 400  # ส่ง HTTP status 400

    data = file.read()  # อ่านข้อมูลรูปภาพเป็น bytes

    result = process(data, user_id)  # ส่งรูปภาพและ user_id ไปให้ AI process

    return jsonify({                # ส่งผลลัพธ์จาก AI กลับไปให้ Frontend
        "status": result["status"], # ส่งสถานะการประมวลผล
        "note": result["note"],     # ส่งข้อความผลลัพธ์
        "model": model,             # ส่งชื่อ model กลับไป
    })


# =========================================================
# ฟังก์ชันรับรูปจากหน้าเว็บและส่งเข้า AI
# =========================================================
@app.route("/api/process-image", methods=["POST"])  # สร้าง route สำหรับรับรูปจากหน้าเว็บ
def process_image():  # ฟังก์ชันรับรูปจากหน้าเว็บและประมวลผลด้วย AI

    user = session.get("user")  # อ่านข้อมูล user จาก session

    if user is None:           # ตรวจสอบว่าผู้ใช้ Login แล้วหรือยัง
        return jsonify({       # ส่งข้อความแจ้งเตือนกลับไป
            "success": False,  # บอกว่าการทำงานไม่สำเร็จ
            "message": "กรุณาเข้าสู่ระบบ"  # แจ้งให้ Login ก่อน
        }), 401  # ส่ง HTTP status 401

    image = request.files.get("image")  # รับรูปภาพจากหน้าเว็บ
    model = request.form.get("model") or "stub"  # รับชื่อ AI model

    if not image:              # ตรวจสอบว่ามีรูปภาพหรือไม่
        return jsonify({       # ส่งข้อความแจ้งเตือนกลับไป
            "success": False,  # บอกว่าการทำงานไม่สำเร็จ
            "message": "กรุณาเลือกไฟล์รูปภาพ"  # แจ้งให้เลือกไฟล์
        }), 400  # ส่ง HTTP status 400

    data = image.read()  # อ่านข้อมูลรูปภาพเป็น bytes

    result = process(data, user["id"])  # ส่งรูปและ user_id ไปให้ AI โดยตรง

    if result.get("status") == "ok":  # ตรวจสอบว่า AI ประมวลผลสำเร็จหรือไม่
        return jsonify({      # ส่งผลลัพธ์กลับไปให้หน้าเว็บ
            "success": True,  # บอกว่าประมวลผลสำเร็จ
            "note": result.get("note")  # ส่งข้อความผลลัพธ์
        }), 200  # ส่ง HTTP status 200

    return jsonify({       # ส่งผลลัพธ์กรณีประมวลผลไม่สำเร็จ
        "success": False,  # บอกว่าประมวลผลไม่สำเร็จ
        "message": result.get("note", "เกิดข้อผิดพลาด")  # ส่งข้อความ error
    }), 500  # ส่ง HTTP status 500


# =========================================================
# ฟังก์ชันแสดงหน้า Image
# =========================================================
@app.route("/image")  # สร้าง route สำหรับหน้า Image
def image():  # ฟังก์ชันแสดงหน้า Image

    user = session.get("user")  # อ่านข้อมูล user จาก session

    if user is None:  # ตรวจสอบว่าผู้ใช้ Login แล้วหรือยัง
        return redirect(url_for("login"))  # ถ้ายังไม่ได้ Login ให้กลับไปหน้า Login

    return render_template("image.html", user=user)  # แสดงหน้า image.html


# =========================================================
# ฟังก์ชันแสดงหน้า Webcam
# =========================================================
@app.route("/webcam")  # สร้าง route สำหรับหน้า Webcam
def webcam():  # ฟังก์ชันแสดงหน้า Webcam

    user = session.get("user")  # อ่านข้อมูล user จาก session

    if user is None:  # ตรวจสอบว่าผู้ใช้ Login แล้วหรือยัง
        return redirect(url_for("login"))  # ถ้ายังไม่ได้ Login ให้กลับไปหน้า Login

    return render_template("webcam.html", user=user)  # แสดงหน้า webcam.html


# =========================================================
# ฟังก์ชันแสดงหน้า About
# =========================================================
@app.route("/about")  # สร้าง route สำหรับหน้า About
def about():  # ฟังก์ชันแสดงหน้า About

    user = session.get("user")  # อ่านข้อมูล user จาก session

    return render_template("about.html", user=user)  # แสดงหน้า about.html

# =========================================================
# ฟังก์ชันแสดงหน้า About
# =========================================================
@app.route("/TXT2img")
def txt2img():
    user = session.get("user")  # อ่านข้อมูล user จาก session
    
    if user is None:  # ตรวจสอบว่าผู้ใช้ Login แล้วหรือยัง
        return redirect(url_for("login"))  # ถ้ายังไม่ได้ Login ให้กลับไปหน้า Login
    
    return render_template("TXT2img.html", user=user)  # แสดงหน้า webcam.html


# =========================================================
# เริ่มต้น Backend Server
# =========================================================
if __name__ == "__main__":  # ตรวจสอบว่าไฟล์นี้ถูกเรียกให้ทำงานโดยตรงหรือไม่

    init_db()  # สร้างและเตรียม SQLite database ก่อนเริ่ม Server

    app.run(             # เริ่ม Flask development server
        host="0.0.0.0",  # เปิดให้เครื่องอื่นใน Network เข้ามาหา Backend ได้
        port=8000,       # ให้ Backend ทำงานที่ port 8000
        debug=True,      # เปิด debug mode เพื่อช่วยตรวจสอบ error ระหว่างพัฒนา
    )