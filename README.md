# LUMA

เว็บแอปสำหรับสร้างและแก้ไขรูปภาพ พัฒนาด้วย Flask โดยส่งงานสร้างภาพ, inpaint และ ControlNet ไปประมวลผลผ่าน Stable Diffusion WebUI Forge ใช้ rembg สำหรับลบพื้นหลัง และประมวลผลการเปลี่ยนสีภายในเครื่อง

## ทำอะไรได้

- สมัครสมาชิกและเข้าสู่ระบบ โดยแบ่งบทบาทเป็น `user`, `admin` และ `super`
- สร้างภาพจาก prompt โดยแปลข้อความภาษาไทยเป็นภาษาอังกฤษก่อนส่งให้ Forge
- ลบพื้นหลังของรูปภาพ
- คลิกเลือกบริเวณในภาพเพื่อเปลี่ยนสี หรือสั่ง inpaint เฉพาะบริเวณนั้น
- สร้างภาพตามท่าทางจากรูปภาพหรือกล้อง

## สิ่งที่ต้องมี

- Python 3.12.x และ `virtualenv`
- [Stable Diffusion WebUI Forge](https://github.com/lllyasviel/stable-diffusion-webui-forge) โดยเปิด API ที่ `http://172.20.56.117:7860` (ต้องเป็น IP ของเครื่องที่รัน AI ในเครือข่าย LAN เดียวกัน) ด้วยอาร์กิวเมนต์ `--api` ถ้าเป็นในกรณีที่รันคนละเครื่องต้องเปิดพร้อมกับ `--listen` ด้วย
- โมเดล ControlNet `control_v11p_sd15_openpose` ใน Forge สำหรับฟังก์ชันสร้างภาพตามท่าทาง
- การสร้างภาพผ่าน Forge ต้องใช้ GPU ตามข้อกำหนดของเครื่อง ส่วนการลบพื้นหลังและการแปลภาษาไทยสามารถทำงานบน CPU ได้

## ติดตั้ง

```bash
git clone https://github.com/Napat1203/Image-Processing.git
cd Image-Processing
```

Windows (Command prompt):

```cmd 
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r ai/requirements.txt
pip install flask flask-cors
```

Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r ai/requirements.txt
pip install flask flask-cors
```

## ขั้นตอนการรัน

เปิด Forge ก่อน จากนั้นรันคำสั่งต่อไปนี้:

```bash
python backend/app.py
```

เปิดเว็บเบราว์เซอร์และไปที่ http://172.20.56.229:8000 (ต้องเป็น IP ของเครื่องที่รัน backend ในเครือข่าย LAN เดียวกัน)

เมื่อเริ่มใช้งานครั้งแรกที่รัน ระบบจะสร้างฐานข้อมูล `backend/users.db` และบัญชีเจ้าของ `super` / `super` รหัสผ่านเก็บบน SQLite แบบข้อความธรรมดา

กำหนดที่อยู่ Forge เปลี่ยนได้ด้วยตัวแปร `FORGE_URL` ค่าเริ่มต้นคือ `http://172.20.56.117:7860` โดยต้องใช้ `http` ไม่ใช่ `https`

ภาพที่สร้างจะมีขนาด  512×512 px. ใช้ 20 steps และ sampler `Euler a`

## nginx

ไม่จำเป็นต้องใช้ nginx สำหรับการรันแอปในเครื่อง ตัวอย่างการตั้งค่าอยู่ใน nginx.conf.example ซึ่งกำหนดให้ nginx รับการเชื่อมต่อที่พอร์ต 8080 และส่งต่อไปยังพอร์ต 8000 จำกัดขนาดไฟล์อัปโหลดไว้ที่ 20 MB และกำหนดเวลาอ่านข้อมูลสูงสุด 600 วินาที

## โครงสร้าง

```text
backend/    Flask, session, SQLite
frontend/   HTML, CSS, JavaScript
ai/         Forge, rembg, เปลี่ยนสี, inpaint, ControlNet
```

| หน้า | ใช้ทำอะไร |
| --- | --- |
| `/login` `/register` | เข้าสู่ระบบและสมัครสมาชิก |
| `/home` | หน้าหลัก |
| `/TXT2img` | สร้างภาพและแก้ไขภาพที่สร้างแล้ว |
| `/image` | อัปโหลดรูปแล้วลบพื้นหลัง เปลี่ยนสี หรือ inpaint |
| `/webcam` | ส่งท่าจากกล้องเข้า ControlNet |
| `/admin` | จัดการผู้ใช้ เฉพาะ `admin` และ `super` |
| `/about` | ข้อมูลเกี่ยวกับโปรเจกต์ |

## สมาชิก

- 6710301020 นางสาวพรพิรุณ ขามเทศ
- 6710301034 นางสาวณภัทร ภูสระล้ำ
- 6710301043 นายนที ผิวเกลี้ยง