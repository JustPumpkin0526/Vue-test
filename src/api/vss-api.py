from fastapi import FastAPI, File, Form, UploadFile, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
from pydantic import BaseModel
from fastapi import Request
from openai import OpenAI
import requests
import mariadb
import shutil
import json
import os
import re

app = FastAPI()

# VIA 서버 주소
VIA_SERVER_URL = "http://172.16.7.64:8100"  # 환경에 맞게 수정

class VSS:
    """Wrapper to call VSS REST APIs"""

    def __init__(self, host):

        self.host = host

        self.summarize_endpoint = self.host + "/summarize"
        self.query_endpoint = self.host + "/chat/completions"
        self.files_endpoint = self.host + "/files"
        self.models_endpoint = self.host + "/models"

        self.model = self.get_model()

        self.f_count = 0

    def check_response(self, response, json_format=True):
        print(f"Response Status Code: {response.status_code}")
        if response.status_code == 200:
            try:
                return response.json()
            except Exception:
                print("JSON decode error, returning text.")
                return response.text
        else:
            print("서버 에러:", response.status_code, response.text)
            return response.text

    def get_model(self):
        try:
            resp = requests.get(self.models_endpoint, timeout=10)
        except Exception as e:
            # Raise HTTPException so FastAPI returns a proper error response (and CORS headers)
            raise HTTPException(status_code=502, detail=f"Failed to reach VIA server for models: {e}")
        json_data = self.check_response(resp)
        try:
            return json_data["data"][0]["id"]  # get configured model name
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Invalid response from VIA /models: {e}")

    def upload_video(self, video_path):
        files = {"file": (f"file_{self.f_count}", open(video_path, "rb"))}
        data = {"purpose": "vision", "media_type": "video"}
        response = requests.post(self.files_endpoint, data=data, files=files)
        self.f_count += 1
        json_data = self.check_response(response)
        return json_data.get("id")  # return uploaded file id

    def summarize_video(self, file_id, prompt, cs_prompt, sa_prompt, chunk_duration, model, num_frames_per_chunk, frame_width, frame_height, top_k, top_p, temperature, max_new_tokens, seed, batch_size, rag_batch_size, rag_top_k, summarize_top_p, summarize_temperature, summarize_max_tokens, chat_top_p, chat_temperature, chat_max_tokens, notification_top_p, notification_temperature, notification_max_tokens):
        body = {
            "id": file_id,
            "prompt": prompt,
            "caption_summarization_prompt": cs_prompt,
            "summary_aggregation_prompt": sa_prompt,
            "model": self.model,
            "chunk_duration": chunk_duration,
            "temperature": temperature,
            "seed": seed,
            "max_tokens": max_new_tokens,
            "top_p": top_p,
            "top_k": top_k,
            "num_frames_per_chunk": num_frames_per_chunk,
            "vlm_input_width": frame_width,
            "vlm_input_height": frame_height,
            "summarize_top_p": summarize_top_p,
            "summarize_temperature": summarize_temperature,
            "summarize_max_tokens": summarize_max_tokens,
            "chat_top_p": chat_top_p,
            "chat_temperature": chat_temperature,
            "chat_max_tokens": chat_max_tokens,
            "notification_top_p": notification_top_p,
            "notification_temperature": notification_temperature,
            "notification_max_tokens": notification_max_tokens,
            "summarize_batch_size": batch_size,
            "rag_batch_size": rag_batch_size,
            "rag_top_k": rag_top_k,
            "enable_chat": True,
        }

        response = requests.post(self.summarize_endpoint, json=body)

        # check response
        json_data = self.check_response(response)
        if isinstance(json_data, dict) and "choices" in json_data:
            message_content = json_data["choices"][0]["message"]["content"]
            return message_content
        else:
            # JSON이 아니거나 에러일 때는 원본 텍스트 또는 에러 메시지 반환
            return json_data

    def query_video(self, video_id, model, chunk_size, temperature, seed, max_new_tokens, top_p, top_k, query):
        body = {
            "id": video_id,
            "model": model,
            "chunk_duration": chunk_size,
            "temperature": temperature,
            "seed": seed,
            "max_tokens": max_new_tokens,
            "top_p": top_p,
            "top_k": top_k,
            "stream": True,
            "stream_options": {"include_usage": True},
            "highlight": False,
        }
        body["messages"] = [{"content": str(query), "role": "user"}]
        response = requests.post(self.query_endpoint, json=body)
        json_data = self.check_response(response)
        message_content = json_data["choices"][0]["message"]["content"]
        return message_content

