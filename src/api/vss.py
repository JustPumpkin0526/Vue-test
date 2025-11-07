from fastapi import FastAPI, File, Form, UploadFile, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
from pydantic import BaseModel
from fastapi import Request
from openai import OpenAI
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
        response = requests.get(self.models_endpoint)
        json_data = self.check_response(response)
        return json_data["data"][0]["id"]  # get configured model name

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

    def query_video(self, file_id, query):
        body = {
            "id": file_id,
            "messages": [{"content": query, "role": "user"}],
            "model": self.model,
        }
        response = requests.post(self.query_endpoint, json=body)
        json_data = self.check_response(response)
        message_content = json_data["choices"][0]["message"]["content"]
        return message_content

@app.post("/vss-summarize")
async def gradio_api(
    file: UploadFile,
    prompt: str = Form(...),
    csprompt: str = Form(...),
    saprompt: str = Form(...),
    chunk_duration: int = Form(...),
    model: Optional[str] = Form(...),
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
    os.makedirs("./tmp", exist_ok=True)
    file_path = f"./tmp/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    vss = VSS("http://172.16.7.64:8100")
    video_id = vss.upload_video(file_path)

    result = vss.summarize_video(
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
    return {"summary": result}
