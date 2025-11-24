from fastapi import FastAPI, File, Form, UploadFile, Body, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
from pydantic import BaseModel
from fastapi import Request
import requests
import mariadb
import shutil
import json
import os
import random
from moviepy.video.io.VideoFileClip import VideoFileClip
from fastapi.logger import logger
import time

app = FastAPI()

# Serve generated clips as static files under /clips
os.makedirs("./clips", exist_ok=True)
app.mount("/clips", StaticFiles(directory="clips"), name="clips")

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

    #print(video_id)
    #print(prompt)
    #print(csprompt)
    #print(saprompt)
    #print(chunk_duration)
    #print(model)
    #print(num_frames_per_chunk)
    #print(frame_width)
    #print(frame_height)
    #print(top_k)
    #print(top_p)
    #print(temperature)
    #print(max_tokens)
    #print(seed)
    #print(batch_size)
    #print(rag_batch_size)
    #print(rag_top_k)
    #print(summary_top_p)
    #print(summary_temperature)
    #print(summary_max_tokens)
    #print(chat_top_p)
    #print(chat_temperature)
    #print(chat_max_tokens)
    #print(alert_top_p)
    #print(alert_temperature)
    #print(alert_max_tokens)

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

@app.post("/api/generate-clips")
async def generate_clips(
    request: Request,
    file: UploadFile = File(None),
    files: List[UploadFile] = File(None)
):
    os.makedirs("./clips", exist_ok=True)  # 클립 저장 디렉토리 생성
    # /clips 폴더 초기화 (기존 파일 삭제) - 요청 전체에서 단 한 번만 실행
    if getattr(request, "_clips_cleared", None) is None:
        for existing_file in os.listdir("./clips"):
            file_path = os.path.join("./clips", existing_file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    logger.info(f"Deleted existing clip: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {e}")
        setattr(request, "_clips_cleared", True)

    grouped_clips = []

    # Normalize inputs: support single file param or multiple files
    upload_list = []
    if files:
        upload_list.extend(files)
    if file:
        upload_list.append(file)

    if not upload_list:
        raise HTTPException(status_code=400, detail="No file provided")

    # Ensure tmp directory exists
    os.makedirs("./tmp", exist_ok=True)

    try:
        for upfile in upload_list:
            safe_filename = os.path.basename(upfile.filename)
            tmp_path = f"./tmp/{safe_filename}"
            # 업로드 파일을 새로 열어서 복사 (핸들 문제 방지)
            upfile.file.seek(0)
            with open(tmp_path, "wb") as buffer:
                shutil.copyfileobj(upfile.file, buffer)

            logger.info(f"Uploaded video saved to {tmp_path}")

            video_clips = []
            # MoviePy에 파일 경로(문자열)로 전달
            video = VideoFileClip(tmp_path)
            duration = video.duration or 0
            logger.info(f"Video duration: {duration} seconds for {tmp_path}")
            num_clips = random.randint(0, 3)
            logger.info(f"Number of clips to generate: {num_clips}")
            base_name, _ = os.path.splitext(safe_filename)
            for clip_index in range(num_clips):
                start_time = random.uniform(0, max(0, duration - 15))
                end_time = min(start_time + 15, duration)
                clip_filename = f"clip_{base_name}_{clip_index+1}.mp4"
                clip_path = os.path.join("./clips", clip_filename)
                try:
                    video.subclip(start_time, end_time).write_videofile(
                        clip_path,
                        codec="libx264",
                        audio = False,
                        verbose=False
                    )
                    logger.info(f"Clip saved: {clip_path}")
                    base = str(request.base_url).rstrip('/')
                    clip_url = f"{base}/clips/{clip_filename}"
                    video_clips.append({
                        "id": f"{base_name}_{clip_index}",
                        "title": clip_filename,
                        "url": clip_url,
                    })
                except Exception as e:
                    logger.error(f"Error generating clip {clip_filename}: {e}")
                time.sleep(0.5)
            video.close()
            del video

            grouped_clips.append({
                "video": safe_filename,
                "clips": video_clips
            })

    except Exception as e:
        logger.error(f"Error processing uploaded video(s): {e}")
        raise HTTPException(status_code=500, detail=f"Error processing uploaded video(s): {e}")

    print("All clips generated successfully.")
    print(f"Returned clips payload: {json.dumps({'clips': grouped_clips}, ensure_ascii=False)}")
    return JSONResponse(content={"clips": grouped_clips})

