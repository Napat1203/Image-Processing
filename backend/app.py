import sys                # ใช้จัดการ Python path เพื่อให้ import ไฟล์ในโปรเจกต์ได้
from pathlib import Path  # ใช้จัดการ path ของโฟลเดอร์และไฟล์

from flask import Flask, request, jsonify  # import Flask และเครื่องมือรับ/ส่งข้อมูล HTTP
from flask_cors import CORS                # ใช้เปิด CORS ให้ Frontend สามารถเรียก Backend ได้

ROOT = Path(__file__).resolve().parent.parent  # หาโฟลเดอร์หลักของโปรเจกต์ Image-Processing
sys.path.insert(0, str(ROOT))                  # เพิ่มโฟลเดอร์หลักเข้าไปใน Python path

from backend.db import (   # import ฟังก์ชันที่ใช้ติดต่อ SQLite
    init_db,               # สร้างและเตรียม database
    get_user_by_username,  # ค้นหา user จาก username
    create_user,           # สร้าง user ใหม่
)

from ai.process import process  # import ฟังก์ชัน AI สำหรับประมวลผลรูปภาพ


app = Flask(__name__)  # สร้าง Flask application

CORS(app)  # อนุญาตให้ Frontend ที่มาจาก origin อื่นเรียก API ของ Backend ได้


# =========================================================
# ฟังก์ชันตรวจสอบสถานะ Backend
# =========================================================
@app.route("/api/health", methods=["GET"]) # สร้าง API สำหรับตรวจสอบว่า Backend ทำงานอยู่หรือไม่
def health():                              # ฟังก์ชันตรวจสอบสถานะ Backend
    return jsonify({"ok": True})           # ส่ง JSON กลับไปบอกว่า Backend ทำงานอยู่


# =========================================================
# ฟังก์ชัน Login
# =========================================================
@app.route("/api/login", methods=["POST"])  # สร้าง API สำหรับ Login
def api_login():                            # ฟังก์ชันตรวจสอบ username และ password

    body = request.get_json() or {}         # รับข้อมูล JSON ที่ Frontend ส่งมา

    username = (body.get("username") or "").strip()  # อ่าน username และตัดช่องว่างด้านหน้า/หลัง
    password = body.get("password") or ""            # อ่าน password จากข้อมูลที่ส่งมา

    user = get_user_by_username(username)   # ค้นหา user ใน SQLite จาก username

    if user is None or user["password"] != password:  # ตรวจสอบว่าไม่มี user หรือ password ไม่ตรงกัน
        return jsonify({                    # ส่งผลลัพธ์ Login ไม่สำเร็จกลับไป
            "success": False,               # บอกว่า Login ไม่สำเร็จ
            "message": "ชื่อหรือรหัสไม่ถูกต้อง",  # ข้อความแจ้งผู้ใช้
        })

    return jsonify({      # ส่งผลลัพธ์ Login สำเร็จกลับไป
        "success": True,  # บอกว่า Login สำเร็จ
        "user": {         # ส่งข้อมูล user กลับไปให้ Frontend
            "id": user["id"],             # ส่ง id ของ user
            "username": user["username"], # ส่ง username ของ user
            "role": user["role"],         # ส่ง role ของ user
        },
    })


