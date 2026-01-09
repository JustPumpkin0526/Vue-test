from fastapi import FastAPI, File, Form, UploadFile, Body, HTTPException, Request, BackgroundTasks, Query
from moviepy.video.io.VideoFileClip import VideoFileClip
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from typing import Optional, List
from fastapi.logger import logger
from pydantic import BaseModel
import aiohttp
import mariadb
import random
import shutil
import json
import time
import os
import re
from pathlib import Path
import bcrypt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import asyncio
import aiofiles
import logging
from logging.handlers import TimedRotatingFileHandler

# ==================== 로깅 설정 ====================
# 로그 디렉토리 생성
log_dir = Path("./logs")
log_dir.mkdir(exist_ok=True)

# 오늘 날짜를 파일명에 포함
today = datetime.now().strftime('%Y-%m-%d')
log_file = log_dir / f"vss-api-{today}.log"
uvicorn_log_file = log_dir / f"uvicorn-{today}.log"
uvicorn_access_log_file = log_dir / f"uvicorn-access-{today}.log"

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        # 콘솔 출력
        logging.StreamHandler(),
        # 파일 출력 (매일 자정에 새 파일 생성, 30일 보관)
        TimedRotatingFileHandler(
            filename=str(log_file),
            when='midnight',  # 매일 자정
            interval=1,  # 1일마다
            backupCount=30,  # 30일치 보관
            encoding='utf-8',
            delay=False
        )
    ]
)

# FastAPI와 uvicorn 로거 설정
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_error_logger = logging.getLogger("uvicorn.error")

# uvicorn 로그도 파일에 기록
uvicorn_file_handler = TimedRotatingFileHandler(
    filename=str(uvicorn_log_file),
    when='midnight',
    interval=1,
    backupCount=30,
    encoding='utf-8',
    delay=False
)
uvicorn_file_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
)

uvicorn_access_file_handler = TimedRotatingFileHandler(
    filename=str(uvicorn_access_log_file),
    when='midnight',
    interval=1,
    backupCount=30,
    encoding='utf-8',
    delay=False
)
uvicorn_access_file_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
)

uvicorn_logger.addHandler(uvicorn_file_handler)
uvicorn_access_logger.addHandler(uvicorn_access_file_handler)
uvicorn_error_logger.addHandler(uvicorn_file_handler)

# .env 파일 지원 (python-dotenv가 설치되어 있는 경우)
try:
    from dotenv import load_dotenv
    # 현재 스크립트 위치 기준으로 .env 파일 찾기
    env_path = Path(__file__).parent.parent.parent / ".env"  # src/api/ -> src/ -> 프로젝트 루트
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f".env 파일을 로드했습니다: {env_path}")
    else:
        # 프로젝트 루트에 없으면 현재 디렉토리에서 찾기
        load_dotenv()
        logger.info("현재 디렉토리에서 .env 파일을 찾았습니다.")
except ImportError:
    logger.warning("python-dotenv가 설치되지 않았습니다. .env 파일을 사용하려면 'pip install python-dotenv'를 실행하세요.")
    logger.info("시스템 환경 변수를 사용합니다.")

app = FastAPI()

# Serve generated clips as static files under /clips
os.makedirs("./clips", exist_ok=True)
app.mount("/clips", StaticFiles(directory="clips"), name="clips")

# Serve uploaded videos as static files under /video-files (API 엔드포인트와 충돌 방지)
videos_dir = Path("./videos")
videos_dir.mkdir(exist_ok=True)
app.mount("/video-files", StaticFiles(directory=str(videos_dir.resolve())), name="video-files")

# Serve converted videos as static files under /converted-videos
converted_videos_dir = Path("./converted-videos")
converted_videos_dir.mkdir(exist_ok=True)
app.mount("/converted-videos", StaticFiles(directory=str(converted_videos_dir.resolve())), name="converted-videos")

# Serve profile images as static files under /profile-images
profile_images_dir = Path("./profile-images")
profile_images_dir.mkdir(exist_ok=True)
app.mount("/profile-images", StaticFiles(directory=str(profile_images_dir.resolve())), name="profile-images")

# Serve sample videos as static files under /sample
# 절대 경로를 사용하여 현재 스크립트 위치 기준으로 sample 폴더 찾기
import pathlib
current_dir = pathlib.Path(__file__).parent  # src/api/
# src/api/ -> src/ -> src/assets/sample
sample_dir = current_dir.parent / "assets" / "sample"
sample_dir = sample_dir.resolve()  # 절대 경로로 변환
os.makedirs(sample_dir, exist_ok=True)
logger.info(f"Serving sample videos from: {sample_dir}")

# sample.mp4 파일 존재 여부 확인
sample_file = sample_dir / "sample.mp4"
if sample_file.exists():
    logger.info(f"샘플 동영상을 찾았습니다. : {sample_file}")
else:
    logger.warning(f"샘플 동영상은 해당 경로에 없습니다. : {sample_file}")

    try:
        app.mount("/sample", StaticFiles(directory=str(sample_dir)), name="sample")
        logger.info(f"/sample 엔드포인트를 {sample_dir}에 성공적으로 마운트했습니다.")
    except Exception as e:
        logger.error(f"/sample 엔드포인트를 마운트하는데 실패했습니다. : {e}")

# ==================== 상수 정의 ====================
# API 설정
API_BASE_URL = os.getenv("API_BASE_URL", "http://172.16.15.69:8001")

# VIA 서버 설정
VIA_SERVER_URL = "http://172.16.7.64:8101"
VIA_MODEL_TIMEOUT = 10  # VIA 모델 조회 타임아웃 (초)
VIA_UPLOAD_TIMEOUT_MIN = 60  # 최소 업로드 타임아웃 (초)
VIA_UPLOAD_TIMEOUT_MAX = 600  # 최대 업로드 타임아웃 (초)
VIA_UPLOAD_TIMEOUT_PER_MB = 10  # 1MB당 타임아웃 (초)

# Ollama 설정
# 같은 서버에서 실행 중이면 localhost 사용, 다른 서버면 해당 IP 주소 사용
# 기본 포트는 11434입니다 (Ollama 기본 포트)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_TIMEOUT = 60  # Ollama API 타임아웃 (초)

# 파일 설정
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv'}
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
FILE_BUFFER_SIZE = 16 * 1024 * 1024  # 16MB (업로드 성능 최적화)
CLIP_CLEANUP_AGE = 86400  # 클립 파일 정리 기준 시간 (24시간, 초)

# 타임아웃 설정
DEFAULT_VIA_TARGET_RESPONSE_TIME = 2 * 60  # 초
DEFAULT_VIA_TARGET_USECASE_EVENT_DURATION = 10  # 초

# 정규식 패턴
EMAIL_REGEX = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
IP_PATTERN = r'^(\d{1,3}\.){3}\d{1,3}$'

# 이메일 설정
EMAIL_CODE_EXPIRY_MINUTES = 10

# VIA 서버 요약 기본 설정 (generate-clips용)
DEFAULT_SUMMARIZE_PROMPT = "You are a video monitoring system. Describe the events in this video and look for any anomalies. Start each sentence with the start and end timestamp of the event."
DEFAULT_CAPTION_SUMMARIZATION_PROMPT = "You will be given captions from sequential clips of a video. Aggregate captions in the format start_time:end_time:caption based on whether captions are related to one another or create a continuous scene."
DEFAULT_SUMMARY_AGGREGATION_PROMPT = "Based on the available information, generate a summary that captures the important events in the video. The summary should be organized chronologically and in logical sections. This should be a concise, yet descriptive summary of all the important events. The format should be intuitive and easy for a user to read and understand what happened. Format the output in Markdown so it can be displayed nicely. Timestamps are in seconds so please format them as SS.SSS"

# VIA 서버 요약 파라미터 기본값
DEFAULT_FRAME_WIDTH = 0
DEFAULT_FRAME_HEIGHT = 0
DEFAULT_TOP_K = 80
DEFAULT_TOP_P = 1.0
DEFAULT_TEMPERATURE = 0.4
DEFAULT_MAX_TOKENS = 512
DEFAULT_SEED = 1
DEFAULT_BATCH_SIZE = 6
DEFAULT_RAG_BATCH_SIZE = 1
DEFAULT_RAG_TOP_K = 5
DEFAULT_SUMMARIZE_TOP_P = 0.7
DEFAULT_SUMMARIZE_TEMPERATURE = 0.2
DEFAULT_SUMMARIZE_MAX_TOKENS = 2048
DEFAULT_CHAT_TOP_P = 0.7
DEFAULT_CHAT_TEMPERATURE = 0.2
DEFAULT_CHAT_MAX_TOKENS = 2048
DEFAULT_NOTIFICATION_TOP_P = 0.7
DEFAULT_NOTIFICATION_TEMPERATURE = 0.2
DEFAULT_NOTIFICATION_MAX_TOKENS = 2048
DEFAULT_ENABLE_AUDIO = True

# VIA 서버 질의(query) 기본 설정
DEFAULT_QUERY_TEMPERATURE = 0.3
DEFAULT_QUERY_SEED = 42
DEFAULT_QUERY_MAX_TOKENS = 1024  # VIA 서버는 최대 1024까지만 허용
DEFAULT_QUERY_TOP_P = 1.0
DEFAULT_QUERY_TOP_K = 80
DEFAULT_QUERY_TIMESTAMP_SUFFIX = " 장면의 시작 타임스탬프와 종료 타임스탬프를 추출하여 반드시 '시작시간-끝시간' 형태로만 출력해주세요. 타임스탬프 형식은 초 단위(예: 10.5-120.3) 또는 분:초 형식(예: 1:30-2:45)일 수 있습니다. 타임스탬프만 출력하고 다른 설명은 포함하지 마세요."

# 전역 변수
http_session: Optional[aiohttp.ClientSession] = None
vss_client = None

# ==================== 유틸리티 함수 ====================
async def get_session():
    """전역 aiohttp 세션 가져오기 또는 생성"""
    global http_session
    if http_session is None or http_session.closed:
        http_session = aiohttp.ClientSession()
    return http_session

async def ensure_vss_client():
    """VSS 클라이언트 초기화 (중복 초기화 방지)"""
    global vss_client
    if vss_client is None:
        vss_client = VSS(VIA_SERVER_URL)
        vss_client.model = await vss_client.get_model()
    return vss_client