# 전역 VSS 클라이언트 (지연 초기화)
vss_client = None

@app.post("/vss-summarize")
async def vss_summarize(
    file: UploadFile,
    prompt: str = Form(...),
    csprompt: str = Form(...),
    saprompt: str = Form(...),
    chunk_duration: int = Form(...),
    num_frames_per_chunk: int = Form(...),
    frame_width: int = Form(...),
    frame_height: int = Form(...),
    top_k: int = Form(...),
    top_p: float = Form(...),
    temperature: float = Form(...),
    max_tokens: int = Form(...),
    seed: int = Form(...),
    batch_size: int = Form(...),
    rag_batch_size: int = Form(...),
    rag_top_k: int = Form(...),
    summary_top_p: float = Form(...),
    summary_temperature: float = Form(...),
    summary_max_tokens: int = Form(...),
    chat_top_p: float = Form(...),
    chat_temperature: float = Form(...),
    chat_max_tokens: int = Form(...),
    alert_top_p: float = Form(...),
    alert_temperature: float = Form(...),
    alert_max_tokens: int = Form(...),
):
    global vss_client
    if vss_client is None:
        vss_client = VSS(VIA_SERVER_URL)

    # GET models from VIA server (synchronous requests)
    try:
        resp = requests.get(VIA_SERVER_URL + "/models", timeout=10)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to contact VIA server: {e}")
    try:
        resp_json = resp.json()
    except Exception:
        resp_json = None
    if resp.status_code >= 400 or not resp_json:
        raise HTTPException(status_code=502, detail=f"VIA /models returned status {resp.status_code}")

    model = resp_json["data"][0]["id"]

    os.makedirs("./tmp", exist_ok=True)
    file_path = f"./tmp/{file.filename}"
    # 업로드용 임시 파일 실제 저장 (기존 누락으로 인해 FileNotFoundError / 빈 처리 발생 가능)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    video_id = vss_client.upload_video(file_path)

    result = vss_client.summarize_video(
        video_id,
        prompt,
        csprompt,
        saprompt,
        chunk_duration,
        model,
        num_frames_per_chunk,
        frame_width,
        frame_height,
        top_k,
        top_p,
        temperature,
        max_tokens,
        seed,
        batch_size,
        rag_batch_size,
        rag_top_k,
        summary_top_p,
        summary_temperature,
        summary_max_tokens,
        chat_top_p,
        chat_temperature,
        chat_max_tokens,
        alert_top_p,
        alert_temperature,
        alert_max_tokens,
    )
    return {"summary": result, "video_id": video_id}

@app.post("/vss-query")
def vss_query(
    video_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = None,
    chunk_size: int = Form(...),
    temperature: float = Form(...),
    seed: int = Form(...),
    max_new_tokens: int = Form(...),
    top_p: float = Form(...),
    top_k: int = Form(...),
    query: str = Form(...)
    ):
    
    # 전역 vss_client 사용 선언 (누락 시 UnboundLocalError 발생)
    global vss_client
    if vss_client is None:
        vss_client = VSS(VIA_SERVER_URL)
    
    resp = requests.get(VIA_SERVER_URL + "/models")
    resp_json = resp.json()
    if resp.status_code >= 400:
        return
    model = resp_json["data"][0]["id"]
    
    if file and not video_id:
        os.makedirs("./tmp", exist_ok=True)
        file_path = f"./tmp/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        video_id = vss_client.upload_video(file_path)
    elif not video_id:
        raise HTTPException(status_code=400, detail="video_id 또는 file 중 하나는 필요합니다.")\
        
    result = vss_client.query_video(video_id, model, chunk_size, temperature, seed, max_new_tokens, top_p, top_k, query)

    return {"summary": result, "video_id": video_id}

# 로그인용 모델
class LoginRequest(BaseModel):
    username: str
    password: str

# DB 연결 설정
conn = mariadb.connect(
    user="root",
    password="pass0001!",
    host="127.0.0.1",
    port=3306,
    database="vss"
)
cursor = conn.cursor()

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