# =========================================================
# ฟังก์ชันสมัครสมาชิก
# =========================================================
@app.route("/api/register", methods=["POST"]) # สร้าง API สำหรับสมัครสมาชิก
def api_register():  # ฟังก์ชันสมัครสมาชิก

    body = request.get_json() or {}  # รับข้อมูล JSON จาก Frontend

    username = (body.get("username") or "").strip() # อ่าน username และตัดช่องว่าง
    password = body.get("password") or ""           # อ่าน password

    if not username or not password:      # ตรวจสอบว่าผู้ใช้กรอกข้อมูลครบหรือไม่
        return jsonify({                  # ส่งข้อความแจ้งเตือนกลับไป
            "success": False,             # สมัครไม่สำเร็จ
            "message": "กรอกชื่อกับรหัสก่อน", # ข้อความแจ้งผู้ใช้
        })

    if get_user_by_username(username):  # ตรวจสอบว่า username นี้มีอยู่ใน database แล้วหรือไม่
        return jsonify({                # ส่งข้อความแจ้งเตือนกลับไป
            "success": False,           # สมัครไม่สำเร็จ
            "message": "ชื่อนี้มีคนใช้แล้ว",  # แจ้งว่า username ซ้ำ
        })

    if not create_user(username, password, role="user"):  # สร้าง user ใหม่ใน SQLite
        return jsonify({              # ส่งข้อความแจ้งเตือนกลับไป
            "success": False,         # สมัครไม่สำเร็จ
            "message": "สมัครไม่สำเร็จ", # ข้อความแจ้งผู้ใช้
        })

    return jsonify({     # ส่งผลลัพธ์กลับไปเมื่อสมัครสำเร็จ
        "success": True  # บอกว่า สมัครสมาชิกสำเร็จ
    })


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
        }), 400           # ส่ง HTTP status 400 เพราะข้อมูลไม่ครบ

    data = file.read()    # อ่านข้อมูลรูปภาพเป็น bytes

    return jsonify({          # ส่งข้อมูลที่ Backend ได้รับกลับไป
        "ok": True,           # บอกว่า Backend รับข้อมูลสำเร็จ
        "username": username,  # ส่ง username กลับไป
        "password": password,  # ส่ง password กลับไป
        "filename": file.filename,  # ส่งชื่อไฟล์กลับไป
        "size": len(data),          # ส่งขนาดไฟล์กลับไป
    })


# =========================================================
# ฟังก์ชันรับข้อมูลและรูปภาพ
# =========================================================
@app.route("/api/process", methods=["POST"])  # สร้าง API สำหรับส่งรูปไปประมวลผลด้วย AI
def api_process():  # ฟังก์ชันประมวลผลรูปภาพ

    file = request.files.get("file")  # รับรูปภาพจาก Frontend
    user_id = request.form.get("user_id", type=int)  # รับ user_id และแปลงเป็น integer
    model = request.form.get("model", "stub")        # รับชื่อ AI model ถ้าไม่มีให้ใช้ stub

    if file is None:      # ตรวจสอบว่ามีรูปภาพหรือไม่
        return jsonify({  # ส่งข้อความแจ้งเตือนกลับไป
            "status": "error",        # ระบุว่าเกิดข้อผิดพลาด
            "note": "ไม่พบไฟล์รูปภาพ",  # แจ้งว่าไม่มีรูป
        }), 400           # ส่ง HTTP status 400

    if user_id is None:   # ตรวจสอบว่ามี user_id หรือไม่
        return jsonify({  # ส่งข้อความแจ้งเตือนกลับไป
            "status": "error",       # ระบุว่าเกิดข้อผิดพลาด
            "note": "ไม่พบ user_id",  # แจ้งว่าไม่มี user_id
        }), 400           # ส่ง HTTP status 400

    data = file.read()    # อ่านข้อมูลรูปภาพเป็น bytes

    result = process(data, user_id)  # ส่งรูปภาพและ user_id ไปให้ AI process

    return jsonify({      # ส่งผลลัพธ์จาก AI กลับไปให้ Frontend
        "status": result["status"],  # ส่งสถานะการประมวลผล
        "note": result["note"],      # ส่งข้อความผลลัพธ์
        "model": model,              # ส่งชื่อ model กลับไป
    })


# =========================================================
# เริ่มต้น Backend Server
# =========================================================
if __name__ == "__main__":  # ตรวจสอบว่าไฟล์นี้ถูกเรียกให้ทำงานโดยตรงหรือไม่
    init_db()  # สร้างและเตรียม SQLite database ก่อนเริ่ม Server

    app.run(  # เริ่ม Flask development server
        host="0.0.0.0",  # เปิดให้เครื่องอื่นใน Network เข้ามาหา Backend ได้
        port=8000,       # ให้ Backend ทำงานที่ port 8000
        debug=True,      # เปิด debug mode เพื่อช่วยตรวจสอบ error ระหว่างพัฒนา
    )