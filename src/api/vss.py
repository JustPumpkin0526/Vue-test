from fastapi import FastAPI, File, Form, UploadFile, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
import mariadb
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 로그인용 모델
class LoginRequest(BaseModel):
    username: str
    password: str

# 로그인 엔드포인트
@app.post("/login")
def login(data: LoginRequest = Body(...)):
    cursor.execute(
        "SELECT PW FROM vss_user WHERE ID = ?",
        (data.username,)
    )
    row = cursor.fetchone()
    if row is None:
        return {"success": False, "message": "가입되지 않은 ID입니다."}
    db_pw = row[0]
    if db_pw != data.password:
        return {"success": False, "message": "비밀번호가 올바르지 않습니다."}
    return {"success": True}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 또는 ["*"]로 모든 출처 허용(개발용)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB 연결 설정
conn = mariadb.connect(
    user="root",
    password="pass0001!",
    host="127.0.0.1",
    port=3306,
    database="vss"
)
cursor = conn.cursor()

class User(BaseModel):
    username: str
    password: str
    email: str

@app.post("/register")
def register(user: User):
    try:
        cursor.execute(
            "INSERT INTO vss_user (ID, PW, EMAIL) VALUES (?, ?, ?)",
            (user.username, user.password, user.email)
        )
        conn.commit()
        return {"message": "회원가입 성공"}
    except mariadb.IntegrityError:
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자입니다.")


# CORS 설정 (Vue와 통신 가능하게)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영에서는 도메인 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# VIA 서버 주소
VIA_SERVER_URL = "http://172.16.7.64:8100"  # 환경에 맞게 수정

@app.post("/api/summarize")
async def summarize(file: UploadFile = File(...), prompt: str = Form(...)):
    # 1. VIA 서버에 파일 업로드
    files = {"file": (file.filename, await file.read(), file.content_type)}
    upload_resp = requests.post(f"{VIA_SERVER_URL}/files", files=files)
    if upload_resp.status_code != 200:
        return JSONResponse(status_code=500, content={"error": "VIA 서버 파일 업로드 실패"})
    media_id = upload_resp.json().get("id")
    if not media_id:
        return JSONResponse(status_code=500, content={"error": "media_id 없음"})

    # 2. VIA 서버에 요약 요청
    payload = {
        "media_id": media_id,
        "prompt": prompt,
    }
    summarize_resp = requests.post(f"{VIA_SERVER_URL}/summarize", json=payload)
    if summarize_resp.status_code != 200:
        return JSONResponse(status_code=500, content={"error": "VIA 서버 요약 실패"})
    result = summarize_resp.json()

    # 3. Vue로 결과 반환
    return JSONResponse(content={"summary": result.get("summary", result)})