async def get_via_model():
    """VIA 서버에서 모델 정보 가져오기"""
    session = await get_session()
    try:
        async with session.get(
            f"{VIA_SERVER_URL}/models",
            timeout=aiohttp.ClientTimeout(total=VIA_MODEL_TIMEOUT)
        ) as resp:
            if resp.status >= 400:
                raise HTTPException(status_code=502, detail=f"VIA /models returned status {resp.status}")
            try:
                resp_json = await resp.json()
            except Exception:
                raise HTTPException(status_code=502, detail="VIA /models returned invalid JSON")
            return resp_json["data"][0]["id"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to contact VIA server: {e}")

def validate_email(email: str) -> str:
    """이메일 형식 검증 및 정규화"""
    if not email or not email.strip():
        raise HTTPException(status_code=400, detail="이메일 주소를 입력해주세요.")
    email = email.strip().lower()
    if not re.match(EMAIL_REGEX, email):
        raise HTTPException(status_code=400, detail="올바른 이메일 형식이 아닙니다.")
    return email

def build_file_url(file_url: str) -> str:
    """파일 URL 생성 (API 베이스 URL 포함)"""
    if file_url.startswith('http'):
        return file_url
    return f"{API_BASE_URL}{file_url}"

async def create_summarize_prompt(user_prompt: str) -> str:
    """
    Ollama를 사용하여 요약 프롬프트 생성
    
    Args:
        user_prompt: 사용자가 입력한 프롬프트
    
    Returns:
        생성된 요약 프롬프트 (Ollama 실패 시 기본 프롬프트 반환)
    """
    try:
        # Ollama API 호출을 위한 프롬프트 구성
        ollama_prompt = f""" 사용자 질문: {user_prompt}
        사용자 질문을 아래 조건에 맞는 프롬프트로 수정해주세요.

        기본 프롬프트: {DEFAULT_SUMMARIZE_PROMPT}
        위 기본 프롬프트의 형태를 참고하여 사용자 질문을 기본 프롬프트의 형태처럼 변형시켜주세요.

        아래 조건에 맞는 형태를 유지해주세요.
        1. 시작 시간 - 종료 시간 형태의 타임스탬프를 출력하게 해주세요.
        2. 출력 결과는 영어여야 하며 문장의 형태로 출력해주세요.
        """
        
        # Ollama API 호출 (aiohttp 사용)
        session = await get_session()
        ollama_url = f"{OLLAMA_BASE_URL}/api/chat"
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": """You are a text generator.
                                Return ONLY the final prompt text.
                                Do NOT add any preface, explanation, or quotes.
                                Do NOT say things like "Here is ..." or "Sure"."""
                },
                {
                    "role": "user",
                    "content": ollama_prompt
                }
            ],
            "stream": False,
            "options": {
                "temperature": 0.6,  # 창의성과 일관성의 균형
                "num_predict": 1000  # 충분한 길이의 프롬프트 생성
            }
        }
        
        async with session.post(
            ollama_url,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=OLLAMA_TIMEOUT)
        ) as ollama_response:
            if ollama_response.status == 200:
                ollama_data = await ollama_response.json()
                generated_prompt = ollama_data.get("message", {}).get("content", "")
                print(f"generated_prompt: {generated_prompt}")
                if generated_prompt:
                    generated_prompt = generated_prompt.strip()
                    logger.info(f"Ollama를 사용하여 요약 프롬프트 생성 성공")
                    return generated_prompt
                else:
                    logger.warning("Ollama 응답에 content가 없습니다. 기본 프롬프트 사용")
            else:
                error_text = await ollama_response.text()
                logger.warning(f"Ollama API 호출 실패 (HTTP {ollama_response.status}): {error_text}")
    except aiohttp.ClientConnectorError as e:
        logger.warning(f"Ollama 서버에 연결할 수 없습니다: {e}")
        logger.info("Ollama가 실행 중인지 확인하세요: ollama serve")
    except Exception as e:
        logger.warning(f"Ollama를 사용한 프롬프트 생성 중 오류 발생: {e}")
    
    # Ollama 실패 시 기본 프롬프트와 사용자 프롬프트 결합
    return f"{DEFAULT_SUMMARIZE_PROMPT}\n\n사용자 요청: {user_prompt}"

async def build_query_prompt(prompt: str) -> str:
    """
    Ollama를 사용하여 프롬프트를 영어로 번역하고 query_video 함수 호출을 위한 프롬프트 생성
    
    Args:
        prompt: 사용자가 입력한 프롬프트
    
    Returns:
        영어로 번역된 프롬프트 (Ollama 실패 시 원본 프롬프트 반환)
    """
    try:
        # Ollama API 호출을 위한 프롬프트 구성
        ollama_prompt = f"""다음 프롬프트를 영어로 번역해주세요:
"{prompt}"

번역된 프롬프트만 출력하고 다른 설명이나 지시사항은 포함하지 마세요."""
        
        # Ollama API 호출 (aiohttp 사용)
        session = await get_session()
        ollama_url = f"{OLLAMA_BASE_URL}/api/chat"
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert translator. Translate the given prompt to English accurately and naturally. Output only the translated text without any additional explanations."
                },
                {
                    "role": "user",
                    "content": ollama_prompt
                }
            ],
            "stream": False,
            "options": {
                "temperature": 0.0,  # 번역은 정확성이 중요하므로 낮은 temperature
                "num_predict": 500  # 번역은 적은 토큰 수로 충분
            }
        }
        
        async with session.post(
            ollama_url,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=OLLAMA_TIMEOUT)
        ) as ollama_response:
            if ollama_response.status == 200:
                ollama_data = await ollama_response.json()
                translated_prompt = ollama_data.get("message", {}).get("content", "")
                print(f"translated_prompt: {translated_prompt}")
                if translated_prompt:
                    translated_prompt = translated_prompt.strip()
                    logger.info(f"Ollama를 사용하여 프롬프트 영어 번역 성공")
                    return f"{translated_prompt}"
                else:
                    logger.warning("Ollama 응답에 content가 없습니다. 원본 프롬프트 사용")
            else:
                error_text = await ollama_response.text()
                logger.warning(f"Ollama API 호출 실패 (HTTP {ollama_response.status}): {error_text}")
    except aiohttp.ClientConnectorError as e:
        logger.warning(f"Ollama 서버에 연결할 수 없습니다: {e}")
        logger.info("Ollama가 실행 중인지 확인하세요: ollama serve")
    except Exception as e:
        logger.warning(f"Ollama를 사용한 프롬프트 번역 중 오류 발생: {e}")
    
    # Ollama 실패 시 원본 프롬프트와 타임스탬프 서픽스 결합
    return f"{prompt} {DEFAULT_QUERY_TIMESTAMP_SUFFIX}"

def build_summarize_params(
    video_id: str,
    chunk_duration: int,
    model: str,
    prompt: str = DEFAULT_SUMMARIZE_PROMPT,
    cs_prompt: str = DEFAULT_CAPTION_SUMMARIZATION_PROMPT,
    sa_prompt: str = DEFAULT_SUMMARY_AGGREGATION_PROMPT,
    num_frames_per_chunk: Optional[int] = None,
    frame_width: int = DEFAULT_FRAME_WIDTH,
    frame_height: int = DEFAULT_FRAME_HEIGHT,
    top_k: int = DEFAULT_TOP_K,
    top_p: float = DEFAULT_TOP_P,
    temperature: float = DEFAULT_TEMPERATURE,
    max_new_tokens: int = DEFAULT_MAX_TOKENS,
    seed: int = DEFAULT_SEED,
    batch_size: int = DEFAULT_BATCH_SIZE,
    rag_batch_size: int = DEFAULT_RAG_BATCH_SIZE,
    rag_top_k: int = DEFAULT_RAG_TOP_K,
    summarize_top_p: float = DEFAULT_SUMMARIZE_TOP_P,
    summarize_temperature: float = DEFAULT_SUMMARIZE_TEMPERATURE,
    summarize_max_tokens: int = DEFAULT_SUMMARIZE_MAX_TOKENS,
    chat_top_p: float = DEFAULT_CHAT_TOP_P,
    chat_temperature: float = DEFAULT_CHAT_TEMPERATURE,
    chat_max_tokens: int = DEFAULT_CHAT_MAX_TOKENS,
    notification_top_p: float = DEFAULT_NOTIFICATION_TOP_P,
    notification_temperature: float = DEFAULT_NOTIFICATION_TEMPERATURE,
    notification_max_tokens: int = DEFAULT_NOTIFICATION_MAX_TOKENS,
    enable_audio: bool = DEFAULT_ENABLE_AUDIO
):
    """
    summarize_video 함수 호출을 위한 파라미터 튜플 생성
    
    Args:
        video_id: VIA 서버의 video_id
        chunk_duration: 청크 지속 시간
        model: 모델 ID
        num_frames_per_chunk: None이면 chunk_duration // 4로 자동 계산
        기타 파라미터: 기본값 사용 또는 커스텀 값 지정
    
    Returns:
        summarize_video 함수에 전달할 파라미터 튜플
    """
    if num_frames_per_chunk is None:
        num_frames_per_chunk = chunk_duration // 2
        if num_frames_per_chunk > 256:
            num_frames_per_chunk = 256
        if num_frames_per_chunk < 1:
            num_frames_per_chunk = 1
    return (
        video_id,
        prompt,
        cs_prompt,
        sa_prompt,
        chunk_duration,
        model,
        num_frames_per_chunk,
        frame_width,
        frame_height,
        top_k,
        top_p,
        temperature,
        max_new_tokens,
        seed,
        batch_size,
        rag_batch_size,
        rag_top_k,
        summarize_top_p,
        summarize_temperature,
        summarize_max_tokens,
        chat_top_p,
        chat_temperature,
        chat_max_tokens,
        notification_top_p,
        notification_temperature,
        notification_max_tokens,
        enable_audio
    )

def build_query_video_params(
    video_id: str,
    model: str,
    query: str,
    chunk_size: int,
    temperature: float = DEFAULT_QUERY_TEMPERATURE,
    seed: int = DEFAULT_QUERY_SEED,
    max_new_tokens: int = DEFAULT_QUERY_MAX_TOKENS,
    top_p: float = DEFAULT_QUERY_TOP_P,
    top_k: int = DEFAULT_QUERY_TOP_K
):
    """
    query_video 함수 호출을 위한 파라미터 튜플 생성
    
    Args:
        video_id: VIA 서버의 video_id
        model: 모델 ID
        query: 질문 텍스트
        chunk_size: 청크 크기
        temperature: 기본값 0.3
        seed: 기본값 42
        max_new_tokens: 기본값 1024 (VIA 서버 최대값)
        top_p: 기본값 1.0
        top_k: 기본값 80
    
    Returns:
        query_video 함수에 전달할 파라미터 튜플
    """
    return (
        video_id,
        model,
        chunk_size,
        temperature,
        seed,
        max_new_tokens,
        top_p,
        top_k,
        query
    )

# ==================== VSS API 클래스 ====================
class VSS:
    """Wrapper to call VSS REST APIs"""

    def __init__(self, host):
        self.host = host
        self.summarize_endpoint = self.host + "/summarize"
        self.query_endpoint = self.host + "/chat/completions"
        self.files_endpoint = self.host + "/files"
        self.models_endpoint = self.host + "/models"
        self.model = None
        self.f_count = 0

    async def check_response(self, response, json_format=True):
        print(f"Response Status Code: {response.status}")
        if response.status == 200:
            try:
                return await response.json()
            except Exception:
                print("JSON decode error, returning text.")
                return await response.text()
        else:
            text = await response.text()
            print("서버 에러:", response.status, text)
            return text

    async def get_model(self):
        session = await get_session()
        try:
            async with session.get(
                self.models_endpoint,
                timeout=aiohttp.ClientTimeout(total=VIA_MODEL_TIMEOUT)
            ) as resp:
                json_data = await self.check_response(resp)
                try:
                    return json_data["data"][0]["id"]
                except Exception as e:
                    raise HTTPException(status_code=502, detail=f"Invalid response from VIA /models: {e}")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to reach VIA server for models: {e}")

    async def upload_video(self, video_path):
        session = await get_session()
        data = aiohttp.FormData()
        
        file_handle = open(video_path, "rb")
        try:
            file_size = os.path.getsize(video_path)
            logger.info(f"Uploading video file: {video_path} (size: {file_size / (1024*1024):.2f} MB)")
            
            data.add_field("file", file_handle, filename=f"file_{self.f_count}")
            data.add_field("purpose", "vision")
            data.add_field("media_type", "video")
            
            # 파일 크기에 따라 동적 타임아웃 계산
            timeout_seconds = max(
                VIA_UPLOAD_TIMEOUT_MIN,
                min(VIA_UPLOAD_TIMEOUT_MAX, int(file_size / (1024 * 1024) * VIA_UPLOAD_TIMEOUT_PER_MB))
            )

            async with session.post(
                self.files_endpoint, 
                data=data,
                timeout=aiohttp.ClientTimeout(total=timeout_seconds)
            ) as response:
                self.f_count += 1
                json_data = await self.check_response(response)
                return json_data.get("id")  # return uploaded file id

        finally:
            # 파일 핸들 닫기
            file_handle.close()

    async def summarize_video(self, file_id, prompt, cs_prompt, sa_prompt, chunk_duration, model, num_frames_per_chunk, frame_width, frame_height, top_k, top_p, temperature, max_new_tokens, seed, batch_size, rag_batch_size, rag_top_k, summarize_top_p, summarize_temperature, summarize_max_tokens, chat_top_p, chat_temperature, chat_max_tokens, notification_top_p, notification_temperature, notification_max_tokens, enable_audio):
        body = {
            "id": file_id,
            "prompt": prompt,
            "caption_summarization_prompt": cs_prompt,
            "summary_aggregation_prompt": sa_prompt,
            "model": model,
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
            "enable_audio": enable_audio,
        }

        session = await get_session()
        async with session.post(self.summarize_endpoint, json=body) as response:
            # 에러 응답 처리
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"VIA 서버 summarize_video 오류 (HTTP {response.status}): {error_text}")
                
                # GStreamer 에러인 경우 더 명확한 메시지 제공
                if "gst-stream-error" in error_text or "qtdemux" in error_text or "not-negotiated" in error_text:
                    error_msg = (
                        "동영상 파일 처리 중 오류가 발생했습니다. "
                        "가능한 원인:\n"
                        "1. 손상된 동영상 파일\n"
                        "2. 지원하지 않는 코덱 또는 포맷\n"
                        "3. 파일이 완전히 업로드되지 않음\n"
                        "4. 파일 메타데이터 문제\n\n"
                        f"VIA 서버 오류: {error_text}"
                    )
                    raise HTTPException(status_code=500, detail=error_msg)
                else:
                    raise HTTPException(status_code=response.status, detail=f"VIA 서버 summarize_video 오류: {error_text}")
            
            # check response
            json_data = await self.check_response(response)
            if isinstance(json_data, dict) and "choices" in json_data:
                message_content = json_data["choices"][0]["message"]["content"]
                return message_content
            else:
                # JSON이 아니거나 에러일 때는 원본 텍스트 또는 에러 메시지 반환
                return json_data

    async def list_files(self, purpose: str = "vision"):
        """
        VIA 서버에서 파일 목록 조회
        
        Args:
            purpose: 파일 목적 (기본값: "vision")
        
        Returns:
            파일 목록 (ListFilesResponse 형식)
        """
        session = await get_session()
        try:
            async with session.get(
                self.files_endpoint,
                params={"purpose": purpose},
                timeout=aiohttp.ClientTimeout(total=VIA_MODEL_TIMEOUT)
            ) as response:
                json_data = await self.check_response(response)
                
                # 오류 응답 처리
                if response.status != 200:
                    error_msg = json_data if isinstance(json_data, str) else str(json_data)
                    raise HTTPException(status_code=response.status, detail=f"VIA 서버 파일 목록 조회 오류: {error_msg}")
                
                # 정상 응답 처리
                if isinstance(json_data, dict) and "data" in json_data:
                    return json_data
                else:
                    raise HTTPException(status_code=502, detail=f"VIA 서버 응답 형식 오류: {json_data}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"VIA 서버 파일 목록 조회 실패: {e}")
            raise HTTPException(status_code=502, detail=f"VIA 서버 파일 목록 조회 실패: {str(e)}")

    async def query_video(self, video_id, model, chunk_size, temperature, seed, max_new_tokens, top_p, top_k, query):
        
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
        session = await get_session()
        async with session.post(self.query_endpoint, json=body) as response:
            json_data = await self.check_response(response)
            
            # 오류 응답 처리
            if response.status != 200:
                error_msg = json_data if isinstance(json_data, str) else str(json_data)
                raise HTTPException(status_code=response.status, detail=f"VIA 서버 query_video 오류: {error_msg}")
            
            # 정상 응답 처리
            if isinstance(json_data, dict) and "choices" in json_data:
                message_content = json_data["choices"][0]["message"]["content"]
                return message_content
            else:
                raise HTTPException(status_code=502, detail=f"VIA 서버 응답 형식 오류: {json_data}")

# CHUNK_SIZES 정의 (튜플 리스트 형식: (label, value))
CHUNK_SIZES = [
    ("0초", 0),
    ("5초", 5),
    ("10초", 10),
    ("20초", 20),
    ("30초", 30),
    ("60초", 60),
    ("120초", 120),
    ("300초", 300),
    ("600초", 600),
    ("1200초", 1200),
    ("1800초", 1800),
]

def get_closest_chunk_size(CHUNK_SIZES, x):
    """
    Returns the integer value from CHUNK_SIZES that is closest to x.

    Args:
        CHUNK_SIZES (list of tuples): A list of tuples containing chunk size labels and values.
        x (int): The target value to find the closest chunk size to.

    Returns:
        int: The integer value from CHUNK_SIZES that is closest to x.
    """
    _, values = zip(*CHUNK_SIZES)  # extract just the values from CHUNK_SIZES
    closest_value = min(values, key=lambda v: abs(v - x))  # find the value closest to x
    return closest_value

async def get_recommended_chunk_size(video_length):
    """동영상 길이에 따른 추천 chunk_size 계산"""
    recommended_chunk_size = 0

    try:
        session = await get_session()
        async with session.post(
            f"{VIA_SERVER_URL}/recommended_config",
            json={
                "video_length": int(video_length),
                "target_response_time": int(DEFAULT_VIA_TARGET_RESPONSE_TIME),
                "usecase_event_duration": int(DEFAULT_VIA_TARGET_USECASE_EVENT_DURATION),
            },
            timeout=aiohttp.ClientTimeout(total=VIA_MODEL_TIMEOUT)
        ) as response:
            if response.status < 400:
                # Success response from API:
                resp_json = await response.json()
                recommended_chunk_size = int(resp_json.get("chunk_size", 0))
    except Exception as e:
        logger.warning(f"Failed to get recommended chunk size from backend: {e}")
    
    if recommended_chunk_size == 0:
        # API fail to provide non-zero chunk size
        # Choose the largest chunk-size in favor of quick VIA execution
        recommended_chunk_size = video_length
    
    return get_closest_chunk_size(CHUNK_SIZES, recommended_chunk_size)

# 추천 chunk_size 요청용 모델
class RecommendedChunkSizeRequest(BaseModel):
    video_length: float

@app.post("/get-recommended-chunk-size")
async def get_recommended_chunk_size_endpoint(request: RecommendedChunkSizeRequest):
    """
    동영상 길이를 받아서 추천 chunk_size를 반환하는 엔드포인트
    """
    try:
        recommended_chunk_size = await get_recommended_chunk_size(request.video_length)
        return {"recommended_chunk_size": recommended_chunk_size, "video_length": request.video_length}
    except Exception as e:
        logger.error(f"Error getting recommended chunk size: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting recommended chunk size: {e}")

# ==================== 타임스탬프 파싱 함수 ====================
def parse_timestamps(timestamp_text, video_duration):
    """
    타임스탬프 텍스트에서 시간 구간을 파싱하여 (start_time, end_time) 튜플 리스트를 반환합니다.
    
    지원 형식:
    - 초 단위: 10.5, 120.3
    - 분:초 형식: 1:30, 2:45
    - 범위: 10.5-15.3, 1:30-2:45, 10.5~15.3
    - 여러 타임스탬프: "10.5, 20.3, 30.1" 또는 "1:30, 2:45"
    
    타임스탬프는 짝으로 처리되며, 첫 번째 타임스탬프가 시작 시간, 두 번째 타임스탬프가 끝 시간이 됩니다.
    타임스탬프가 명시적으로 주어진 경우 실제 범위를 그대로 사용합니다.
    
    Args:
        timestamp_text (str): 타임스탬프가 포함된 텍스트
        video_duration (float): 동영상 전체 길이 (초)
    
    Returns:
        List[tuple]: [(start_time, end_time), ...] 리스트. 타임스탬프가 명시된 경우 실제 범위를 사용.
    """
    if not timestamp_text or not isinstance(timestamp_text, str):
        return []
    
    timestamps = []
    
    # 분:초 형식을 초로 변환하는 함수
    def parse_time_to_seconds(time_str):
        time_str = time_str.strip()
        # 분:초 형식인지 확인
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:
                try:
                    minutes = float(parts[0])
                    seconds = float(parts[1])
                    return minutes * 60 + seconds
                except ValueError:
                    return None
        # 초 단위 형식
        try:
            return float(time_str)
        except ValueError:
            return None
    
    # 타임스탬프 텍스트에서 숫자와 범위 패턴 찾기
    # 패턴: 숫자(초 또는 분:초) 또는 범위(숫자-숫자, 숫자~숫자)
    
    # 1. 범위 패턴 찾기 (예: 10.5-15.3, 1:30-2:45)
    range_pattern = r'(\d+(?:\.\d+)?(?::\d+(?:\.\d+)?)?)\s*[-~]\s*(\d+(?:\.\d+)?(?::\d+(?:\.\d+)?)?)'
    range_timestamps = []
    for match in re.finditer(range_pattern, timestamp_text):
        start_str = match.group(1)
        end_str = match.group(2)
        start_time = parse_time_to_seconds(start_str)
        end_time = parse_time_to_seconds(end_str)
        if start_time is not None and end_time is not None:
            start_time = max(0, min(start_time, video_duration))
            end_time = max(start_time, min(end_time, video_duration))
            # 범위 패턴으로 명시된 경우 실제 범위를 그대로 사용 (15초 제한 없음)
            range_timestamps.append((start_time, end_time))
    
    # 2. 단일 타임스탬프 찾기 (범위에 포함되지 않은 것들)
    # 이미 범위로 처리된 부분을 제외하고 나머지에서 찾기
    processed_text = re.sub(range_pattern, '', timestamp_text)
    
    # 숫자 패턴 찾기 (초 단위 또는 분:초)
    number_pattern = r'\d+(?:\.\d+)?(?::\d+(?:\.\d+)?)?'
    single_timestamps = []
    for match in re.finditer(number_pattern, processed_text):
        time_str = match.group(0)
        time_seconds = parse_time_to_seconds(time_str)
        if time_seconds is not None:
            time_seconds = max(0, min(time_seconds, video_duration))
            single_timestamps.append(time_seconds)
    
    # 범위 패턴으로 찾은 타임스탬프는 그대로 사용
    timestamps.extend(range_timestamps)
    
    # 단일 타임스탬프는 짝으로 묶어서 처리
    # 첫 번째 타임스탬프가 시작 시간, 두 번째 타임스탬프가 끝 시간
    for i in range(0, len(single_timestamps) - 1, 2):
        start_time = single_timestamps[i]
        end_time = single_timestamps[i + 1]
        # 타임스탬프가 짝으로 명시된 경우 실제 범위를 그대로 사용 (15초 제한 없음)
        timestamps.append((start_time, end_time))
    
    # 중복 제거 및 정렬
    timestamps = sorted(set(timestamps), key=lambda x: x[0])
    
    # 겹치는 구간 병합 (5초 이내로 가까운 구간)
    merged = []
    for start, end in timestamps:
        if merged and start - merged[-1][1] < 5:
            # 이전 구간과 가까우면 병합 (실제 범위 유지)
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            # 실제 범위를 그대로 사용
            merged.append((start, end))
    
    logger.info(f"파싱된 타임스탬프: {merged}")
    return merged

async def remove_all_media(session: aiohttp.ClientSession, media_ids):
    """
    VIA 서버에서 여러 미디어 파일을 삭제하는 함수
    vss-summarize.py의 remove_all_media 함수를 참고하여 구현
    """
    for media_id in media_ids:
        try:
            async with session.delete(VIA_SERVER_URL + "/files/" + media_id) as resp:
                if resp.status >= 400:
                    logger.warning(f"Failed to delete media {media_id}: HTTP {resp.status}")
                else:
                    logger.info(f"Successfully deleted media {media_id}")
        except Exception as e:
            logger.error(f"Error deleting media {media_id}: {e}")

# 미디어 삭제 요청용 모델
class RemoveMediaRequest(BaseModel):
    media_ids: List[str]

@app.post("/remove-media")
async def remove_media_endpoint(request: RemoveMediaRequest):
    """
    VIA 서버에서 미디어 파일들을 삭제하는 엔드포인트
    """
    try:
        session = await get_session()
        await remove_all_media(session, request.media_ids)
        return {"success": True, "message": f"Deleted {len(request.media_ids)} media file(s)"}
    except Exception as e:
        logger.error(f"Error removing media: {e}")
        raise HTTPException(status_code=500, detail=f"Error removing media: {e}")

# ==================== 장면 검색 결과 클립 생성 ====================
@app.post("/generate-clips")
async def generate_clips(
    request: Request,
    files: List[UploadFile] = File(None),
    prompt: str = Form(...),
    user_id: Optional[str] = Form(None),
    video_ids: Optional[str] = Form(None)  # JSON 문자열로 전달: {"filename1": video_id1, "filename2": video_id2}
):
    os.makedirs("./clips", exist_ok=True)
    
    # 오래된 클립 파일 정리
    try:
        current_time = time.time()
        for existing_file in os.listdir("./clips"):
            file_path = os.path.join("./clips", existing_file)
            try:
                if os.path.isfile(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    if current_time - file_mtime > CLIP_CLEANUP_AGE:
                        os.remove(file_path)
                        logger.info(f"Deleted old clip: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting old clip {file_path}: {e}")
    except Exception as e:
        logger.warning(f"Error cleaning old clips: {e}")

    grouped_clips = []
    global vss_client

    # Normalize inputs: support single file param or multiple files
    upload_list = []
    if files:
        upload_list.extend(files)

    if not upload_list:
        raise HTTPException(status_code=400, detail="No file provided")

    # Ensure tmp directory exists
    os.makedirs("./tmp", exist_ok=True)
    
    try:
        # video_ids 파싱 (JSON 문자열)
        video_id_map = {}
        if video_ids and user_id:
            try:
                video_id_map = json.loads(video_ids) if isinstance(video_ids, str) else video_ids
            except:
                video_id_map = {}
        
        for upfile in upload_list:
            file_path = os.path.basename(upfile.filename)
            tmp_path = f"./tmp/{file_path}"

            await ensure_vss_client()
            model = await get_via_model()

            os.makedirs("./tmp", exist_ok=True)
            # 업로드용 임시 파일 실제 저장
            with open(tmp_path, "wb") as buffer:
                shutil.copyfileobj(upfile.file, buffer)

            logger.info(f"Uploaded video saved to {tmp_path}")

            # video_ids에서 내부 DB ID 가져오기 (VIA 서버의 video_id로 변환 필요)
            video_id = None
            db_internal_id = None
            if video_id_map:
                # 파일명으로 내부 DB ID 찾기
                db_internal_id = video_id_map.get(file_path) or video_id_map.get(upfile.filename)
                if db_internal_id:
                    try:
                        # 내부 DB ID로 vss_videos 테이블에서 VIDEO_ID (VIA 서버의 video_id) 조회
                        cursor.execute(
                            "SELECT VIDEO_ID FROM vss_videos WHERE ID = ? AND USER_ID = ?",
                            (db_internal_id, user_id)
                        )
                        video_row = cursor.fetchone()
                        if video_row and video_row[0]:
                            video_id = video_row[0]  # VIA 서버의 video_id
                            logger.info(f"video_ids에서 내부 DB ID {db_internal_id}로 VIDEO_ID {video_id} 조회 성공 (파일명: {file_path})")
                        else:
                            logger.warning(f"내부 DB ID {db_internal_id}에 해당하는 VIDEO_ID를 찾을 수 없습니다.")
                    except Exception as e:
                        logger.warning(f"VIDEO_ID 조회 중 오류: {e}")
            
            # video_id가 없으면 VIA 서버에 업로드하여 video_id 얻기
            if not video_id:
                video_id = await vss_client.upload_video(tmp_path)
                logger.info(f"VIA 서버에 업로드하여 video_id 획득: {video_id}")

            video_clips = []
            # MoviePy에 파일 경로(문자열)로 전달
            video = VideoFileClip(tmp_path)
            duration = video.duration or 0
            logger.info(f"Video duration: {duration} seconds for {tmp_path}")
            
            # chunk_duration 계산
            chunk_duration = await get_recommended_chunk_size(duration)

            # DB에서 요약 결과 확인 (user_id와 video_id가 있는 경우)
            has_stored_summary = False
            if user_id and video_id:
                try:
                    # VIDEO_ID (VIA 서버의 video_id)로 요약 결과 확인
                    cursor.execute(
                        """SELECT ID FROM vss_summaries 
                           WHERE VIDEO_ID = ? AND USER_ID = ?""",
                        (video_id, user_id)
                    )
                    if cursor.fetchone():
                        has_stored_summary = True
                        print(f"저장된 요약 결과 발견: VIDEO_ID {video_id}, summarize_video 건너뛰기")
                except Exception as e:
                    print(f"요약 결과 확인 중 오류: {e}")

            # 요약 파라미터 준비 (Ollama를 사용하여 프롬프트 생성)
            AI_prompt = await create_summarize_prompt(prompt)
            
            # 저장된 요약이 있으면 PROMPT를 비교하여 프롬프트가 변경되었는지 확인
            if has_stored_summary and user_id and video_id:
                try:
                    cursor.execute(
                        """SELECT PROMPT FROM vss_summaries WHERE VIDEO_ID = ? AND USER_ID = ?;""",
                        (video_id, user_id)
                    )
                    summary_row = cursor.fetchone()
                    if summary_row and summary_row[0]:
                        # SELECT PROMPT만 했으므로 인덱스는 [0]만 존재
                        stored_prompt = summary_row[0]
                        print(f"저장된 PROMPT: {stored_prompt}")
                        print(f"현재 AI_prompt: {AI_prompt}")
                        # 저장된 PROMPT와 현재 AI_prompt를 비교
                        if stored_prompt.strip() == AI_prompt.strip():
                            # 프롬프트가 같으면 저장된 요약 사용
                            has_stored_summary = True
                            print(f"프롬프트가 동일하여 저장된 요약을 사용합니다. (VIDEO_ID: {video_id})")
                        else:
                            # 프롬프트가 다르면 요약을 다시 수행해야 함
                            has_stored_summary = False
                            print(f"프롬프트가 변경되어 요약을 다시 수행합니다. (VIDEO_ID: {video_id})")
                    else:
                        # PROMPT가 없거나 NULL인 경우 요약을 다시 수행
                        has_stored_summary = False
                        print(f"저장된 PROMPT가 없어 요약을 다시 수행합니다. (VIDEO_ID: {video_id})")
                except Exception as e:
                    logger.warning(f"PROMPT 조회 중 오류: {e}")
                    # 오류 발생 시 요약을 다시 수행
                    has_stored_summary = False

            if not has_stored_summary:
                summarize_params = build_summarize_params(
                    video_id=video_id,
                    chunk_duration=chunk_duration,
                    model=model,
                    prompt=AI_prompt,  # Ollama로 생성된 프롬프트 사용
                    temperature=0,
                    summarize_temperature=0,
                    chat_temperature=0,
                    notification_temperature=0
                )
                result = await vss_client.summarize_video(*summarize_params)
                
                # 요약 결과를 DB에 저장
                if user_id and video_id and result:
                    try:
                        # 요약 텍스트 추출 (result가 문자열인 경우 그대로 사용, dict인 경우 content 추출)
                        summary_text = result
                        if isinstance(result, dict):
                            summary_text = result.get("content", str(result))
                        elif not isinstance(result, str):
                            summary_text = str(result)
                        
                        # 공통 저장 함수 사용
                        _save_summary_to_db(video_id, user_id, summary_text, AI_prompt)
                    except Exception as e:
                        logger.error(f"요약 결과 DB 저장 실패: {e}")
                        # DB 저장 실패해도 요약은 계속 진행
            else:
                print(f"저장된 요약 결과가 있어 summarize_video를 건너뜁니다. 바로 query_video로 진행합니다.")
            
            # prompt를 질문으로 처리: VIA 서버의 query_video 사용
            # 동영상 컨텍스트를 직접 활용하여 질문에 답변
            try:
                # Ollama를 사용하여 프롬프트를 영어로 번역하고 타임스탬프 추출 지시 추가
                enhanced_prompt = await build_query_prompt(prompt + DEFAULT_QUERY_TIMESTAMP_SUFFIX)
                
                # query_video 파라미터 준비 (기본값 사용)
                query_params = build_query_video_params(
                    video_id=video_id,
                    model=model,
                    query=enhanced_prompt,
                    chunk_size=chunk_duration,  # 요약에 사용한 chunk_duration과 동일하게
                    temperature=0
                )
                
                # VIA 서버로 질문 전달
                query_result = await vss_client.query_video(*query_params)
                
                # query_result를 Ollama LLM에 보내서 타임스탬프만 추출
                extracted_timestamps_text = None
                try:
                    
                    # Ollama API 호출을 위한 프롬프트 구성
                    timestamp_extraction_prompt = f"""다음은 동영상 질의 응답 결과입니다:
{query_result}

위 응답에서 타임스탬프만 추출하여 반드시 '시작시간-끝시간' 형태로만 출력해주세요. 타임스탬프 형식은 초 단위(예: 10.5-120.3) 또는 분:초 형식(예: 1:30-2:45)일 수 있습니다. 타임스탬프만 출력하고 다른 설명은 포함하지 마세요."""
                    
                    # Ollama API 호출 (aiohttp 사용)
                    session = await get_session()
                    ollama_url = f"{OLLAMA_BASE_URL}/api/chat"
                    payload = {
                        "model": OLLAMA_MODEL,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert at extracting timestamps from video query responses. Extract only timestamps and output them in a clear format."
                            },
                            {
                                "role": "user",
                                "content": timestamp_extraction_prompt
                            }
                        ],
                        "stream": False,
                        "options": {
                            "temperature": 0,  # 타임스탬프 추출은 정확성이 중요하므로 낮은 temperature
                            "num_predict": 500  # 타임스탬프만 추출하므로 적은 토큰 수
                        }
                    }
                    
                    async with session.post(
                        ollama_url,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=OLLAMA_TIMEOUT)
                    ) as ollama_response:
                        if ollama_response.status == 200:
                            ollama_data = await ollama_response.json()
                            extracted_timestamps_text = ollama_data.get("message", {}).get("content", "")
                            if extracted_timestamps_text:
                                extracted_timestamps_text = extracted_timestamps_text.strip()
                            else:
                                print("Ollama 응답에 content가 없습니다.")
                        else:
                            error_text = await ollama_response.text()
                            print(f"Ollama API 호출 실패 (HTTP {ollama_response.status}): {error_text}")
                except aiohttp.ClientConnectorError as e:
                    logger.error(f"Ollama 서버에 연결할 수 없습니다: {e}")
                    logger.error(f"Ollama 서버 주소: {OLLAMA_BASE_URL}")
                    logger.warning("Ollama 연결 실패로 타임스탬프 추출을 건너뜁니다. VIA 서버 응답만 사용합니다.")
                    logger.info("Ollama 서버 확인 방법:")
                    logger.info("  1. Ollama 서버가 실행 중인지 확인: ollama serve")
                    logger.info("  2. 네트워크 연결 확인: ping 172.16.15.69")
                    logger.info("  3. 포트 확인: telnet 172.16.15.69 11434")
                    logger.info("  4. 환경 변수 확인: OLLAMA_BASE_URL 설정 확인")
                except asyncio.TimeoutError as e:
                    logger.error(f"Ollama 서버 응답 시간 초과: {e}")
                    logger.warning("Ollama 연결 타임아웃으로 타임스탬프 추출을 건너뜁니다.")
                except Exception as e:
                    logger.error(f"Ollama를 사용한 타임스탬프 추출 중 오류 발생: {e}")
                    logger.warning("Ollama 오류로 타임스탬프 추출을 건너뜁니다.")
                
                print(f"VIA 서버 답변: {query_result}")
                
                # 추출된 타임스탬프를 파싱하여 클립 생성에 사용
                timestamp_ranges = []
                if extracted_timestamps_text:
                    timestamp_ranges = parse_timestamps(extracted_timestamps_text, duration)
                
                # 타임스탬프 기반 클립 생성
                base_name, _ = os.path.splitext(file_path)
                # 고유한 파일명을 위해 타임스탬프 추가 (중복 방지 및 브라우저 캐시 문제 해결)
                timestamp_suffix = int(time.time() * 1000)  # 밀리초 단위 타임스탬프
                
                if timestamp_ranges:
                    # 타임스탬프가 있으면 해당 구간의 클립 생성
                    clip_index = 0
                    for start_time, end_time in timestamp_ranges:
                        # 타임스탬프 간격이 0초인 클립은 건너뛰기
                        if end_time - start_time <= 0:
                            logger.warning(f"타임스탬프 간격이 0초 이하인 클립을 건너뜁니다: {start_time} - {end_time}")
                            continue
                        
                        clip_filename = f"clip_{base_name}_{timestamp_suffix}_{clip_index+1}.mp4"
                        clip_path = os.path.join("./clips", clip_filename)
                        try:
                            # 타임스탬프 구간의 클립 생성
                            video.subclip(start_time, end_time).write_videofile(
                                clip_path,
                                codec="libx264",
                                audio=False,
                                verbose=False
                            )
                            base = str(request.base_url).rstrip('/')
                            clip_url = f"{base}/clips/{clip_filename}"
                            video_clips.append({
                                "id": f"{base_name}_{timestamp_suffix}_{clip_index}",
                                "title": clip_filename,
                                "url": clip_url,
                                "start_time": start_time,
                                "end_time": end_time,
                                "search_query": prompt
                            })
                            clip_index += 1
                        except Exception as e:
                            print(f"Error generating clip {clip_filename}: {e}")
                        time.sleep(0.5)
                else:
                    # 타임스탬프가 없으면 VIA 서버 답변을 그대로 반환
                    logger.warning(f"타임스탬프를 찾을 수 없습니다. 검색어: '{prompt}'. VIA 서버 답변을 반환합니다.")
                    # 클립 없이 VIA 서버 답변만 포함하여 반환
                    video_clips.append({
                        "id": f"{base_name}_{timestamp_suffix}_no_timestamp",
                        "title": "VIA 서버 응답",
                        "url": None,
                        "start_time": None,
                        "end_time": None,
                        "search_query": prompt,
                        "via_response": query_result  # VIA 서버 답변 추가
                    })
            except HTTPException:
                # HTTPException은 그대로 전파
                raise
            except Exception as via_error:
                logger.error(f"VIA 서버 query_video 실패: {via_error}")
                # 검색 실패 에러 반환
                raise HTTPException(
                    status_code=500,
                    detail=f"검색 실패: VIA 서버에서 장면 검색 중 오류가 발생했습니다. ({str(via_error)})"
                )
            finally:
                video.close()
                del video

            grouped_clips.append({
                "video": file_path,
                "clips": video_clips
            })

    except Exception as e:
        logger.error(f"Error processing uploaded video(s): {e}")
        raise HTTPException(status_code=500, detail=f"Error processing uploaded video(s): {e}")

    # 클립 추출 여부 확인
    clips_extracted = False
    for group in grouped_clips:
        for clip in group.get("clips", []):
            if clip.get("url") and not clip.get("via_response"):
                clips_extracted = True
                break
        if clips_extracted:
            break
    
    print("All clips generated successfully.")
    print(f"Returned clips payload: {json.dumps({'clips': grouped_clips, 'clips_extracted': clips_extracted}, ensure_ascii=False)}")
    return JSONResponse(content={"clips": grouped_clips, "clips_extracted": clips_extracted})

# ==================== 동영상 요약 VSS API ====================
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
    enable_audio: bool = Form(...),
    video_id: Optional[str] = Form(None),  # VIA 서버의 video_id (이미 업로드된 경우)
):
    await ensure_vss_client()
    model = await get_via_model()

    # video_id가 제공되지 않은 경우에만 업로드 (하지만 사용자 요청에 따라 업로드하지 않음)
    if not video_id:
        # video_id가 없으면 에러 반환 (업로드를 하지 않도록 수정)
        raise HTTPException(status_code=400, detail="video_id가 필요합니다. 이미 업로드된 동영상의 video_id를 제공해주세요.")

    try:
        # summarize_video 파라미터 준비 (Form으로 받은 모든 값 전달)
        summarize_params = build_summarize_params(
            video_id=video_id,
            chunk_duration=chunk_duration,
            model=model,
            prompt=prompt,
            cs_prompt=csprompt,
            sa_prompt=saprompt,
            num_frames_per_chunk=num_frames_per_chunk,
            frame_width=frame_width,
            frame_height=frame_height,
            top_k=top_k,
            top_p=top_p,
            temperature=temperature,
            max_new_tokens=max_tokens,
            seed=seed,
            batch_size=batch_size,
            rag_batch_size=rag_batch_size,
            rag_top_k=rag_top_k,
            summarize_top_p=summary_top_p,
            summarize_temperature=summary_temperature,
            summarize_max_tokens=summary_max_tokens,
            chat_top_p=chat_top_p,
            chat_temperature=chat_temperature,
            chat_max_tokens=chat_max_tokens,
            notification_top_p=alert_top_p,
            notification_temperature=alert_temperature,
            notification_max_tokens=alert_max_tokens,
            enable_audio=enable_audio
        )
        result = await vss_client.summarize_video(*summarize_params)
        return {"summary": result, "video_id": video_id}
    except HTTPException:
        # HTTPException은 그대로 전파
        raise
    except Exception as e:
        # 기타 예외 처리
        logger.error(f"vss_summarize 실행 중 오류: {e}")
        error_msg = str(e)
        
        # GStreamer 관련 에러인 경우 더 명확한 메시지 제공
        if "gst-stream-error" in error_msg or "qtdemux" in error_msg or "not-negotiated" in error_msg:
            raise HTTPException(
                status_code=500,
                detail=f"기술적 오류: {error_msg}"
            )
        else:
            raise HTTPException(status_code=500, detail=f"요약 생성 중 오류가 발생했습니다: {error_msg}")

# ==================== 동영상 검색 VSS API ====================
@app.post("/vss-query")
async def vss_query(
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
        
        await ensure_vss_client()
        model = await get_via_model()
    
        if file and not video_id:
            os.makedirs("./tmp", exist_ok=True)
            file_path = f"./tmp/{file.filename}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            video_id = await vss_client.upload_video(file_path)
        elif not video_id:
            raise HTTPException(status_code=400, detail="video_id 또는 file 중 하나는 필요합니다.")
        
        # query_video 파라미터 준비
        query_params = build_query_video_params(
            video_id=video_id,
            model=model,
            query=query,
            chunk_size=chunk_size,
            temperature=temperature,
            seed=seed,
            max_new_tokens=max_new_tokens,
            top_p=top_p,
            top_k=top_k
        )
        result = await vss_client.query_video(*query_params)

        return {"summary": result, "video_id": video_id}

# ==================== VIA 파일 목록 조회 API ====================
@app.get("/via-files")
async def list_via_files(
    purpose: str = Query(default="vision", description="파일 목적 (기본값: vision)")
):
    """
    VIA 서버에 업로드된 파일 목록 조회
    
    Args:
        purpose: 파일 목적 (기본값: "vision")
    
    Returns:
        파일 목록 (VIA 서버의 ListFilesResponse 형식)
    """
    try:
        await ensure_vss_client()
        result = await vss_client.list_files(purpose=purpose)
        print(result)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"VIA 파일 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"VIA 파일 목록 조회 중 오류가 발생했습니다: {str(e)}")

# 로그인용 모델
class LoginRequest(BaseModel):
    username: str
    password: str

# 동영상 업로드 응답 모델
class VideoUploadResponse(BaseModel):
    success: bool
    video_id: int
    file_url: str
    message: str

# DB 연결 설정 (커넥션 풀 사용)
import threading
from queue import Queue, Empty

# ==================== 데이터베이스 연결 풀 설정 클래스 ====================
class ConnectionPool:
    """DB 커넥션 풀 (동시 요청 처리 최적화)"""
    def __init__(self, max_connections=10, **kwargs):
        self.max_connections = max_connections
        self.connection_kwargs = kwargs
        self.pool = Queue(maxsize=max_connections)
        self.lock = threading.Lock()
        self.created_connections = 0
        
        # 초기 연결 생성 (실패해도 애플리케이션 시작은 계속)
        try:
            for _ in range(min(3, max_connections)):
                try:
                    conn = self._create_connection()
                    self.pool.put(conn)
                    self.created_connections += 1
                except Exception as e:
                    logger.warning(f"초기 DB 연결 생성 실패 (무시됨): {e}")
                    break
        except Exception as e:
            logger.warning(f"ConnectionPool 초기화 중 오류 (무시됨): {e}")
            logger.warning("첫 요청 시 연결을 다시 시도합니다.")
    
    def _create_connection(self):
        """새 DB 연결 생성"""
        # 호스트명이 명시적으로 전달되도록 보장
        connection_params = {
            'autocommit': True,  # 자동 커밋으로 성능 향상
            **self.connection_kwargs
        }
        
        # host.docker.internal 변환 방지: host를 강제로 IP 주소로 설정
        if 'host' in connection_params:
            original_host = connection_params['host']
            # IP 주소 형식인지 확인 (IPv4)
            if re.match(IP_PATTERN, str(original_host)):
                # IP 주소인 경우 그대로 사용 (변환 방지)
                # 문자열로 명시적 변환하여 호스트명 해석 방지
                connection_params['host'] = str(original_host).strip()
                logger.info(f"DB 연결 시도: host={connection_params['host']} (IP 주소 직접 사용), user={connection_params.get('user', 'N/A')}, database={connection_params.get('database', 'N/A')}")
            else:
                # 호스트명인 경우 그대로 사용
                connection_params['host'] = str(original_host).strip()
                logger.info(f"DB 연결 시도: host={connection_params['host']} (호스트명), user={connection_params.get('user', 'N/A')}, database={connection_params.get('database', 'N/A')}")
        
        # MariaDB 연결 시도
        try:
            conn = mariadb.connect(**connection_params)
            logger.info(f"DB 연결 성공: {connection_params.get('host', 'N/A')}")
            return conn
        except Exception as e:
            logger.error(f"DB 연결 실패: host={connection_params.get('host', 'N/A')}, error={e}")
            raise
    
    def get_connection(self, timeout=5):
        """풀에서 연결 가져오기"""
        try:
            conn = self.pool.get(timeout=timeout)
            # 연결이 살아있는지 확인
            try:
                conn.ping()
            except:
                # 연결이 끊어진 경우 새로 생성
                conn = self._create_connection()
            return conn
        except Empty:
            # 풀이 비어있으면 새 연결 생성 (최대치 내에서)
            with self.lock:
                if self.created_connections < self.max_connections:
                    self.created_connections += 1
                    return self._create_connection()
                else:
                    # 최대치 도달 시 대기
                    return self.pool.get(timeout=timeout)
    
    def return_connection(self, conn):
        """연결을 풀에 반환"""
        try:
            self.pool.put_nowait(conn)
        except:
            # 풀이 가득 찬 경우 연결 종료
            try:
                conn.close()
            except:
                pass
            with self.lock:
                self.created_connections -= 1

# ============================================================================
# 데이터베이스 연결 풀 초기화
# ============================================================================
# 데이터베이스 연결 정보 (환경 변수에서 로드, 없으면 기본값 사용)
# 환경 변수 설정: .env 파일에 DB_HOST, DB_USER, DB_PASSWORD, DB_PORT, DB_NAME 추가
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")  # 환경 변수에서 로드 (필수)
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "vss")

# DB_PASSWORD가 설정되지 않았으면 경고
if not DB_PASSWORD:
    logger.warning("DB_PASSWORD가 설정되지 않았습니다!")
    logger.warning("   .env 파일에 DB_PASSWORD를 설정하거나 환경 변수로 설정하세요.")

# ConnectionPool에 명시적으로 host를 IP 주소로 전달
# host.docker.internal 변환을 방지하기 위해 IP 주소를 문자열로 명시
# IP 주소 형식 검증
if not re.match(IP_PATTERN, str(DB_HOST)):
    logger.warning(f"DB_HOST가 IP 주소 형식이 아닙니다: {DB_HOST}")
    logger.warning("IP 주소 형식(예: 172.16.15.69)을 사용하는 것을 권장합니다.")

# IP 주소를 명시적으로 문자열로 변환 (호스트명 변환 방지)
db_host_str = str(DB_HOST).strip()
logger.info(f"DB 연결 풀 초기화: host={db_host_str} (타입: {type(db_host_str).__name__})")

db_pool = ConnectionPool(
    max_connections=20,
    user=DB_USER,
    password=DB_PASSWORD,
    host=db_host_str,  # IP 주소를 문자열로 명시적으로 전달
    port=int(DB_PORT),
    database=DB_NAME
)

# 하위 호환성을 위한 전역 연결 (점진적 마이그레이션용)
# 모듈 레벨에서 연결을 시도하되, 실패해도 애플리케이션 시작은 계속 진행
# 실제 사용 시점에 연결을 다시 시도하도록 함
conn = None
cursor = None

try:
    conn = db_pool.get_connection()
    conn.autocommit = True  # 자동 커밋 활성화
    cursor = conn.cursor()
    logger.info("데이터베이스 연결 성공 (전역 연결)")
except Exception as e:
    logger.warning(f"전역 데이터베이스 연결 실패 (시작 시점): {e}")
    logger.warning("첫 요청 시 연결을 다시 시도합니다.")
    conn = None
    cursor = None

def ensure_db_connection():
    """전역 DB 연결이 없으면 다시 시도"""
    global conn, cursor
    if conn is None or cursor is None:
        try:
            conn = db_pool.get_connection()
            conn.autocommit = True
            cursor = conn.cursor()
            logger.info("데이터베이스 연결 성공 (재연결)")
        except Exception as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            raise HTTPException(status_code=500, detail=f"데이터베이스 연결에 실패했습니다: {str(e)}")

def verify_user_exists(user_id: str):
    """사용자 존재 확인"""
    ensure_db_connection()
    cursor.execute("SELECT ID FROM vss_user WHERE ID = ?", (user_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

def validate_video_ownership(video_id: str, user_id: str, via_video_id: bool = False):
    """동영상 소유권 확인"""
    ensure_db_connection()
    if via_video_id:
        cursor.execute(
            "SELECT ID FROM vss_videos WHERE VIDEO_ID = ? AND USER_ID = ?",
            (video_id, user_id)
        )
    else:
        cursor.execute(
            "SELECT ID FROM vss_videos WHERE ID = ? AND USER_ID = ?",
            (video_id, user_id)
        )
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="동영상을 찾을 수 없거나 권한이 없습니다.")

def _save_summary_to_db(video_id: str, user_id: str, summary_text: str, prompt: str):
    """
    요약 결과를 DB에 저장하는 공통 함수
    
    Args:
        video_id: VIA 서버의 video_id (vss_videos.VIDEO_ID 컬럼 값)
        user_id: 사용자 ID
        summary_text: 요약 텍스트
        prompt: 사용된 프롬프트
    
    Returns:
        summary_id: 저장된 요약의 ID (INSERT인 경우), None (UPDATE인 경우)
    """
    try:
        # vss_summaries 테이블에 저장 또는 업데이트
        cursor.execute(
            """INSERT INTO vss_summaries (VIDEO_ID, USER_ID, SUMMARY_TEXT, PROMPT) 
               VALUES (?, ?, ?, ?)
               ON DUPLICATE KEY UPDATE 
               SUMMARY_TEXT = VALUES(SUMMARY_TEXT),
               PROMPT = VALUES(PROMPT),
               UPDATED_AT = CURRENT_TIMESTAMP""",
            (video_id, user_id, summary_text, prompt)
        )
        conn.commit()
        
        summary_id = cursor.lastrowid if cursor.rowcount == 1 else None
        if summary_id is None:
            # UPDATE인 경우 ID 조회
            cursor.execute(
                "SELECT ID FROM vss_summaries WHERE VIDEO_ID = ? AND USER_ID = ?",
                (video_id, user_id)
            )
            row = cursor.fetchone()
            summary_id = row[0] if row else None
        
        logger.info(f"요약 결과 DB 저장 완료: VIDEO_ID={video_id}, USER_ID={user_id}, summary_id={summary_id}")
        return summary_id
    except Exception as e:
        logger.error(f"요약 결과 DB 저장 실패: {e}")
        raise

def get_db_connection():
    """DB 연결 가져오기 (컨텍스트 매니저)"""
    return DBConnectionContext()

class DBConnectionContext:
    """DB 연결 컨텍스트 매니저"""
    def __enter__(self):
        self.conn = db_pool.get_connection()
        self.conn.autocommit = True  # 자동 커밋 활성화
        self.cursor = self.conn.cursor()
        return self.cursor
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # autocommit이 활성화되어 있으므로 명시적 커밋 불필요
        db_pool.return_connection(self.conn)

# 이메일 인증 코드 저장소 (실제 운영에서는 Redis 등 사용 권장)
# 구조: {email: {"code": "123456", "expires_at": datetime, "verified": False}}
email_verification_codes = {}

# 비밀번호 재설정용 인증 코드 저장소
# 구조: {email: {"code": "123456", "expires_at": datetime, "verified": False, "username": "user_id"}}
reset_password_codes = {}

# 이메일 설정 (환경 변수에서 가져오거나 기본값 사용)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)

# SMTP 설정 로드 확인 로깅
if SMTP_USER and SMTP_PASSWORD:
    logger.info(f"SMTP 설정 로드 완료: SERVER={SMTP_SERVER}, PORT={SMTP_PORT}, USER={SMTP_USER[:3]}***")
else:
    logger.warning("SMTP 설정이 로드되지 않았습니다!")
    logger.warning(f"   SMTP_USER: {'설정됨' if SMTP_USER else '비어있음'}")
    logger.warning(f"   SMTP_PASSWORD: {'설정됨' if SMTP_PASSWORD else '비어있음'}")
    logger.warning("   .env 파일을 확인하거나 setup_smtp.py를 실행하여 설정하세요.")

def generate_verification_code():
    """6자리 인증 코드 생성"""
    return str(random.randint(100000, 999999))

def send_verification_email(to_email: str, code: str, is_reset_password: bool = False):
    """인증 코드를 이메일로 전송"""
    try:
        # 이메일 메시지 생성
        msg = MIMEMultipart()
        msg['From'] = SMTP_FROM_EMAIL
        msg['To'] = to_email
        purpose_text = "비밀번호 재설정" if is_reset_password else "회원가입"
        msg['Subject'] = f"VSS {purpose_text} 이메일 인증"
        
        # 이메일 본문 (HTML 형식으로 개선)
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .code-box {{ background: white; border: 2px dashed #667eea; padding: 20px; text-align: center; margin: 20px 0; border-radius: 5px; }}
        .code {{ font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 5px; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>VSS {purpose_text} 인증</h1>
        </div>
        <div class="content">
            <p>안녕하세요,</p>
            <p>VSS {purpose_text}을 위한 이메일 인증 코드입니다.</p>
            <div class="code-box">
                <div class="code">{code}</div>
            </div>
            <p>이 코드는 <strong>10분간</strong> 유효합니다.</p>
            <p style="color: #999; font-size: 12px;">본인이 요청한 것이 아니라면 이 이메일을 무시하세요.</p>
        </div>
        <div class="footer">
            <p>감사합니다.<br>VSS Team</p>
        </div>
    </div>
</body>
</html>
        """
        
        # 텍스트 버전도 포함 (HTML을 지원하지 않는 클라이언트용)
        text_body = f"""
안녕하세요,

VSS {purpose_text}을 위한 이메일 인증 코드입니다.

인증 코드: {code}

이 코드는 10분간 유효합니다.
본인이 요청한 것이 아니라면 이 이메일을 무시하세요.

감사합니다.
VSS Team
        """
        
        # HTML과 텍스트 버전 모두 첨부
        msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        # SMTP 서버 연결 및 이메일 전송
        if SMTP_USER and SMTP_PASSWORD:
            # 포트 465는 SSL, 포트 587은 TLS 사용
            if SMTP_PORT == 465:
                # SSL 사용 (Naver, Daum 등)
                server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
                server.login(SMTP_USER, SMTP_PASSWORD)
            else:
                # TLS 사용 (Gmail, Outlook 등)
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
            
            text = msg.as_string()
            server.sendmail(SMTP_FROM_EMAIL, to_email, text)
            server.quit()
            logger.info(f"인증 코드 이메일 전송 성공: {to_email}")
            return True
        else:
            # SMTP 설정이 없으면 로그만 출력 (개발 환경)
            logger.warning(f"SMTP 설정이 없어 이메일을 전송하지 않습니다.")
            logger.warning(f"인증 코드: {code} (이메일: {to_email})")
            logger.warning(f"실제 운영 환경에서는 .env 파일에 SMTP 설정을 추가하세요.")
            return True  # 개발 환경에서는 항상 성공으로 처리
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP 인증 실패: {e}")
        logger.error(f"사용자명과 비밀번호를 확인하세요. Gmail의 경우 앱 비밀번호를 사용해야 합니다.")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP 오류: {e}")
        return False
    except Exception as e:
        logger.error(f"이메일 전송 실패: {e}")
        logger.error(f"SMTP 설정 확인: SERVER={SMTP_SERVER}, PORT={SMTP_PORT}, USER={SMTP_USER[:3] + '***' if SMTP_USER else 'None'}")
        return False

def cleanup_expired_codes():
    """만료된 인증 코드 정리"""
    current_time = datetime.now()
    expired_emails = [
        email for email, data in email_verification_codes.items()
        if data["expires_at"] < current_time
    ]
    for email in expired_emails:
        del email_verification_codes[email]

# 로그인 엔드포인트
@app.post("/login")
def login(data: LoginRequest = Body(...)):
    ensure_db_connection()
    cursor.execute(
        "SELECT PW FROM vss_user WHERE ID = ?",
        (data.username,)
    )
    row = cursor.fetchone()
    if row is None:
        return {"success": False, "message": "계정이 없습니다."}
    db_pw = row[0]
    
    # 해시화된 비밀번호와 입력된 비밀번호 비교
    password_correct = False
    try:
        # bcrypt 해시로 저장된 경우
        if bcrypt.checkpw(data.password.encode('utf-8'), db_pw.encode('utf-8')):
            password_correct = True
    except (ValueError, AttributeError):
        # bcrypt 해시가 아닌 경우 (기존 평문 비밀번호 호환성 유지)
        if db_pw == data.password:
            password_correct = True
            # 기존 평문 비밀번호를 해시화하여 업데이트 (마이그레이션)
            try:
                hashed_password = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt())
                cursor.execute(
                    "UPDATE vss_user SET PW = ? WHERE ID = ?",
                    (hashed_password.decode('utf-8'), data.username)
                )
                conn.commit()
                logger.info(f"비밀번호를 해시화하여 업데이트했습니다: {data.username}")
            except Exception as e:
                logger.warning(f"비밀번호 해시화 업데이트 실패: {e}")
    
    if password_correct:
        return {"success": True}
    else:
        return {"success": False, "message": "비밀번호가 틀렸습니다."}

