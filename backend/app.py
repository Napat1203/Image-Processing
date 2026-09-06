import sys
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.db import (
    init_db,
    get_user_by_username,
    create_user,
)

from ai.process import process


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserIn(BaseModel):
    username: str
    password: str


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/login")
def api_login(body: UserIn):
    username = (body.username or "").strip()

    user = get_user_by_username(username)

    if user is None or user["password"] != body.password:
        return {
            "success": False,
            "message": "ชื่อหรือรหัสไม่ถูกต้อง",
        }

    return {
        "success": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
        },
    }


@app.post("/api/register")
def api_register(body: UserIn):
    username = (body.username or "").strip()
    password = body.password or ""

    if not username or not password:
        return {
            "success": False,
            "message": "กรอกชื่อกับรหัสก่อน",
        }

    if get_user_by_username(username):
        return {
            "success": False,
            "message": "ชื่อนี้มีคนใช้แล้ว",
        }

    if not create_user(username, password, role="user"):
        return {
            "success": False,
            "message": "สมัครไม่สำเร็จ",
        }

    return {
        "success": True
    }


@app.post("/api/upload")
async def upload(
    username: str = Form(...),
    password: str = Form(...),
    file: UploadFile = File(...),
):
    data = await file.read()

    return {
        "ok": True,
        "username": username,
        "password": password,
        "filename": file.filename,
        "size": len(data),
    }


@app.post("/api/process")
async def api_process(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    model: str = Form("stub"),
):
    data = await file.read()

    result = process(data, user_id)

    return {
        "status": result["status"],
        "note": result["note"],
        "model": model,
    }


if __name__ == "__main__":
    init_db()

    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )