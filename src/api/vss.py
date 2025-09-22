from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import requests

app = FastAPI()

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