# 이메일 인증 코드 전송 요청 모델
class SendVerificationCodeRequest(BaseModel):
    email: str

# 이메일 인증 코드 검증 요청 모델
class VerifyEmailRequest(BaseModel):
    email: str
    code: str

# 회원가입 요청 모델 (인증 코드 포함)
class User(BaseModel):
    username: str
    password: str
    email: str
    verification_code: str

@app.get("/debug/email-check/{email}")
def debug_email_check(email: str):
    """이메일 검증 디버깅용 엔드포인트"""
    email_lower = validate_email(email)
    is_valid_format = True  # validate_email에서 이미 검증됨
    
    ensure_db_connection()
    cursor.execute("SELECT ID FROM vss_user WHERE EMAIL = ?", (email_lower,))
    existing_user = cursor.fetchone()
    is_existing = existing_user is not None
    
    return {
        "email": email_lower,
        "is_valid_format": is_valid_format,
        "is_existing": is_existing,
        "existing_user_id": existing_user[0] if existing_user else None
    }

@app.post("/send-verification-code")
def send_verification_code(request: SendVerificationCodeRequest):
    """이메일 인증 코드 전송"""
    try:
        # 요청 데이터 로깅
        logger.info(f"인증 코드 전송 요청 수신: {request.email}")
        
        email = validate_email(request.email)
        logger.info(f"처리할 이메일: {email}")
        
        # 기존 사용자 이메일 중복 확인
        try:
            ensure_db_connection()
            cursor.execute("SELECT ID FROM vss_user WHERE EMAIL = ?", (email,))
            existing_user = cursor.fetchone()
            if existing_user:
                logger.warning(f"이미 사용 중인 이메일: {email}")
                raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")
        except HTTPException:
            raise
        except Exception as db_error:
            logger.error(f"데이터베이스 조회 오류: {db_error}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
        # 만료된 코드 정리
        cleanup_expired_codes()
        
        # 인증 코드 생성 및 저장
        code = generate_verification_code()
        expires_at = datetime.now() + timedelta(minutes=EMAIL_CODE_EXPIRY_MINUTES)
        
        email_verification_codes[email] = {
            "code": code,
            "expires_at": expires_at,
            "verified": False
        }
        logger.info(f"인증 코드 생성 완료: {email} (코드: {code})")
        
        # 이메일 전송
        if send_verification_email(email, code):
            logger.info(f"인증 코드 이메일 전송 성공: {email}")
            return {"success": True, "message": "인증 코드가 이메일로 전송되었습니다."}
        else:
            logger.error(f"이메일 전송 실패: {email}")
            raise HTTPException(status_code=500, detail="이메일 전송에 실패했습니다. SMTP 설정을 확인하거나 다시 시도해주세요.")
    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except Exception as e:
        logger.error(f"인증 코드 전송 중 예상치 못한 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}")

@app.post("/verify-email-code")
def verify_email_code(request: VerifyEmailRequest):
    """이메일 인증 코드 검증"""
    email = validate_email(request.email)
    code = request.code.strip()
    
    # 만료된 코드 정리
    cleanup_expired_codes()
    
    # 인증 코드 확인
    if email not in email_verification_codes:
        raise HTTPException(status_code=400, detail="인증 코드가 만료되었거나 존재하지 않습니다. 다시 요청해주세요.")
    
    verification_data = email_verification_codes[email]
    
    # 만료 확인
    if verification_data["expires_at"] < datetime.now():
        del email_verification_codes[email]
        raise HTTPException(status_code=400, detail="인증 코드가 만료되었습니다. 다시 요청해주세요.")
    
    # 코드 일치 확인
    if verification_data["code"] != code:
        raise HTTPException(status_code=400, detail="인증 코드가 일치하지 않습니다.")
    
    # 인증 성공 표시
    verification_data["verified"] = True
    logger.info(f"이메일 인증 성공: {email}")
    return {"success": True, "message": "이메일 인증이 완료되었습니다."}

@app.post("/register")
def register(user: User):
    """회원가입 (이메일 인증 필수)"""
    email = validate_email(user.email)
    
    # 이메일 인증 확인
    cleanup_expired_codes()
    if email not in email_verification_codes:
        raise HTTPException(status_code=400, detail="이메일 인증이 필요합니다. 인증 코드를 먼저 요청해주세요.")
    
    verification_data = email_verification_codes[email]
    
    # 인증 코드 검증 확인
    if not verification_data["verified"]:
        raise HTTPException(status_code=400, detail="이메일 인증이 완료되지 않았습니다. 인증 코드를 먼저 검증해주세요.")
    
    # 인증 코드 만료 확인
    if verification_data["expires_at"] < datetime.now():
        del email_verification_codes[email]
        raise HTTPException(status_code=400, detail="인증 코드가 만료되었습니다. 다시 요청해주세요.")
    
    # 최종 인증 코드 확인 (추가 보안)
    if verification_data["code"] != user.verification_code.strip():
        raise HTTPException(status_code=400, detail="인증 코드가 일치하지 않습니다.")
    
    try:
        # 비밀번호를 bcrypt로 해시화
        hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
        hashed_password_str = hashed_password.decode('utf-8')
        
        ensure_db_connection()
        cursor.execute(
            "INSERT INTO vss_user (ID, PW, EMAIL) VALUES (?, ?, ?)",
            (user.username, hashed_password_str, email)
        )
        conn.commit()
        
        # 회원가입 성공 후 인증 코드 삭제
        del email_verification_codes[email]
        
        logger.info(f"회원가입 성공: {user.username} ({email})")
        return {"message": "회원가입 성공"}
    except mariadb.IntegrityError as e:
            error_msg = str(e)
            if "ID" in error_msg or "PRIMARY" in error_msg:
                raise HTTPException(status_code=400, detail="이미 존재하는 사용자 ID입니다.")
            elif "EMAIL" in error_msg:
                raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")
            else:
                raise HTTPException(status_code=400, detail="이미 존재하는 사용자입니다.")

# 비밀번호 재설정용 인증 코드 전송 요청 모델
class SendResetPasswordCodeRequest(BaseModel):
    username: str
    email: str

# 비밀번호 재설정용 인증 코드 검증 요청 모델
class VerifyResetPasswordCodeRequest(BaseModel):
    username: str
    email: str
    code: str

# 비밀번호 재설정 요청 모델
class ResetPasswordRequest(BaseModel):
    username: str
    email: str
    verification_code: str
    new_password: str

def cleanup_expired_reset_codes():
    """만료된 비밀번호 재설정 인증 코드 정리"""
    current_time = datetime.now()
    expired_emails = [
        email for email, data in reset_password_codes.items()
        if data["expires_at"] < current_time
    ]
    for email in expired_emails:
        del reset_password_codes[email]

@app.post("/send-reset-password-code")
def send_reset_password_code(request: SendResetPasswordCodeRequest):
    """비밀번호 재설정용 이메일 인증 코드 전송"""
    try:
        username = request.username.strip()
        email = request.email.strip().lower()
        
        if not username:
            raise HTTPException(status_code=400, detail="ID를 입력해주세요.")
        email = validate_email(request.email)
        
        # 사용자 ID와 이메일 일치 확인
        ensure_db_connection()
        cursor.execute("SELECT ID, EMAIL FROM vss_user WHERE ID = ?", (username,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        db_email = user[1].strip().lower() if user[1] else ""
        if db_email != email:
            raise HTTPException(status_code=400, detail="등록된 이메일과 일치하지 않습니다.")
        
        # 만료된 코드 정리
        cleanup_expired_reset_codes()
        
        # 인증 코드 생성 및 저장
        code = generate_verification_code()
        expires_at = datetime.now() + timedelta(minutes=EMAIL_CODE_EXPIRY_MINUTES)
        
        reset_password_codes[email] = {
            "code": code,
            "expires_at": expires_at,
            "verified": False,
            "username": username
        }
        logger.info(f"비밀번호 재설정 인증 코드 생성 완료: {email} (코드: {code})")
        
        # 이메일 전송
        if send_verification_email(email, code, is_reset_password=True):
            logger.info(f"비밀번호 재설정 인증 코드 이메일 전송 성공: {email}")
            return {"success": True, "message": "인증 코드가 이메일로 전송되었습니다."}
        else:
            logger.error(f"이메일 전송 실패: {email}")
            raise HTTPException(status_code=500, detail="이메일 전송에 실패했습니다. SMTP 설정을 확인하거나 다시 시도해주세요.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"비밀번호 재설정 인증 코드 전송 중 예상치 못한 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}")

@app.post("/verify-reset-password-code")
def verify_reset_password_code(request: VerifyResetPasswordCodeRequest):
    """비밀번호 재설정용 이메일 인증 코드 검증"""
    username = request.username.strip()
    email = validate_email(request.email)
    code = request.code.strip()
    
    # 만료된 코드 정리
    cleanup_expired_reset_codes()
    
    # 인증 코드 확인
    if email not in reset_password_codes:
        raise HTTPException(status_code=400, detail="인증 코드가 만료되었거나 존재하지 않습니다. 다시 요청해주세요.")
    
    verification_data = reset_password_codes[email]
    
    # 사용자 ID 일치 확인
    if verification_data["username"] != username:
        raise HTTPException(status_code=400, detail="사용자 ID가 일치하지 않습니다.")
    
    # 만료 확인
    if verification_data["expires_at"] < datetime.now():
        del reset_password_codes[email]
        raise HTTPException(status_code=400, detail="인증 코드가 만료되었습니다. 다시 요청해주세요.")
    
    # 코드 일치 확인
    if verification_data["code"] != code:
        raise HTTPException(status_code=400, detail="인증 코드가 일치하지 않습니다.")
    
    # 인증 성공 표시
    verification_data["verified"] = True
    logger.info(f"비밀번호 재설정 이메일 인증 성공: {email}")
    return {"success": True, "message": "이메일 인증이 완료되었습니다."}

@app.post("/reset-password")
def reset_password(request: ResetPasswordRequest):
    """비밀번호 재설정"""
    username = request.username.strip()
    email = validate_email(request.email)
    code = request.verification_code.strip()
    new_password = request.new_password
    
    # 비밀번호 길이 검증
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="비밀번호는 8자 이상이어야 합니다.")
    
    # 이메일 인증 확인
    cleanup_expired_reset_codes()
    if email not in reset_password_codes:
        raise HTTPException(status_code=400, detail="이메일 인증이 필요합니다. 인증 코드를 먼저 요청해주세요.")
    
    verification_data = reset_password_codes[email]
    
    # 인증 코드 검증 확인
    if not verification_data["verified"]:
        raise HTTPException(status_code=400, detail="이메일 인증이 완료되지 않았습니다. 인증 코드를 먼저 검증해주세요.")
    
    # 인증 코드 만료 확인
    if verification_data["expires_at"] < datetime.now():
        del reset_password_codes[email]
        raise HTTPException(status_code=400, detail="인증 코드가 만료되었습니다. 다시 요청해주세요.")
    
    # 최종 인증 코드 확인 (추가 보안)
    if verification_data["code"] != code:
        raise HTTPException(status_code=400, detail="인증 코드가 일치하지 않습니다.")
    
    # 사용자 ID 일치 확인
    if verification_data["username"] != username:
        raise HTTPException(status_code=400, detail="사용자 ID가 일치하지 않습니다.")
    
    try:
        # 기존 비밀번호 조회
        ensure_db_connection()
        cursor.execute("SELECT PW FROM vss_user WHERE ID = ? AND EMAIL = ?", (username, email))
        user_row = cursor.fetchone()
        if not user_row:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없거나 이메일이 일치하지 않습니다.")
        
        db_pw = user_row[0]
        
        # 기존 비밀번호와 새 비밀번호 비교
        password_match = False
        try:
            # bcrypt 해시로 저장된 경우
            if bcrypt.checkpw(new_password.encode('utf-8'), db_pw.encode('utf-8')):
                password_match = True
        except (ValueError, AttributeError):
            # bcrypt 해시가 아닌 경우 (기존 평문 비밀번호 호환성 유지)
            if db_pw == new_password:
                password_match = True
        
        if password_match:
            raise HTTPException(status_code=400, detail="새 비밀번호는 기존 비밀번호와 동일할 수 없습니다.")
        
        # 비밀번호를 bcrypt로 해시화
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        hashed_password_str = hashed_password.decode('utf-8')
        
        # 비밀번호 업데이트
        cursor.execute(
            "UPDATE vss_user SET PW = ? WHERE ID = ? AND EMAIL = ?",
            (hashed_password_str, username, email)
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없거나 이메일이 일치하지 않습니다.")
        
        conn.commit()
        
        # 비밀번호 재설정 성공 후 인증 코드 삭제
        del reset_password_codes[email]
        
        logger.info(f"비밀번호 재설정 성공: {username} ({email})")
        return {"success": True, "message": "비밀번호가 성공적으로 재설정되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"비밀번호 재설정 실패: {e}")
        raise HTTPException(status_code=500, detail=f"비밀번호 재설정 중 오류가 발생했습니다: {str(e)}")

# 사용자 정보 조회 엔드포인트
@app.get("/user/{user_id}")
def get_user_info(user_id: str):
    """사용자 정보 조회"""
    try:
        verify_user_exists(user_id)
        ensure_db_connection()
        cursor.execute(
            "SELECT ID, EMAIL, CREATED_AT, UPDATED_AT FROM vss_user WHERE ID = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        # 프로필 이미지 경로 조회 (PROFILE_IMAGE_URL 필드가 있는 경우)
        profile_image_url = None
        try:
            cursor.execute(
                "SELECT PROFILE_IMAGE_URL FROM vss_user WHERE ID = ?",
                (user_id,)
            )
            profile_row = cursor.fetchone()
            if profile_row and profile_row[0]:
                profile_image_url = profile_row[0]
        except Exception as e:
            # PROFILE_IMAGE_URL 필드가 없을 수 있으므로 무시
            logger.debug(f"프로필 이미지 조회 중 오류 (무시됨): {e}")
        
        return {
            "success": True,
            "user": {
                "id": row[0],
                "email": row[1],
                "created_at": row[2].isoformat() if row[2] else None,
                "updated_at": row[3].isoformat() if row[3] else None,
                "profile_image_url": profile_image_url
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"사용자 정보 조회 중 오류가 발생했습니다: {str(e)}")

# 사용자 이메일 업데이트 요청 모델
class UpdateUserEmailRequest(BaseModel):
    email: str

# 사용자 이메일 업데이트 엔드포인트
@app.put("/user/{user_id}/email")
def update_user_email(user_id: str, request: UpdateUserEmailRequest):
    """사용자 이메일 업데이트"""
    try:
        verify_user_exists(user_id)
        email = validate_email(request.email)
        
        ensure_db_connection()
        cursor.execute(
            "UPDATE vss_user SET EMAIL = ?, UPDATED_AT = CURRENT_TIMESTAMP WHERE ID = ?",
            (email, user_id)
        )
        conn.commit()
        
        logger.info(f"사용자 이메일 업데이트 성공: {user_id} -> {email}")
        return {"success": True, "message": "이메일이 업데이트되었습니다.", "email": email}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 이메일 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail=f"이메일 업데이트 중 오류가 발생했습니다: {str(e)}")

# 프로필 이미지 업로드 엔드포인트
@app.post("/user/{user_id}/profile-image")
async def upload_profile_image(user_id: str, file: UploadFile = File(...)):
    """사용자 프로필 이미지 업로드"""
    try:
        verify_user_exists(user_id)
        
        # 파일 확장자 검증
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 이미지 형식입니다: {file_ext}. 지원 형식: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")
        
        # 파일 크기 제한 (5MB)
        file_content = await file.read()
        if len(file_content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="이미지 파일 크기는 5MB를 초과할 수 없습니다.")
        
        # 고유한 파일명 생성
        timestamp = int(time.time() * 1000)
        unique_filename = f"{user_id}_{timestamp}{file_ext}"
        file_path = profile_images_dir / unique_filename
        file_url = f"/profile-images/{unique_filename}"
        
        # 파일 저장
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # DB에 프로필 이미지 경로 저장 (PROFILE_IMAGE_URL 필드가 있는 경우)
        ensure_db_connection()
        try:
            # 먼저 컬럼이 있는지 확인하고 업데이트
            cursor.execute(
                "UPDATE vss_user SET PROFILE_IMAGE_URL = ?, UPDATED_AT = CURRENT_TIMESTAMP WHERE ID = ?",
                (file_url, user_id)
            )
            conn.commit()
        except Exception as db_error:
            # PROFILE_IMAGE_URL 필드가 없을 수 있으므로 컬럼 추가 시도
            logger.warning(f"프로필 이미지 URL 업데이트 실패, 컬럼 추가 시도: {db_error}")
            try:
                cursor.execute(
                    "ALTER TABLE vss_user ADD COLUMN PROFILE_IMAGE_URL VARCHAR(500)"
                )
                conn.commit()
                # 다시 업데이트 시도
                cursor.execute(
                    "UPDATE vss_user SET PROFILE_IMAGE_URL = ?, UPDATED_AT = CURRENT_TIMESTAMP WHERE ID = ?",
                    (file_url, user_id)
                )
                conn.commit()
            except Exception as alter_error:
                logger.error(f"프로필 이미지 컬럼 추가 실패: {alter_error}")
                # 컬럼 추가 실패해도 파일은 저장되었으므로 경로만 반환
                return {
                    "success": True,
                    "message": "프로필 이미지가 업로드되었습니다. (DB 업데이트 실패)",
                    "profile_image_url": build_file_url(file_url)
                }
        
        logger.info(f"프로필 이미지 업로드 성공: {user_id} -> {file_url}")
        return {
            "success": True,
            "message": "프로필 이미지가 업로드되었습니다.",
            "profile_image_url": build_file_url(file_url)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"프로필 이미지 업로드 실패: {e}")
        raise HTTPException(status_code=500, detail=f"프로필 이미지 업로드 중 오류가 발생했습니다: {str(e)}")

# VIA 서버 업로드 함수 (백그라운드 작업 - 비동기)
async def upload_to_via_server_background(file_path: str, video_id: int, user_id: str):
    """VIA 서버에 동영상을 업로드하고 DB에 VIDEO_ID 업데이트 (백그라운드 작업)"""
    try:
        # 파일이 존재하는지 확인
        if not Path(file_path).exists():
            logger.error(f"파일이 존재하지 않습니다: {file_path}")
            return
        
        await ensure_vss_client()
        via_video_id = await vss_client.upload_video(str(file_path))
        logger.info(f"VIA 서버 업로드 성공: video_id={via_video_id}, db_video_id={video_id}")
        
        # DB에 VIDEO_ID 업데이트
        ensure_db_connection()
        cursor.execute(
            "UPDATE vss_videos SET VIDEO_ID = ? WHERE ID = ? AND USER_ID = ?",
            (via_video_id, video_id, user_id)
        )
        conn.commit()
        logger.info(f"VIDEO_ID 업데이트 완료: video_id={video_id}, via_video_id={via_video_id}")
    except Exception as e:
        logger.warning(f"VIA 서버 업로드 실패 (video_id={video_id}): {e}")
        # VIA 업로드 실패해도 계속 진행 (나중에 재시도 가능)

# 동영상 메타데이터 추출 함수 (백그라운드 작업)
def extract_video_metadata(file_path: str, video_id: int, filename: str):
    """동영상 메타데이터를 추출하여 DB에 업데이트"""
    try:
        video = VideoFileClip(str(file_path))
        width = int(video.w) if video.w else None
        height = int(video.h) if video.h else None
        duration = float(video.duration) if video.duration else None
        video.close()
        
        # 메타데이터 업데이트
        ensure_db_connection()
        cursor.execute(
            """UPDATE vss_videos 
               SET WIDTH = ?, HEIGHT = ?, DURATION = ? 
               WHERE ID = ?""",
            (width, height, duration, video_id)
        )
        conn.commit()
        logger.info(f"동영상 메타데이터 업데이트 완료: {filename} (ID: {video_id})")
    except Exception as e:
        logger.warning(f"동영상 메타데이터 추출 실패: {e}")

# 동영상 변환 함수 (AVI, MKV, FLV, WMV -> MP4)
def convert_video_to_mp4(input_path: str, output_path: str):
    """동영상을 MP4 형식으로 변환"""
    try:
        video = VideoFileClip(str(input_path))
        # MP4로 변환 (H.264 코덱 사용)
        video.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            verbose=False,
            logger=None
        )
        video.close()
        logger.info(f"동영상 변환 완료: {input_path} -> {output_path}")
        return True
    except Exception as e:
        logger.error(f"동영상 변환 실패: {e}")
        if 'video' in locals():
            try:
                video.close()
            except:
                pass
        return False

# 지원하지 않는 형식 목록
UNSUPPORTED_VIDEO_FORMATS = {'.avi', '.mkv', '.flv', '.wmv'}

@app.get("/convert-video/{video_id}")
async def convert_video(
    video_id: int,
    user_id: str = Query(..., description="사용자 ID")
):
    """동영상을 MP4 형식으로 변환하여 반환"""
    try:
        verify_user_exists(user_id)
        
        ensure_db_connection()
        
        # 동영상 정보 조회
        cursor.execute(
            "SELECT FILE_PATH, FILE_NAME, FILE_URL FROM vss_videos WHERE ID = ? AND USER_ID = ?",
            (video_id, user_id)
        )
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="동영상을 찾을 수 없거나 권한이 없습니다.")
        
        file_path = Path(row[0])
        file_name = row[1]
        file_url = row[2]
        
        # 파일이 존재하는지 확인
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="동영상 파일을 찾을 수 없습니다.")
        
        # 파일 확장자 확인
        file_ext = file_path.suffix.lower()
        if file_ext not in UNSUPPORTED_VIDEO_FORMATS:
            # 이미 지원하는 형식이면 원본 URL 반환
            return {
                "success": True,
                "converted_url": build_file_url(file_url),
                "message": "이미 지원하는 형식입니다."
            }
        
        # 변환된 파일 경로 생성
        base_name = file_path.stem
        converted_filename = f"{base_name}_converted.mp4"
        converted_path = converted_videos_dir / converted_filename
        converted_url = f"/converted-videos/{converted_filename}"
        
        # 이미 변환된 파일이 있으면 그대로 반환
        if converted_path.exists():
            logger.info(f"변환된 파일이 이미 존재함: {converted_path}")
            return {
                "success": True,
                "converted_url": build_file_url(converted_url),
                "message": "변환된 동영상이 준비되었습니다."
            }
        
        # 동영상 변환 실행
        logger.info(f"동영상 변환 시작: {file_path} -> {converted_path}")
        success = convert_video_to_mp4(str(file_path), str(converted_path))
        
        if not success:
            raise HTTPException(status_code=500, detail="동영상 변환에 실패했습니다.")
        
        return {
            "success": True,
            "converted_url": build_file_url(converted_url),
            "message": "동영상이 MP4로 변환되었습니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"동영상 변환 실패: {e}")
        raise HTTPException(status_code=500, detail=f"동영상 변환 중 오류가 발생했습니다: {str(e)}")

# 동영상 업로드 및 조회 API
@app.post("/upload-video")
async def upload_video_to_db(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Form(...)
):
    """동영상 파일을 서버에 업로드하고 DB에 저장 (최적화됨)"""
    global vss_client
    
    try:
        # 1. 파일 검증 (빠른 실패 - DB 쿼리 전에 검증)
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_VIDEO_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식입니다: {file_ext}")
        
        # 2. DB 쿼리 최적화: EXISTS 사용으로 성능 개선 (COUNT보다 빠름)
        ensure_db_connection()
        cursor.execute(
            """SELECT 
                   EXISTS(SELECT 1 FROM vss_user WHERE ID = ?) as user_exists,
                   EXISTS(SELECT 1 FROM vss_videos WHERE USER_ID = ? AND FILE_NAME = ?) as duplicate_exists""",
            (user_id, user_id, file.filename)
        )
        result = cursor.fetchone()
        user_exists, duplicate_exists = bool(result[0]), bool(result[1])
        
        if not user_exists:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        if duplicate_exists:
            raise HTTPException(status_code=400, detail=f"이미 업로드된 동영상입니다: {file.filename}")
        
        # 3. 파일명 생성 (타임스탬프는 미리 생성)
        base_filename = Path(file.filename).stem
        timestamp = int(time.time() * 1000)
        unique_filename = f"{base_filename}_{timestamp}{file_ext}"
        file_path = videos_dir / unique_filename
        file_url = f"/video-files/{unique_filename}"
        
        # 4. 파일 저장 (비동기 I/O로 최적화 - aiofiles 사용)
        file_size = 0
        async with aiofiles.open(file_path, "wb") as buffer:
            # 파일을 청크 단위로 읽어서 저장 (비동기 방식으로 더 빠름)
            while True:
                chunk = await file.read(FILE_BUFFER_SIZE)
                if not chunk:
                    break
                await buffer.write(chunk)
                file_size += len(chunk)
        
        # 5. DB 저장
        cursor.execute(
            """INSERT INTO vss_videos 
               (USER_ID, FILE_NAME, FILE_PATH, FILE_SIZE, FILE_URL, WIDTH, HEIGHT, DURATION, VIDEO_ID) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, file.filename, str(file_path), file_size, file_url, None, None, None, None)
        )
        # autocommit이 활성화되어 있으므로 명시적 커밋 불필요
        video_id = cursor.lastrowid
        
        # 6. VIA 서버 업로드 (동기적으로 실행 - 완료될 때까지 대기)
        try:
            await upload_to_via_server_background(str(file_path), video_id, user_id)
            logger.info(f"VIA 서버 업로드 완료: video_id={video_id}")
        except Exception as e:
            logger.error(f"VIA 서버 업로드 실패 (video_id={video_id}): {e}")
            # VIA 업로드 실패해도 업로드는 성공으로 처리 (나중에 재시도 가능)
            # 하지만 사용자에게 경고 메시지 포함
        
        # 7. 메타데이터 추출은 백그라운드로 실행 (VIA 업로드 완료 후)
        background_tasks.add_task(extract_video_metadata, str(file_path), video_id, file.filename)
        
        return {
            "success": True,
            "video_id": video_id,
            "file_url": build_file_url(file_url),
            "message": "동영상 업로드가 완료되었습니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"동영상 업로드 실패: {e}")
        # 파일이 저장되었지만 DB 저장 실패 시 파일 삭제
        if 'file_path' in locals() and file_path.exists():
            try:
                file_path.unlink()
            except:
                pass
        raise HTTPException(status_code=500, detail=f"동영상 업로드 중 오류가 발생했습니다: {str(e)}")

@app.get("/videos")
async def get_videos(user_id: str = Query(...)):
    """사용자의 동영상 목록 조회 (파일 존재 여부 확인 및 유효한 URL 반환)"""
    try:
        ensure_db_connection()
        cursor.execute(
            """SELECT ID, FILE_NAME, FILE_URL, FILE_SIZE, WIDTH, HEIGHT, DURATION, CREATED_AT, VIDEO_ID 
               FROM vss_videos 
               WHERE USER_ID = ? 
               ORDER BY CREATED_AT DESC""",
            (user_id,)
        )
        rows = cursor.fetchall()
        
        videos = []
        for row in rows:
            video_id = row[0]
            file_name = row[1]
            file_url = row[2]  # DB에 저장된 FILE_URL (예: /video-files/filename_timestamp.ext)
            file_size = row[3]
            width = row[4]
            height = row[5]
            duration = row[6]
            created_at = row[7]
            via_video_id = row[8]
            
            # 파일 존재 여부 확인 및 유효한 URL 결정
            valid_file_url = ""
            
            # 1. 원본 파일 확인 (FILE_URL에서 파일명 추출)
            if file_url:
                # FILE_URL에서 파일명 추출 (예: /video-files/filename.ext -> filename.ext)
                original_filename = file_url.replace("/video-files/", "").lstrip("/")
                original_file_path = videos_dir / original_filename
                
                if original_file_path.exists():
                    # 원본 파일이 존재하면 원본 URL 사용
                    valid_file_url = build_file_url(file_url)
                else:
                    # 원본 파일이 없으면 변환된 MP4 확인
                    # 변환된 파일명: filename_timestamp.mp4 (확장자를 .mp4로 변경)
                    base_name = Path(original_filename).stem  # 확장자 제거
                    converted_filename = f"{base_name}.mp4"
                    converted_file_path = converted_videos_dir / converted_filename
                    
                    if converted_file_path.exists():
                        # 변환된 MP4가 존재하면 변환된 URL 사용
                        converted_url = f"/converted-videos/{converted_filename}"
                        valid_file_url = build_file_url(converted_url)
                        logger.info(f"원본 파일 없음, 변환된 MP4 사용: {file_name} -> {converted_filename}")
                    else:
                        # 둘 다 없으면 원본 URL 사용 (나중에 404 처리)
                        valid_file_url = build_file_url(file_url)
                        logger.warning(f"동영상 파일을 찾을 수 없음: {file_name} (원본: {original_filename}, 변환: {converted_filename})")
            else:
                # FILE_URL이 없으면 빈 문자열
                logger.warning(f"FILE_URL이 없음: video_id={video_id}, file_name={file_name}")
            
            videos.append({
                "id": video_id,
                "title": file_name,
                "file_url": valid_file_url,
                "fileSize": file_size,
                "width": width,
                "height": height,
                "duration": duration,
                "date": created_at.strftime("%Y-%m-%d") if created_at else None,
                "video_id": via_video_id
            })
        
        return {"success": True, "videos": videos}
    except Exception as e:
        logger.error(f"동영상 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"동영상 목록 조회 중 오류가 발생했습니다: {str(e)}")

@app.delete("/videos/{video_id}")
async def delete_video(video_id: int, user_id: str = Query(...)):
    """동영상 삭제"""
    try:
        logger.info(f"동영상 삭제 요청: video_id={video_id}, user_id={user_id}")
        
        # 동영상 소유권 확인 및 파일 경로, VIDEO_ID 조회
        ensure_db_connection()
        cursor.execute(
            "SELECT FILE_PATH, FILE_URL, VIDEO_ID FROM vss_videos WHERE ID = ? AND USER_ID = ?",
            (video_id, user_id)
        )
        row = cursor.fetchone()
        if not row:
            logger.warning(f"동영상을 찾을 수 없음: video_id={video_id}, user_id={user_id}")
            raise HTTPException(status_code=404, detail="동영상을 찾을 수 없거나 권한이 없습니다.")
        
        db_file_path = row[0]  # DB에 저장된 FILE_PATH
        file_url = row[1]  # FILE_URL (예: /video-files/filename_timestamp.ext)
        via_video_id = row[2]  # VIA 서버의 video_id (vss_summaries 테이블의 VIDEO_ID)
        
        # vss_summaries 테이블에서 요약 결과 삭제 (VIDEO_ID는 VIA 서버의 video_id)
        if via_video_id:
            try:
                cursor.execute(
                    "DELETE FROM vss_summaries WHERE VIDEO_ID = ? AND USER_ID = ?",
                    (via_video_id, user_id)
                )
                deleted_summaries = cursor.rowcount
                if deleted_summaries > 0:
                    logger.info(f"요약 결과 삭제 완료: VIDEO_ID={via_video_id}, 삭제된 요약 수={deleted_summaries}")
                else:
                    logger.info(f"삭제할 요약 결과 없음: VIDEO_ID={via_video_id}")
            except Exception as e:
                logger.warning(f"요약 결과 삭제 중 오류 발생: {e}")
        
        # vss_videos 테이블에서 동영상 삭제
        cursor.execute("DELETE FROM vss_videos WHERE ID = ? AND USER_ID = ?", (video_id, user_id))
        conn.commit()
        logger.info(f"DB에서 동영상 삭제 완료: video_id={video_id}")
        
        # videos 폴더에서 파일 삭제
        file_path = None
        
        # 방법 1: FILE_PATH 사용 (절대 경로 또는 상대 경로)
        if db_file_path:
            file_path = Path(db_file_path)
            # 상대 경로인 경우 videos_dir 기준으로 절대 경로 생성
            if not file_path.is_absolute():
                # 파일명만 추출하여 videos_dir에 있는 파일 찾기
                filename = file_path.name if file_path.name else Path(db_file_path).name
                file_path = videos_dir.resolve() / filename
            else:
                # 절대 경로인 경우 그대로 사용
                file_path = file_path.resolve()
        
        # 방법 2: FILE_PATH가 없거나 파일이 없으면 FILE_URL에서 파일명 추출
        if not file_path or not file_path.exists():
            if file_url:
                # FILE_URL에서 파일명 추출 (예: /video-files/filename.ext -> filename.ext)
                filename = file_url.replace("/video-files/", "").lstrip("/")
                if filename:
                    file_path = videos_dir.resolve() / filename
        
        # 파일 삭제 시도
        if file_path and file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"동영상 파일 삭제 성공: {file_path}")
            except Exception as e:
                logger.warning(f"동영상 파일 삭제 실패: {file_path}, 오류: {e}")
        elif file_path:
            logger.warning(f"동영상 파일이 존재하지 않음: {file_path}")
        else:
            logger.warning(f"동영상 파일 경로를 확인할 수 없음: FILE_PATH={db_file_path}, FILE_URL={file_url}")
        
        # 클립 삭제: 동영상 파일명으로 시작하는 모든 클립 파일 삭제
        clips_dir = Path("./clips")
        if clips_dir.exists():
            try:
                # 동영상 파일명 추출 (확장자 포함)
                video_filename = None
                if file_path and file_path.exists():
                    video_filename = file_path.name
                elif file_url:
                    # FILE_URL에서 파일명 추출 (예: /video-files/filename.ext -> filename.ext)
                    video_filename = file_url.replace("/video-files/", "").lstrip("/")
                elif db_file_path:
                    # DB의 FILE_PATH에서 파일명 추출
                    video_filename = Path(db_file_path).name
                
                if video_filename:
                    # 파일명에서 확장자 제거하여 base_name 추출
                    base_name = Path(video_filename).stem
                    # 클립 파일명 패턴: clip_{base_name}_ 또는 clip_{full_path}_{base_name}_
                    # 경로가 포함된 경우와 파일명만 있는 경우 모두 처리
                    deleted_clips = 0
                    # clips 디렉토리의 모든 파일 확인
                    for clip_file in clips_dir.iterdir():
                        if not clip_file.is_file():
                            continue
                        
                        clip_name = clip_file.name
                        # 패턴 1: clip_{base_name}_로 시작하는 경우 (파일명만 사용)
                        # 패턴 2: clip_{full_path}_{base_name}_로 시작하는 경우 (경로 포함)
                        # 두 패턴 모두 매칭되도록 base_name이 포함되어 있는지 확인
                        if clip_name.startswith("clip_") and f"_{base_name}_" in clip_name:
                            try:
                                clip_file.unlink()
                                deleted_clips += 1
                                logger.info(f"클립 파일 삭제 성공: {clip_file.name}")
                            except Exception as e:
                                logger.warning(f"클립 파일 삭제 실패: {clip_file.name}, 오류: {e}")
                    
                    if deleted_clips > 0:
                        logger.info(f"총 {deleted_clips}개의 클립 파일이 삭제되었습니다.")
                    else:
                        logger.info(f"삭제할 클립 파일이 없습니다. (base_name: {base_name}, video_filename: {video_filename})")
                else:
                    logger.warning("동영상 파일명을 추출할 수 없어 클립 삭제를 건너뜁니다.")
            except Exception as e:
                logger.warning(f"클립 삭제 중 오류 발생: {e}")
        
        return {"success": True, "message": "동영상이 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"동영상 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=f"동영상 삭제 중 오류가 발생했습니다: {str(e)}")

# 클립 삭제 요청 모델
class DeleteClipsRequest(BaseModel):
    clip_urls: List[str]  # 삭제할 클립 URL 리스트

@app.post("/delete-clips")
async def delete_clips(request: DeleteClipsRequest):
    """클립 파일들을 삭제하는 엔드포인트"""
    try:
        clips_dir = Path("./clips")
        if not clips_dir.exists():
            return {"success": True, "message": "클립 디렉토리가 없습니다.", "deleted_count": 0}
        
        deleted_count = 0
        failed_count = 0
        
        for clip_url in request.clip_urls:
            try:
                # URL에서 파일명 추출
                if "/clips/" in clip_url:
                    filename = clip_url.split("/clips/")[-1].split("?")[0]  # 쿼리 파라미터 제거
                else:
                    # 상대 경로인 경우
                    filename = clip_url.replace("/clips/", "").split("?")[0]
                
                if not filename:
                    logger.warning(f"클립 파일명을 추출할 수 없습니다: {clip_url}")
                    failed_count += 1
                    continue
                
                clip_file_path = clips_dir / filename
                
                if clip_file_path.exists() and clip_file_path.is_file():
                        clip_file_path.unlink()
                        deleted_count += 1
                        logger.info(f"클립 파일 삭제 성공: {filename}")
                else:
                    logger.warning(f"클립 파일을 찾을 수 없습니다: {filename}")
                    failed_count += 1
            except Exception as e:
                logger.error(f"클립 삭제 중 오류 발생 ({clip_url}): {e}")
                failed_count += 1
        
        return {
            "success": True,
            "message": f"{deleted_count}개의 클립이 삭제되었습니다.",
            "deleted_count": deleted_count,
            "failed_count": failed_count
        }
    except Exception as e:
        logger.error(f"클립 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=f"클립 삭제 중 오류가 발생했습니다: {str(e)}")

# 요약 결과 저장 모델
class SaveSummaryRequest(BaseModel):
    video_id: str  # VIA 서버의 video_id (vss_videos.VIDEO_ID 컬럼 값)
    user_id: str
    prompt: str
    summary_text: str
    via_video_id: Optional[str] = None  # VIA 서버의 video_id (하위 호환성을 위해 유지)

@app.post("/save-summary")
async def save_summary(request: SaveSummaryRequest):
    """요약 결과를 DB에 저장"""
    try:
        video_id = request.video_id
        user_id = request.user_id
        prompt = request.prompt
        summary_text = request.summary_text
        
        verify_user_exists(user_id)
        
        validate_video_ownership(video_id, user_id, via_video_id=True)
        
        # 공통 저장 함수 사용
        # vss_summaries 테이블 구조:
        # - VIDEO_ID (VARCHAR): VIA 서버의 video_id (vss_videos.VIDEO_ID 컬럼 값)
        # - USER_ID (VARCHAR): 사용자 ID
        # - SUMMARY_TEXT (LONGTEXT): 요약 텍스트
        # - PROMPT (TEXT): 사용된 프롬프트
        # - CREATED_AT (TIMESTAMP): 자동 설정
        # - UPDATED_AT (TIMESTAMP): 자동 설정
        summary_id = _save_summary_to_db(video_id, user_id, summary_text, prompt)
        return {
            "success": True,
            "summary_id": summary_id,
            "message": "요약 결과가 저장되었습니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"요약 결과 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=f"요약 결과 저장 중 오류가 발생했습니다: {str(e)}")

@app.get("/summaries/{video_id}")
async def get_summary(video_id: str, user_id: str = Query(...)):
    """특정 동영상의 요약 결과 조회"""
    try:
        verify_user_exists(user_id)
        
        # 요약 결과 조회 (소유권 확인 포함)
        ensure_db_connection()
        cursor.execute(
            """SELECT s.ID, s.SUMMARY_TEXT, s.PROMPT, s.CREATED_AT, s.UPDATED_AT
               FROM vss_summaries s
               INNER JOIN vss_videos v ON s.VIDEO_ID = v.VIDEO_ID
               WHERE s.VIDEO_ID = ? AND s.USER_ID = ? AND v.USER_ID = ?""",
            (video_id, user_id, user_id)
        )
        row = cursor.fetchone()
        
        if not row:
            return {
                "success": False,
                "message": "요약 결과를 찾을 수 없습니다."
            }
        
        return {
            "success": True,
            "summary": {
                "id": row[0],
                "summary_text": row[1],
                "prompt": row[2] if len(row) > 2 else None,
                "created_at": row[3].isoformat() if len(row) > 3 and row[3] else None,
                "updated_at": row[4].isoformat() if len(row) > 4 and row[4] else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"요약 결과 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"요약 결과 조회 중 오류가 발생했습니다: {str(e)}")

@app.get("/summaries")
async def get_user_summaries(user_id: str = Query(...)):
    """사용자의 모든 요약 결과 조회"""
    try:
        verify_user_exists(user_id)
        
        # 사용자의 모든 요약 결과 조회
        ensure_db_connection()
        cursor.execute(
            """SELECT s.ID, s.VIDEO_ID, s.SUMMARY_TEXT, s.CREATED_AT, s.UPDATED_AT, v.FILE_NAME
               FROM vss_summaries s
               INNER JOIN vss_videos v ON s.VIDEO_ID = v.VIDEO_ID
               WHERE s.USER_ID = ? AND v.USER_ID = ?
               ORDER BY s.CREATED_AT DESC""",
            (user_id, user_id)
        )
        rows = cursor.fetchall()
        
        summaries = []
        for row in rows:
            summaries.append({
                "id": row[0],
                "video_id": row[1],
                "summary_text": row[2],
                "created_at": row[3].isoformat() if row[3] else None,
                "updated_at": row[4].isoformat() if row[4] else None,
                "video_name": row[5]
            })
        
        return {
            "success": True,
            "summaries": summaries,
            "count": len(summaries)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"요약 결과 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"요약 결과 목록 조회 중 오류가 발생했습니다: {str(e)}")

# 요약 결과 삭제 요청 모델
class DeleteSummaryRequest(BaseModel):
    video_ids: List[int]  # vss_videos 테이블의 ID 목록 (내부 DB ID)
    user_id: str

@app.delete("/summaries")
async def delete_summaries(request: DeleteSummaryRequest):
    """선택된 동영상들의 요약 결과 삭제"""
    try:
        user_id = request.user_id
        video_ids = request.video_ids
        
        if not video_ids or len(video_ids) == 0:
            raise HTTPException(status_code=400, detail="동영상 ID 목록이 필요합니다.")
        
        verify_user_exists(user_id)
        
        # 선택된 동영상들의 VIDEO_ID (VIA 서버의 video_id) 조회
        ensure_db_connection()
        placeholders = ','.join(['?'] * len(video_ids))
        cursor.execute(
            f"SELECT VIDEO_ID FROM vss_videos WHERE ID IN ({placeholders}) AND USER_ID = ?",
            (*video_ids, user_id)
        )
        rows = cursor.fetchall()
        via_video_ids = [row[0] for row in rows if row[0]]  # None이 아닌 것만
        
        if not via_video_ids:
            return {
                "success": True,
                "message": "삭제할 요약 결과가 없습니다.",
                "deleted_count": 0
            }
        
        # 요약 결과 삭제
        via_placeholders = ','.join(['?'] * len(via_video_ids))
        cursor.execute(
            f"DELETE FROM vss_summaries WHERE VIDEO_ID IN ({via_placeholders}) AND USER_ID = ?",
            (*via_video_ids, user_id)
        )
        conn.commit()
        deleted_count = cursor.rowcount
        
        logger.info(f"요약 결과 삭제 완료: USER_ID={user_id}, 삭제된 요약 수={deleted_count}")

        if deleted_count <= 0:
            return {
                "success": False,
                "message": "삭제할 요약 결과가 없습니다.",
                "deleted_count": 0
            }
        
        return {
            "success": True,
            "message": f"{deleted_count}개의 요약 결과가 삭제되었습니다.",
            "deleted_count": deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"요약 결과 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=f"요약 결과 삭제 중 오류가 발생했습니다: {str(e)}")

# ============================================================================
# 보고서 관련 API 엔드포인트
# ============================================================================

# 보고서 생성 요청 모델
class CreateReportRequest(BaseModel):
    user_id: str
    title: str
    description: Optional[str] = None
    content: str
    word_count: int = 0
    video_ids: Optional[List[int]] = None
    video_titles: Optional[List[str]] = None

# 보고서 생성 응답 모델
class CreateReportResponse(BaseModel):
    success: bool
    report_id: Optional[int] = None
    message: str

@app.post("/reports", response_model=CreateReportResponse)
async def create_report(request: CreateReportRequest):
    """보고서 생성"""
    try:
        user_id = request.user_id
        title = request.title
        description = request.description or ""
        content = request.content
        word_count = request.word_count or 0
        video_ids = request.video_ids or []
        video_titles = request.video_titles or []
        
        if not user_id:
            raise HTTPException(status_code=400, detail="사용자 ID가 필요합니다.")
        if not title:
            raise HTTPException(status_code=400, detail="보고서 제목이 필요합니다.")
        if not content:
            raise HTTPException(status_code=400, detail="보고서 내용이 필요합니다.")
        
        verify_user_exists(user_id)
        
        ensure_db_connection()
        
        # vss_reports 테이블이 없으면 생성
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vss_reports (
                    ID INT AUTO_INCREMENT PRIMARY KEY,
                    USER_ID VARCHAR(255) NOT NULL,
                    TITLE VARCHAR(500) NOT NULL,
                    DESCRIPTION TEXT,
                    CONTENT LONGTEXT NOT NULL,
                    WORD_COUNT INT DEFAULT 0,
                    VIDEO_IDS TEXT,
                    VIDEO_TITLES TEXT,
                    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UPDATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_user_id (USER_ID),
                    INDEX idx_created_at (CREATED_AT)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            conn.commit()
            logger.info("vss_reports 테이블 생성 완료 또는 이미 존재함")
        except Exception as e:
            logger.warning(f"vss_reports 테이블 생성/확인 중 오류 (무시됨): {e}")
        
        # 보고서 저장
        video_ids_json = json.dumps(video_ids) if video_ids else None
        video_titles_json = json.dumps(video_titles) if video_titles else None
        
        cursor.execute("""
            INSERT INTO vss_reports (USER_ID, TITLE, DESCRIPTION, CONTENT, WORD_COUNT, VIDEO_IDS, VIDEO_TITLES)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, title, description, content, word_count, video_ids_json, video_titles_json))
        conn.commit()
        
        report_id = cursor.lastrowid
        
        logger.info(f"보고서 생성 완료: USER_ID={user_id}, REPORT_ID={report_id}, TITLE={title}")
        
        return {
            "success": True,
            "report_id": report_id,
            "message": "보고서가 성공적으로 생성되었습니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"보고서 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"보고서 생성 중 오류가 발생했습니다: {str(e)}")

@app.get("/reports")
async def get_reports(
    user_id: str = Query(..., description="사용자 ID"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(10, ge=1, le=100, description="페이지당 항목 수")
):
    """보고서 목록 조회 (페이지네이션 지원)"""
    try:
        if not user_id:
            raise HTTPException(status_code=400, detail="사용자 ID가 필요합니다.")
        
        verify_user_exists(user_id)
        
        ensure_db_connection()
        
        # vss_reports 테이블이 없으면 빈 목록 반환
        try:
            cursor.execute("SELECT COUNT(*) FROM vss_reports WHERE USER_ID = ?", (user_id,))
        except Exception as e:
            # 테이블이 없으면 빈 목록 반환
            logger.warning(f"vss_reports 테이블이 없습니다: {e}")
            return {
                "success": True,
                "reports": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "pages": 0
            }
        
        # 전체 개수 조회
        cursor.execute("SELECT COUNT(*) FROM vss_reports WHERE USER_ID = ?", (user_id,))
        total = cursor.fetchone()[0]
        
        # 페이지네이션 계산
        offset = (page - 1) * page_size
        pages = max(1, (total + page_size - 1) // page_size)
        
        # 보고서 목록 조회 (최신순)
        cursor.execute("""
            SELECT ID, TITLE, DESCRIPTION, CONTENT, WORD_COUNT, VIDEO_IDS, VIDEO_TITLES, CREATED_AT, UPDATED_AT
            FROM vss_reports
            WHERE USER_ID = ?
            ORDER BY CREATED_AT DESC
            LIMIT ? OFFSET ?
        """, (user_id, page_size, offset))
        
        rows = cursor.fetchall()
        
        reports = []
        for row in rows:
            report_id, title, description, content, word_count, video_ids_json, video_titles_json, created_at, updated_at = row
            
            # JSON 문자열 파싱
            video_ids = json.loads(video_ids_json) if video_ids_json else []
            video_titles = json.loads(video_titles_json) if video_titles_json else []
            
            reports.append({
                "id": report_id,
                "report_id": report_id,
                "title": title,
                "description": description or "",
                "content": content or "",
                "word_count": word_count or 0,
                "video_ids": video_ids,
                "video_titles": video_titles,
                "created_at": created_at.isoformat() if created_at else None,
                "createdAt": created_at.isoformat() if created_at else None,
                "updated_at": updated_at.isoformat() if updated_at else None
            })
        
        logger.info(f"보고서 목록 조회 완료: USER_ID={user_id}, 총 {total}개, 페이지 {page}/{pages}")
        
        return {
            "success": True,
            "reports": reports,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"보고서 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"보고서 목록 조회 중 오류가 발생했습니다: {str(e)}")

@app.get("/reports/{report_id}")
async def get_report(
    report_id: int,
    user_id: str = Query(..., description="사용자 ID")
):
    """보고서 상세 조회"""
    try:
        if not user_id:
            raise HTTPException(status_code=400, detail="사용자 ID가 필요합니다.")
        
        verify_user_exists(user_id)
        
        ensure_db_connection()
        
        # 보고서 조회
        cursor.execute("""
            SELECT ID, TITLE, DESCRIPTION, CONTENT, WORD_COUNT, VIDEO_IDS, VIDEO_TITLES, CREATED_AT, UPDATED_AT
            FROM vss_reports
            WHERE ID = ? AND USER_ID = ?
        """, (report_id, user_id))
        
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다.")
        
        report_id_db, title, description, content, word_count, video_ids_json, video_titles_json, created_at, updated_at = row
        
        # JSON 문자열 파싱
        video_ids = json.loads(video_ids_json) if video_ids_json else []
        video_titles = json.loads(video_titles_json) if video_titles_json else []
        
        return {
            "success": True,
            "report": {
                "id": report_id_db,
                "report_id": report_id_db,
                "title": title,
                "description": description or "",
                "content": content or "",
                "word_count": word_count or 0,
                "video_ids": video_ids,
                "video_titles": video_titles,
                "created_at": created_at.isoformat() if created_at else None,
                "createdAt": created_at.isoformat() if created_at else None,
                "updated_at": updated_at.isoformat() if updated_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"보고서 상세 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"보고서 상세 조회 중 오류가 발생했습니다: {str(e)}")

@app.delete("/reports/{report_id}")
async def delete_report(
    report_id: int,
    user_id: str = Query(..., description="사용자 ID")
):
    """보고서 삭제"""
    try:
        if not user_id:
            raise HTTPException(status_code=400, detail="사용자 ID가 필요합니다.")
        
        verify_user_exists(user_id)
        
        ensure_db_connection()
        
        # 보고서 소유권 확인 및 삭제
        cursor.execute("""
            DELETE FROM vss_reports
            WHERE ID = ? AND USER_ID = ?
        """, (report_id, user_id))
        conn.commit()
        
        deleted_count = cursor.rowcount
        
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="보고서를 찾을 수 없거나 권한이 없습니다.")
        
        logger.info(f"보고서 삭제 완료: USER_ID={user_id}, REPORT_ID={report_id}")
        
        return {
            "success": True,
            "message": "보고서가 성공적으로 삭제되었습니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"보고서 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=f"보고서 삭제 중 오류가 발생했습니다: {str(e)}")

# CORS 설정 (Vue와 통신 가능하게)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영에서는 도메인 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 aiohttp 세션 생성 및 DB 연결 확인"""
    await get_session()
    
    # 데이터베이스 연결 확인 (실패해도 애플리케이션은 계속 시작)
    global conn, cursor
    if conn is None or cursor is None:
        try:
            conn = db_pool.get_connection()
            conn.autocommit = True
            cursor = conn.cursor()
            logger.info("데이터베이스 연결 성공 (startup)")
        except Exception as e:
            logger.warning(f"데이터베이스 연결 실패 (startup): {e}")
            logger.warning("첫 요청 시 연결을 다시 시도합니다.")
    
    logger.info("애플리케이션이 시작되었습니다. VIA 서버의 query_video를 사용합니다.")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 aiohttp 세션 종료"""
    global http_session
    if http_session and not http_session.closed:
        await http_session.close()
