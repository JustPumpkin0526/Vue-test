# ============================================================================
# 표준 라이브러리
# ============================================================================
import os
import re
import json
import time
import random
import shutil
import asyncio
import smtplib
import pathlib
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ============================================================================
# 서드파티 라이브러리
# ============================================================================
import aiohttp
import mariadb
import bcrypt
from fastapi import FastAPI, File, Form, UploadFile, Body, HTTPException, Request, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.logger import logger
from pydantic import BaseModel
from moviepy.video.io.VideoFileClip import VideoFileClip

# ============================================================================
# 환경 변수 로드
# ============================================================================
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

# ============================================================================
# FastAPI 애플리케이션 초기화
# ============================================================================
app = FastAPI()

# ============================================================================
# 정적 파일 디렉토리 설정
# ============================================================================
# 클립 파일 서빙
os.makedirs("./clips", exist_ok=True)
app.mount("/clips", StaticFiles(directory="clips"), name="clips")

# 업로드된 동영상 파일 서빙 (API 엔드포인트와 충돌 방지)
videos_dir = Path("./videos")
videos_dir.mkdir(exist_ok=True)
app.mount("/video-files", StaticFiles(directory=str(videos_dir.resolve())), name="video-files")

# 샘플 동영상 파일 서빙
current_dir = Path(__file__).parent  # src/api/
sample_dir = current_dir.parent / "assets" / "sample"
sample_dir = sample_dir.resolve()  # 절대 경로로 변환
os.makedirs(sample_dir, exist_ok=True)
logger.info(f"Serving sample videos from: {sample_dir}")

# sample.mp4 파일 존재 여부 확인
sample_file = sample_dir / "sample.mp4"
if sample_file.exists():
    logger.info(f"Sample video file found: {sample_file}")
else:
    logger.warning(f"Sample video file NOT found at: {sample_file}")
    logger.warning(f"Please ensure sample.mp4 exists in: {sample_dir}")

try:
    app.mount("/sample", StaticFiles(directory=str(sample_dir)), name="sample")
    logger.info(f"Successfully mounted /sample endpoint to {sample_dir}")
except Exception as e:
    logger.error(f"Failed to mount /sample endpoint: {e}")

# ============================================================================
# 환경 변수 및 설정
# ============================================================================
# ============================================================================
# 환경 변수 및 설정
# ============================================================================
# VIA 서버 설정
VIA_SERVER_URL = os.getenv("VIA_SERVER_URL", "http://172.16.7.64:8101")

# Ollama 설정
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# ============================================================================
# 전역 변수
# ============================================================================
# 전역 aiohttp 세션
http_session: Optional[aiohttp.ClientSession] = None

# 전역 VSS 클라이언트 (지연 초기화)
vss_client = None

async def get_session():
    """전역 aiohttp 세션 가져오기 또는 생성"""
    global http_session
    if http_session is None or http_session.closed:
        http_session = aiohttp.ClientSession()
    return http_session

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
        logger.debug(f"Response Status Code: {response.status}")
        if response.status == 200:
            try:
                return await response.json()
            except Exception:
                logger.warning("JSON decode error, returning text.")
                return await response.text()
        else:
            text = await response.text()
            logger.error(f"서버 에러: {response.status}, {text}")
            return text

    async def get_model(self):
        session = await get_session()
        try:
            async with session.get(self.models_endpoint, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                json_data = await self.check_response(resp)
                try:
                    return json_data["data"][0]["id"]  # get configured model name
                except Exception as e:
                    raise HTTPException(status_code=502, detail=f"Invalid response from VIA /models: {e}")
        except Exception as e:
            # Raise HTTPException so FastAPI returns a proper error response (and CORS headers)
            raise HTTPException(status_code=502, detail=f"Failed to reach VIA server for models: {e}")

    async def upload_video(self, video_path):
        session = await get_session()
        data = aiohttp.FormData()
        
        # 파일을 스트리밍 방식으로 전송 (메모리에 전체 로드하지 않음)
        # 파일 핸들을 직접 전달하여 메모리 효율성 향상
        file_handle = open(video_path, "rb")
        try:
            # 파일 크기 확인 (로깅용)
            file_size = os.path.getsize(video_path)
            logger.info(f"Uploading video file: {video_path} (size: {file_size / (1024*1024):.2f} MB)")
            
            data.add_field("file", file_handle, filename=f"file_{self.f_count}")
            data.add_field("purpose", "vision")
            data.add_field("media_type", "video")
            
            # 타임아웃 설정: 큰 파일 업로드를 위해 충분한 시간 할당
            # 파일 크기에 따라 동적으로 타임아웃 계산 (최소 60초, 최대 600초)
            timeout_seconds = max(60, min(600, int(file_size / (1024 * 1024) * 10)))  # 1MB당 10초, 최소 60초, 최대 600초
            
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

# ============================================================================
# 상수 정의
# ============================================================================
DEFAULT_VIA_TARGET_RESPONSE_TIME = 2 * 60  # in seconds
DEFAULT_VIA_TARGET_USECASE_EVENT_DURATION = 10  # in seconds

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


def parse_timestamps(timestamp_text: str, video_duration: float):
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


async def get_recommended_chunk_size(video_length):
    """
    aiohttp를 사용하여 비동기 방식으로 API 호출
    """
    # In seconds:
    target_response_time = DEFAULT_VIA_TARGET_RESPONSE_TIME
    usecase_event_duration = DEFAULT_VIA_TARGET_USECASE_EVENT_DURATION
    recommended_chunk_size = 0

    try:
        session = await get_session()
        async with session.post(
            VIA_SERVER_URL + "/recommended_config",
            json={
                "video_length": int(video_length),
                "target_response_time": int(target_response_time),
                "usecase_event_duration": int(usecase_event_duration),
            },
            timeout=aiohttp.ClientTimeout(total=10)
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

# ============================================================================
# 요청/응답 모델 정의
# ============================================================================
class RecommendedChunkSizeRequest(BaseModel):
    video_length: float

@app.post("/get-recommended-chunk-size")
async def get_recommended_chunk_size_endpoint(request: RecommendedChunkSizeRequest):
    """
    동영상 길이를 받아서 추천 chunk_size를 반환하는 엔드포인트
    """
    try:
        # 입력 검증
        if request.video_length <= 0:
            raise HTTPException(status_code=400, detail="동영상 길이는 0보다 커야 합니다.")
        if request.video_length > 86400:  # 24시간 초과
            raise HTTPException(status_code=400, detail="동영상 길이는 24시간(86400초)을 초과할 수 없습니다.")
        
        recommended_chunk_size = await get_recommended_chunk_size(request.video_length)
        return {"recommended_chunk_size": recommended_chunk_size, "video_length": request.video_length}
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"입력 값 오류: {e}")
        raise HTTPException(status_code=400, detail=f"잘못된 입력 값입니다: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting recommended chunk size: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"추천 chunk size 조회 중 오류가 발생했습니다: {str(e)}")

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

class RemoveMediaRequest(BaseModel):
    media_ids: List[str]

@app.post("/remove-media")
async def remove_media_endpoint(request: RemoveMediaRequest):
    """
    VIA 서버에서 미디어 파일들을 삭제하는 엔드포인트
    """
    try:
        # 입력 검증
        if not request.media_ids or len(request.media_ids) == 0:
            raise HTTPException(status_code=400, detail="삭제할 미디어 ID 목록이 필요합니다.")
        
        session = await get_session()
        await remove_all_media(session, request.media_ids)
        return {"success": True, "message": f"Deleted {len(request.media_ids)} media file(s)"}
    except HTTPException:
        raise
    except aiohttp.ClientError as e:
        logger.error(f"VIA 서버 연결 오류: {e}")
        raise HTTPException(status_code=502, detail=f"VIA 서버에 연결할 수 없습니다: {str(e)}")
    except Exception as e:
        logger.error(f"Error removing media: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"미디어 삭제 중 오류가 발생했습니다: {str(e)}")

@app.post("/generate-clips")
async def generate_clips(
    request: Request,
    files: List[UploadFile] = File(None),
    prompt: str = Form(...),
    user_id: Optional[str] = Form(None),
    video_ids: Optional[str] = Form(None)  # JSON 문자열로 전달: {"filename1": video_id1, "filename2": video_id2}
):
    """
    동영상에서 클립 생성 엔드포인트
    """
    try:
        # 입력 검증
        if not prompt or not prompt.strip():
            raise HTTPException(status_code=400, detail="검색어(prompt)를 입력해주세요.")
        
        prompt = prompt.strip()
        
        # 클립 저장 디렉토리 생성
        try:
            os.makedirs("./clips", exist_ok=True)
        except OSError as e:
            logger.error(f"클립 디렉토리 생성 실패: {e}")
            raise HTTPException(status_code=500, detail="클립 저장 디렉토리를 생성할 수 없습니다.")
        
        # 오래된 클립 파일 정리 (24시간 이상 된 파일만 삭제)
        try:
            current_time = time.time()
            clips_dir = Path("./clips")
            if clips_dir.exists():
                for existing_file in os.listdir("./clips"):
                    file_path = os.path.join("./clips", existing_file)
                    try:
                        if os.path.isfile(file_path):
                            # 파일 수정 시간 확인
                            file_mtime = os.path.getmtime(file_path)
                            # 24시간(86400초) 이상 된 파일만 삭제
                            if current_time - file_mtime > 86400:
                                os.remove(file_path)
                                logger.info(f"Deleted old clip: {file_path}")
                    except OSError as e:
                        logger.warning(f"오래된 클립 파일 삭제 실패 {file_path}: {e}")
                    except Exception as e:
                        logger.error(f"Error deleting old clip {file_path}: {e}")
        except OSError as e:
            logger.warning(f"클립 디렉토리 접근 실패: {e}")
        except Exception as e:
            logger.warning(f"Error cleaning old clips: {e}")

        global vss_client

        # 파일 목록 초기화
        upload_list = []
        if files:
            upload_list.extend(files)

        if not upload_list:
            raise HTTPException(status_code=400, detail="No file provided")

        # 임시 디렉토리 생성
        try:
            os.makedirs("./tmp", exist_ok=True)
        except OSError as e:
            logger.error(f"임시 디렉토리 생성 실패: {e}")
            raise HTTPException(status_code=500, detail="임시 디렉토리를 생성할 수 없습니다.")
        
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

            # VIA 서버 클라이언트 초기화 및 모델 조회
            if vss_client is None:
                vss_client = VSS(VIA_SERVER_URL)
            
            try:
                if not vss_client.model:
                    vss_client.model = await vss_client.get_model()
                model = vss_client.model
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=502, detail=f"Failed to contact VIA server: {e}")

            # 업로드용 임시 파일 실제 저장 (기존 누락으로 인해 FileNotFoundError / 빈 처리 발생 가능)
            try:
                with open(tmp_path, "wb") as buffer:
                    shutil.copyfileobj(upfile.file, buffer)
            except OSError as e:
                logger.error(f"임시 파일 저장 실패: {tmp_path}, 오류: {e}")
                raise HTTPException(status_code=500, detail=f"파일 저장 중 오류가 발생했습니다: {str(e)}")
            except Exception as e:
                logger.error(f"파일 저장 중 예상치 못한 오류: {e}")
                raise HTTPException(status_code=500, detail=f"파일 저장 중 오류가 발생했습니다: {str(e)}")

            logger.info(f"Uploaded video saved to {tmp_path}")

            # video_ids에서 내부 DB ID 가져오기 (VIA 서버의 video_id로 변환 필요)
            video_id = None
            db_internal_id = None
            if user_id and video_id_map:
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
                try:
                    video_id = await vss_client.upload_video(tmp_path)
                    logger.info(f"VIA 서버에 업로드하여 video_id 획득: {video_id}")
                except aiohttp.ClientError as e:
                    logger.error(f"VIA 서버 업로드 연결 오류: {e}")
                    raise HTTPException(status_code=502, detail=f"VIA 서버에 연결할 수 없습니다: {str(e)}")
                except Exception as e:
                    logger.error(f"VIA 서버 업로드 실패: {e}")
                    raise HTTPException(status_code=500, detail=f"VIA 서버에 파일 업로드 중 오류가 발생했습니다: {str(e)}")

            video_clips = []
            video = None
            # MoviePy에 파일 경로(문자열)로 전달
            try:
                if not os.path.exists(tmp_path):
                    raise HTTPException(status_code=404, detail=f"임시 파일을 찾을 수 없습니다: {tmp_path}")
                
                video = VideoFileClip(tmp_path)
                duration = video.duration or 0
                if duration <= 0:
                    raise HTTPException(status_code=400, detail="동영상 길이가 유효하지 않습니다.")
                logger.info(f"Video duration: {duration} seconds for {tmp_path}")
            except FileNotFoundError as e:
                logger.error(f"동영상 파일을 찾을 수 없음: {tmp_path}, 오류: {e}")
                raise HTTPException(status_code=404, detail=f"동영상 파일을 찾을 수 없습니다: {str(e)}")
            except Exception as e:
                logger.error(f"동영상 파일 로드 실패: {tmp_path}, 오류: {e}")
                raise HTTPException(status_code=500, detail=f"동영상 파일을 로드할 수 없습니다: {str(e)}")
            
            # chunk_duration 계산: 동영상 길이의 1/10을 가장 가까운 값으로 반올림
            try:
                chunk_duration = await get_recommended_chunk_size(duration)
            except Exception as e:
                logger.warning(f"추천 chunk_size 조회 실패, 기본값 사용: {e}")
                chunk_duration = duration  # 기본값으로 동영상 전체 길이 사용

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
                        logger.info(f"저장된 요약 결과 발견: VIDEO_ID {video_id}, summarize_video 건너뛰기")
                except mariadb.Error as e:
                    logger.warning(f"요약 결과 확인 중 데이터베이스 오류: {e}")
                except Exception as e:
                    logger.warning(f"요약 결과 확인 중 오류: {e}")

            # 저장된 요약이 있으면 summarize_video 건너뛰기
            if not has_stored_summary:
                result = await vss_client.summarize_video(
                    video_id,
                    "You are a crime CCTV detection system. Please analyze and explain various crimes, including criminal activity, weapon possession, and escape attempts. Please also output timestamps in the form of start and end times.",
                    "You will be given captions from sequential clips of a video. Aggregate captions in the format start_time:end_time:caption based on whether captions are related to one another or create a continuous scene.",
                    "Based on the available information, generate a summary that captures the important events in the video. The summary should be organized chronologically and in logical sections. This should be a concise, yet descriptive summary of all the important events. The format should be intuitive and easy for a user to read and understand what happened. Format the output in Markdown so it can be displayed nicely. Timestamps are in seconds so please format them as SS.SSS",
                    chunk_duration,
                    model,
                    chunk_duration // 3,
                    0,
                    0,
                    100,
                    1.0,
                    0.4,
                    512,
                    1,
                    6,
                    1,
                    5,
                    0.7,
                    0.2,
                    2048,
                    0.7,
                    0.2,
                    2048,
                    0.7,
                    0.2,
                    2048,
                    True  # enable_audio
                )
                
                # 요약 결과를 DB에 저장
                if user_id and video_id and result:
                    try:
                        # 요약 텍스트 추출 (result가 문자열인 경우 그대로 사용, dict인 경우 content 추출)
                        summary_text = result
                        if isinstance(result, dict):
                            summary_text = result.get("content", str(result))
                        elif not isinstance(result, str):
                            summary_text = str(result)
                        
                        # vss_summaries 테이블에 저장 또는 업데이트
                        cursor.execute(
                            """INSERT INTO vss_summaries (VIDEO_ID, USER_ID, SUMMARY_TEXT) 
                               VALUES (?, ?, ?)
                               ON DUPLICATE KEY UPDATE 
                               SUMMARY_TEXT = VALUES(SUMMARY_TEXT),
                               UPDATED_AT = CURRENT_TIMESTAMP""",
                            (video_id, user_id, summary_text)
                        )
                        conn.commit()
                        logger.info(f"요약 결과 DB 저장 완료: VIDEO_ID={video_id}, USER_ID={user_id}")
                    except mariadb.Error as e:
                        logger.error(f"요약 결과 DB 저장 중 데이터베이스 오류: {e}")
                        # DB 저장 실패해도 요약은 계속 진행
                    except Exception as e:
                        logger.error(f"요약 결과 DB 저장 실패: {e}")
                        # DB 저장 실패해도 요약은 계속 진행
            else:
                logger.info(f"저장된 요약 결과가 있어 summarize_video를 건너뜁니다. 바로 query_video로 진행합니다.")
            
            # prompt를 질문으로 처리: VIA 서버의 query_video 사용
            # 동영상 컨텍스트를 직접 활용하여 질문에 답변
            try:                
                # query_video 파라미터 설정
                query_chunk_size = chunk_duration  # 요약에 사용한 chunk_duration과 동일하게
                query_temperature = 0.3
                query_seed = 1
                query_max_tokens = 512  # VIA 서버는 최대 1024까지만 허용
                query_top_p = 1
                query_top_k = 100

                prompt += "이에 해당하는 장면의 시작 시간과 끝 시간의 타임스탬프를 출력해주세요. 타임스탬프만 출력하고 다른 설명은 포함하지 말아야 합니다."
                
                # VIA 서버로 질문 전달
                query_result = await vss_client.query_video(
                    video_id,
                    model,
                    query_chunk_size,
                    query_temperature,
                    query_seed,
                    query_max_tokens,
                    query_top_p,
                    query_top_k,
                    prompt  # 사용자가 입력한 prompt를 질문으로 전달
                )
                
                # query_result를 Ollama LLM에 보내서 타임스탬프만 추출
                extracted_timestamps_text = None
                try:
                    
                    # Ollama API 호출을 위한 프롬프트 구성
                    timestamp_extraction_prompt = f"""다음은 동영상 질의 응답 결과입니다:
{query_result}

위 응답에서 타임스탬프만 추출하여 출력해주세요. 타임스탬프 형식은 초 단위(예: 10.5, 120.3) 또는 분:초 형식(예: 1:30, 2:45)일 수 있습니다. 타임스탬프만 출력하고 다른 설명은 포함하지 마세요."""
                    
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
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as ollama_response:
                        if ollama_response.status == 200:
                            ollama_data = await ollama_response.json()
                            extracted_timestamps_text = ollama_data.get("message", {}).get("content", "")
                            if extracted_timestamps_text:
                                extracted_timestamps_text = extracted_timestamps_text.strip()
                            else:
                                logger.warning("Ollama 응답에 content가 없습니다.")
                        else:
                            error_text = await ollama_response.text()
                            logger.warning(f"Ollama API 호출 실패 (HTTP {ollama_response.status}): {error_text}")
                except aiohttp.ClientConnectorError as e:
                    logger.warning(f"Ollama 서버에 연결할 수 없습니다: {e}")
                    logger.warning("Ollama가 실행 중인지 확인하세요: ollama serve")
                except Exception as e:
                    logger.warning(f"Ollama를 사용한 타임스탬프 추출 중 오류 발생: {e}")
                
                logger.debug(f"VIA 서버 답변: {query_result}")
                
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
                        except OSError as e:
                            logger.error(f"클립 파일 생성 중 파일 시스템 오류 {clip_filename}: {e}")
                        except Exception as e:
                            logger.error(f"Error generating clip {clip_filename}: {e}", exc_info=True)
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
            # 리소스 정리
            if video is not None:
                try:
                    video.close()
                except Exception as e:
                    logger.warning(f"동영상 리소스 정리 중 오류: {e}")
                del video

            grouped_clips.append({
                "video": file_path,
                "clips": video_clips
            })

    except HTTPException:
        raise
    except aiohttp.ClientError as e:
        logger.error(f"VIA 서버 연결 오류: {e}")
        raise HTTPException(status_code=502, detail=f"VIA 서버에 연결할 수 없습니다: {str(e)}")
    except FileNotFoundError as e:
        logger.error(f"파일을 찾을 수 없음: {e}")
        raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {str(e)}")
    except OSError as e:
        logger.error(f"파일 시스템 오류: {e}")
        raise HTTPException(status_code=500, detail=f"파일 처리 중 오류가 발생했습니다: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {e}")
        raise HTTPException(status_code=400, detail=f"잘못된 JSON 형식입니다: {str(e)}")
    except mariadb.Error as e:
        logger.error(f"데이터베이스 오류: {e}")
        raise HTTPException(status_code=500, detail=f"데이터베이스 오류가 발생했습니다: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing uploaded video(s): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"동영상 처리 중 오류가 발생했습니다: {str(e)}")

    # 클립 추출 여부 확인 (실제 URL이 있는 클립이 있는지 확인)
    clips_extracted = False
    try:
        for group in grouped_clips:
            for clip in group.get("clips", []):
                # url이 있고 via_response가 없는 경우에만 추출된 것으로 간주
                if clip.get("url") and not clip.get("via_response"):
                    clips_extracted = True
                    break
            if clips_extracted:
                break
    except Exception as e:
        logger.warning(f"클립 추출 여부 확인 중 오류: {e}")
    
    logger.info("All clips generated successfully.")
    logger.debug(f"Returned clips payload: {json.dumps({'clips': grouped_clips, 'clips_extracted': clips_extracted}, ensure_ascii=False)}")
    return JSONResponse(content={"clips": grouped_clips, "clips_extracted": clips_extracted})


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
    global vss_client
    if vss_client is None:
        vss_client = VSS(VIA_SERVER_URL)
        vss_client.model = await vss_client.get_model()

    # GET models from VIA server (async aiohttp)
    session = await get_session()
    try:
        async with session.get(VIA_SERVER_URL + "/models", timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status >= 400:
                raise HTTPException(status_code=502, detail=f"VIA /models returned status {resp.status}")
            try:
                resp_json = await resp.json()
            except Exception:
                raise HTTPException(status_code=502, detail=f"VIA /models returned invalid JSON")
            model = resp_json["data"][0]["id"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to contact VIA server: {e}")

    # video_id 검증
    if not video_id:
        raise HTTPException(status_code=400, detail="video_id가 필요합니다. 이미 업로드된 동영상의 video_id를 제공해주세요.")

    try:
        result = await vss_client.summarize_video(
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
            enable_audio,
        )
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
                detail=(
                    "동영상 파일 처리 중 오류가 발생했습니다.\n\n"
                    "가능한 원인:\n"
                    "1. 손상된 동영상 파일 - 파일을 다시 다운로드하거나 다른 파일로 시도해보세요.\n"
                    "2. 지원하지 않는 코덱 또는 포맷 - H.264 코덱의 MP4 파일을 권장합니다.\n"
                    "3. 파일이 완전히 업로드되지 않음 - 네트워크 연결을 확인하고 다시 시도해보세요.\n"
                    "4. 파일 메타데이터 문제 - 동영상 편집 프로그램으로 파일을 다시 저장해보세요.\n\n"
                    f"기술적 오류: {error_msg}"
                )
            )
        else:
            raise HTTPException(status_code=500, detail=f"요약 생성 중 오류가 발생했습니다: {error_msg}")

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
    """
    동영상 질의 응답 엔드포인트
    """
    try:
        # 입력 검증
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="질문을 입력해주세요.")
        
        query = query.strip()
        
        if chunk_size < 0:
            raise HTTPException(status_code=400, detail="chunk_size는 0 이상이어야 합니다.")
        if not (0 <= temperature <= 2):
            raise HTTPException(status_code=400, detail="temperature는 0과 2 사이의 값이어야 합니다.")
        if max_new_tokens <= 0:
            raise HTTPException(status_code=400, detail="max_new_tokens는 0보다 커야 합니다.")
        if not (0 <= top_p <= 1):
            raise HTTPException(status_code=400, detail="top_p는 0과 1 사이의 값이어야 합니다.")
        if top_k < 0:
            raise HTTPException(status_code=400, detail="top_k는 0 이상이어야 합니다.")
        
        # video_id 또는 file 중 하나는 필요
        if not video_id and not file:
            raise HTTPException(status_code=400, detail="video_id 또는 file 중 하나는 필요합니다.")
        
        # 전역 vss_client 사용 선언 (누락 시 UnboundLocalError 발생)
        global vss_client
        
        if vss_client is None:
            vss_client = VSS(VIA_SERVER_URL)
            vss_client.model = await vss_client.get_model()
        
        # VIA 서버 모델 조회
        session = await get_session()
        try:
            async with session.get(VIA_SERVER_URL + "/models", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status >= 400:
                    raise HTTPException(status_code=502, detail=f"VIA /models returned status {resp.status}")
                try:
                    resp_json = await resp.json()
                except Exception as e:
                    raise HTTPException(status_code=502, detail=f"VIA /models returned invalid JSON: {str(e)}")
                if not resp_json.get("data") or len(resp_json["data"]) == 0:
                    raise HTTPException(status_code=502, detail="VIA 서버에서 모델을 찾을 수 없습니다.")
                model = resp_json["data"][0]["id"]
        except HTTPException:
            raise
        except aiohttp.ClientError as e:
            logger.error(f"VIA 서버 연결 오류: {e}")
            raise HTTPException(status_code=502, detail=f"VIA 서버에 연결할 수 없습니다: {str(e)}")
        except Exception as e:
            logger.error(f"VIA 서버 모델 조회 중 오류: {e}")
            raise HTTPException(status_code=502, detail=f"VIA 서버 모델 조회 중 오류가 발생했습니다: {str(e)}")
        
        # 파일이 제공된 경우 업로드
        if file and not video_id:
            try:
                if not file.filename:
                    raise HTTPException(status_code=400, detail="파일명이 없습니다.")
                
                os.makedirs("./tmp", exist_ok=True)
                file_path = f"./tmp/{file.filename}"
                try:
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                except OSError as e:
                    logger.error(f"임시 파일 저장 실패: {e}")
                    raise HTTPException(status_code=500, detail=f"파일 저장 중 오류가 발생했습니다: {str(e)}")
                
                try:
                    video_id = await vss_client.upload_video(file_path)
                except Exception as e:
                    logger.error(f"VIA 서버 업로드 실패: {e}")
                    raise HTTPException(status_code=500, detail=f"VIA 서버에 파일 업로드 중 오류가 발생했습니다: {str(e)}")
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"파일 처리 중 오류: {e}")
                raise HTTPException(status_code=500, detail=f"파일 처리 중 오류가 발생했습니다: {str(e)}")
        
        if not video_id:
            raise HTTPException(status_code=400, detail="video_id가 필요합니다.")

        query += " 이에 해당하는 장면의 시작 시간과 끝 시간의 타임스탬프를 출력해주세요. "
        
        try:
            result = await vss_client.query_video(video_id, model, chunk_size, temperature, seed, max_new_tokens, top_p, top_k, query)
        except HTTPException:
            raise
        except aiohttp.ClientError as e:
            logger.error(f"VIA 서버 query_video 연결 오류: {e}")
            raise HTTPException(status_code=502, detail=f"VIA 서버에 연결할 수 없습니다: {str(e)}")
        except Exception as e:
            logger.error(f"VIA 서버 query_video 실행 중 오류: {e}")
            raise HTTPException(status_code=500, detail=f"동영상 질의 처리 중 오류가 발생했습니다: {str(e)}")

        return {"summary": result, "video_id": video_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"vss_query 실행 중 예상치 못한 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"동영상 질의 처리 중 오류가 발생했습니다: {str(e)}")



# ============================================================================
# 요청/응답 모델 정의
# ============================================================================
class LoginRequest(BaseModel):
    username: str
    password: str

class VideoUploadResponse(BaseModel):
    success: bool
    video_id: int
    file_url: str
    message: str

# ============================================================================
# 데이터베이스 연결 풀
# ============================================================================
import threading
from queue import Queue, Empty

# ============================================================================
# 데이터베이스 연결 풀 클래스
# ============================================================================
class ConnectionPool:
    """DB 커넥션 풀 (동시 요청 처리 최적화)"""
    def __init__(self, max_connections=10, **kwargs):
        self.max_connections = max_connections
        self.connection_kwargs = kwargs
        self.pool = Queue(maxsize=max_connections)
        self.lock = threading.Lock()
        self.created_connections = 0
        
        # 초기 연결 생성
        for _ in range(min(3, max_connections)):  # 최소 3개 연결 미리 생성
            conn = self._create_connection()
            self.pool.put(conn)
            self.created_connections += 1
    
    def _create_connection(self):
        """새 DB 연결 생성"""
        conn = mariadb.connect(
            autocommit=True,  # 자동 커밋으로 성능 향상
            **self.connection_kwargs
        )
        return conn
    
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
db_pool = ConnectionPool(
    max_connections=20,
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", "pass0001!"),
    host=os.getenv("DB_HOST", "172.16.15.69"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME", "vss")
)

# ============================================================================
# 전역 데이터베이스 연결 (하위 호환성을 위한 점진적 마이그레이션용)
# ============================================================================
# 모듈 레벨에서 연결을 시도하되, 실패해도 애플리케이션 시작은 계속 진행
# 실제 사용 시점에 연결을 다시 시도하도록 함
conn = None
cursor = None

try:
    conn = db_pool.get_connection()
    conn.autocommit = True
    cursor = conn.cursor()
    logger.info("✓ 데이터베이스 연결 성공 (전역 연결)")
except Exception as e:
    logger.warning(f"⚠️ 전역 데이터베이스 연결 실패 (시작 시점): {e}")
    logger.warning("⚠️ 첫 요청 시 연결을 다시 시도합니다.")
    conn = None
    cursor = None

def get_db_connection():
    """DB 연결 가져오기 (컨텍스트 매니저)"""
    return DBConnectionContext()

def ensure_db_connection():
    """전역 DB 연결이 없으면 다시 시도"""
    global conn, cursor
    if conn is None or cursor is None:
        try:
            conn = db_pool.get_connection()
            conn.autocommit = True
            cursor = conn.cursor()
            logger.info("✓ 데이터베이스 연결 성공 (재연결)")
        except Exception as e:
            logger.error(f"❌ 데이터베이스 연결 실패: {e}")
            raise HTTPException(status_code=500, detail=f"데이터베이스 연결에 실패했습니다: {str(e)}")

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

# ============================================================================
# SMTP 설정
# ============================================================================
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)

# SMTP 설정 로드 확인 로깅
if SMTP_USER and SMTP_PASSWORD:
    logger.info(f"SMTP 설정 로드 완료: SERVER={SMTP_SERVER}, PORT={SMTP_PORT}, USER={SMTP_USER[:3]}***")
else:
    logger.warning("⚠️ SMTP 설정이 로드되지 않았습니다!")
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
    """만료된 이메일 인증 코드 정리"""
    current_time = datetime.now()
    expired_emails = [
        email for email, data in email_verification_codes.items()
        if data["expires_at"] < current_time
    ]
    for email in expired_emails:
        del email_verification_codes[email]

# ============================================================================
# API 엔드포인트: 사용자 인증
# ============================================================================
@app.post("/login")
def login(data: LoginRequest = Body(...)):
    """
    사용자 로그인 처리
    """
    try:
        # 입력 검증
        if not data.username or not data.username.strip():
            raise HTTPException(status_code=400, detail="사용자 ID를 입력해주세요.")
        if not data.password or not data.password.strip():
            raise HTTPException(status_code=400, detail="비밀번호를 입력해주세요.")
        
        username = data.username.strip()
        password = data.password
        
        # DB 연결 확인
        try:
            cursor.execute(
                "SELECT PW FROM vss_user WHERE ID = ?",
                (username,)
            )
            row = cursor.fetchone()
        except mariadb.Error as e:
            logger.error(f"데이터베이스 조회 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
        if row is None:
            # ID가 없는 경우
            return {"success": False, "message": "계정이 없습니다."}
        
        db_pw = row[0]
        
        # 해시화된 비밀번호와 입력된 비밀번호 비교
        # 기존 데이터베이스에 평문 비밀번호가 있을 수 있으므로 둘 다 확인
        password_correct = False
        try:
            # bcrypt 해시로 저장된 경우
            if bcrypt.checkpw(password.encode('utf-8'), db_pw.encode('utf-8')):
                password_correct = True
        except (ValueError, AttributeError) as e:
            # bcrypt 해시가 아닌 경우 (기존 평문 비밀번호 호환성 유지)
            # 새로운 회원가입은 모두 해시화되므로 이 부분은 점진적으로 제거 가능
            if db_pw == password:
                password_correct = True
                # 기존 평문 비밀번호를 해시화하여 업데이트 (마이그레이션)
                try:
                    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                    cursor.execute(
                        "UPDATE vss_user SET PW = ? WHERE ID = ?",
                        (hashed_password.decode('utf-8'), username)
                    )
                    conn.commit()
                    logger.info(f"비밀번호를 해시화하여 업데이트했습니다: {username}")
                except mariadb.Error as db_err:
                    logger.warning(f"비밀번호 해시화 업데이트 실패: {db_err}")
                except Exception as e:
                    logger.warning(f"비밀번호 해시화 업데이트 중 예상치 못한 오류: {e}")
        except Exception as e:
            logger.error(f"비밀번호 검증 중 오류: {e}")
            raise HTTPException(status_code=500, detail="비밀번호 검증 중 오류가 발생했습니다.")
        
        if password_correct:
            return {"success": True}
        else:
            # ID는 있지만 비밀번호가 틀린 경우
            return {"success": False, "message": "비밀번호가 틀렸습니다."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"로그인 처리 중 예상치 못한 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"로그인 처리 중 오류가 발생했습니다: {str(e)}")

class SendVerificationCodeRequest(BaseModel):
    email: str

class VerifyEmailRequest(BaseModel):
    email: str
    code: str

class User(BaseModel):
    username: str
    password: str
    email: str
    verification_code: str

# ============================================================================
# API 엔드포인트: 디버깅
# ============================================================================
@app.get("/debug/email-check/{email}")
def debug_email_check(email: str):
    """이메일 검증 디버깅용 엔드포인트"""
    try:
        if not email or not email.strip():
            raise HTTPException(status_code=400, detail="이메일 주소를 입력해주세요.")
        
        email_lower = email.strip().lower()
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        is_valid_format = bool(re.match(email_regex, email_lower))
        
        try:
            cursor.execute("SELECT ID FROM vss_user WHERE EMAIL = ?", (email_lower,))
            existing_user = cursor.fetchone()
        except mariadb.Error as e:
            logger.error(f"데이터베이스 조회 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
        is_existing = existing_user is not None
        
        return {
            "email": email_lower,
            "is_valid_format": is_valid_format,
            "is_existing": is_existing,
            "existing_user_id": existing_user[0] if existing_user else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이메일 검증 디버깅 중 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"이메일 검증 중 오류가 발생했습니다: {str(e)}")

@app.post("/send-verification-code")
def send_verification_code(request: SendVerificationCodeRequest):
    """이메일 인증 코드 전송"""
    try:
        # 요청 데이터 로깅
        logger.info(f"인증 코드 전송 요청 수신: {request.email}")
        
        if not request.email or not request.email.strip():
            logger.warning("이메일이 비어있습니다.")
            raise HTTPException(status_code=400, detail="이메일 주소를 입력해주세요.")
        
        email = request.email.strip().lower()
        logger.info(f"처리할 이메일: {email}")
        
        # 이메일 형식 검증
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            logger.warning(f"이메일 형식 검증 실패: {email}")
            raise HTTPException(status_code=400, detail="올바른 이메일 형식이 아닙니다.")
        
        # 기존 사용자 이메일 중복 확인
        try:
            cursor.execute("SELECT ID FROM vss_user WHERE EMAIL = ?", (email,))
            existing_user = cursor.fetchone()
            if existing_user:
                logger.warning(f"이미 사용 중인 이메일: {email}")
                raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")
        except Exception as db_error:
            logger.error(f"데이터베이스 조회 오류: {db_error}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
        # 만료된 코드 정리
        cleanup_expired_codes()
        
        # 인증 코드 생성 및 저장
        code = generate_verification_code()
        expires_at = datetime.now() + timedelta(minutes=10)  # 10분 유효
        
        email_verification_codes[email] = {
            "code": code,
            "expires_at": expires_at,
            "verified": False
        }
        logger.info(f"인증 코드 생성 완료: {email} (코드: {code})")
        
        # 이메일 전송
        email_sent = send_verification_email(email, code)
        if email_sent:
            logger.info(f"인증 코드 이메일 전송 성공: {email}")
            return {"success": True, "message": "인증 코드가 이메일로 전송되었습니다."}
        else:
            logger.error(f"이메일 전송 실패: {email}")
            # SMTP 설정이 없는 경우 더 명확한 에러 메시지
            if not SMTP_USER or not SMTP_PASSWORD:
                raise HTTPException(
                    status_code=500, 
                    detail="이메일 전송에 실패했습니다. SMTP 설정이 필요합니다. Railway 환경 변수에 SMTP 설정을 추가해주세요."
                )
            else:
                raise HTTPException(
                    status_code=500, 
                    detail="이메일 전송에 실패했습니다. SMTP 서버 연결을 확인하거나 다시 시도해주세요."
                )
    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except Exception as e:
        logger.error(f"인증 코드 전송 중 예상치 못한 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}")

@app.post("/verify-email-code")
def verify_email_code(request: VerifyEmailRequest):
    """이메일 인증 코드 검증"""
    try:
        # 입력 검증
        if not request.email or not request.email.strip():
            raise HTTPException(status_code=400, detail="이메일 주소를 입력해주세요.")
        if not request.code or not request.code.strip():
            raise HTTPException(status_code=400, detail="인증 코드를 입력해주세요.")
        
        email = request.email.strip().lower()
        code = request.code.strip()
        
        # 이메일 형식 검증
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            raise HTTPException(status_code=400, detail="올바른 이메일 형식이 아닙니다.")
        
        # 인증 코드 형식 검증 (6자리 숫자)
        if not code.isdigit() or len(code) != 6:
            raise HTTPException(status_code=400, detail="인증 코드는 6자리 숫자여야 합니다.")
        
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이메일 인증 코드 검증 중 예상치 못한 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"인증 코드 검증 중 오류가 발생했습니다: {str(e)}")

@app.post("/register")
def register(user: User):
    """회원가입 (이메일 인증 필수)"""
    try:
        # 입력 검증
        if not user.username or not user.username.strip():
            raise HTTPException(status_code=400, detail="사용자 ID를 입력해주세요.")
        if not user.password or len(user.password) < 8:
            raise HTTPException(status_code=400, detail="비밀번호는 8자 이상이어야 합니다.")
        if not user.email or not user.email.strip():
            raise HTTPException(status_code=400, detail="이메일 주소를 입력해주세요.")
        if not user.verification_code or not user.verification_code.strip():
            raise HTTPException(status_code=400, detail="인증 코드를 입력해주세요.")
        
        username = user.username.strip()
        password = user.password
        email = user.email.strip().lower()
        verification_code = user.verification_code.strip()
        
        # 이메일 형식 검증
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            raise HTTPException(status_code=400, detail="올바른 이메일 형식이 아닙니다.")
        
        # 사용자 ID 형식 검증 (영문, 숫자, 언더스코어만 허용, 3-50자)
        if not re.match(r'^[a-zA-Z0-9_]{3,50}$', username):
            raise HTTPException(status_code=400, detail="사용자 ID는 영문, 숫자, 언더스코어만 사용 가능하며 3-50자여야 합니다.")
        
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
        if verification_data["code"] != verification_code:
            raise HTTPException(status_code=400, detail="인증 코드가 일치하지 않습니다.")
        
        try:
            # 비밀번호를 bcrypt로 해시화
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            hashed_password_str = hashed_password.decode('utf-8')
            
            cursor.execute(
                "INSERT INTO vss_user (ID, PW, EMAIL) VALUES (?, ?, ?)",
                (username, hashed_password_str, email)
            )
            conn.commit()
            
            # 회원가입 성공 후 인증 코드 삭제
            del email_verification_codes[email]
            
            logger.info(f"회원가입 성공: {username} ({email})")
            return {"message": "회원가입 성공"}
        except mariadb.IntegrityError as e:
            error_msg = str(e)
            if "ID" in error_msg or "PRIMARY" in error_msg:
                raise HTTPException(status_code=400, detail="이미 존재하는 사용자 ID입니다.")
            elif "EMAIL" in error_msg:
                raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")
            else:
                raise HTTPException(status_code=400, detail="이미 존재하는 사용자입니다.")
        except mariadb.Error as e:
            logger.error(f"데이터베이스 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"회원가입 처리 중 예상치 못한 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"회원가입 처리 중 오류가 발생했습니다: {str(e)}")

class SendResetPasswordCodeRequest(BaseModel):
    username: str
    email: str

class VerifyResetPasswordCodeRequest(BaseModel):
    username: str
    email: str
    code: str

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
        # 입력 검증
        if not request.username or not request.username.strip():
            raise HTTPException(status_code=400, detail="사용자 ID를 입력해주세요.")
        if not request.email or not request.email.strip():
            raise HTTPException(status_code=400, detail="이메일 주소를 입력해주세요.")
        
        username = request.username.strip()
        email = request.email.strip().lower()
        
        # 이메일 형식 검증
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            raise HTTPException(status_code=400, detail="올바른 이메일 형식이 아닙니다.")
        
        # 사용자 ID와 이메일 일치 확인
        try:
            cursor.execute("SELECT ID, EMAIL FROM vss_user WHERE ID = ?", (username,))
            user = cursor.fetchone()
        except mariadb.Error as e:
            logger.error(f"사용자 확인 중 데이터베이스 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        db_email = user[1].strip().lower() if user[1] else ""
        if db_email != email:
            raise HTTPException(status_code=400, detail="등록된 이메일과 일치하지 않습니다.")
        
        # 만료된 코드 정리
        cleanup_expired_reset_codes()
        
        # 인증 코드 생성 및 저장
        code = generate_verification_code()
        expires_at = datetime.now() + timedelta(minutes=10)  # 10분 유효
        
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
    try:
        # 입력 검증
        if not request.username or not request.username.strip():
            raise HTTPException(status_code=400, detail="사용자 ID를 입력해주세요.")
        if not request.email or not request.email.strip():
            raise HTTPException(status_code=400, detail="이메일 주소를 입력해주세요.")
        if not request.code or not request.code.strip():
            raise HTTPException(status_code=400, detail="인증 코드를 입력해주세요.")
        
        username = request.username.strip()
        email = request.email.strip().lower()
        code = request.code.strip()
        
        # 이메일 형식 검증
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            raise HTTPException(status_code=400, detail="올바른 이메일 형식이 아닙니다.")
        
        # 인증 코드 형식 검증 (6자리 숫자)
        if not code.isdigit() or len(code) != 6:
            raise HTTPException(status_code=400, detail="인증 코드는 6자리 숫자여야 합니다.")
        
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"비밀번호 재설정 인증 코드 검증 중 예상치 못한 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"인증 코드 검증 중 오류가 발생했습니다: {str(e)}")

@app.post("/reset-password")
def reset_password(request: ResetPasswordRequest):
    """비밀번호 재설정"""
    try:
        # 입력 검증
        if not request.username or not request.username.strip():
            raise HTTPException(status_code=400, detail="사용자 ID를 입력해주세요.")
        if not request.email or not request.email.strip():
            raise HTTPException(status_code=400, detail="이메일 주소를 입력해주세요.")
        if not request.verification_code or not request.verification_code.strip():
            raise HTTPException(status_code=400, detail="인증 코드를 입력해주세요.")
        if not request.new_password:
            raise HTTPException(status_code=400, detail="새 비밀번호를 입력해주세요.")
        
        username = request.username.strip()
        email = request.email.strip().lower()
        code = request.verification_code.strip()
        new_password = request.new_password
        
        # 이메일 형식 검증
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            raise HTTPException(status_code=400, detail="올바른 이메일 형식이 아닙니다.")
        
        # 인증 코드 형식 검증 (6자리 숫자)
        if not code.isdigit() or len(code) != 6:
            raise HTTPException(status_code=400, detail="인증 코드는 6자리 숫자여야 합니다.")
        
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
            cursor.execute("SELECT PW FROM vss_user WHERE ID = ? AND EMAIL = ?", (username, email))
            user_row = cursor.fetchone()
        except mariadb.Error as e:
            logger.error(f"사용자 조회 중 데이터베이스 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
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
        except Exception as e:
            logger.warning(f"비밀번호 비교 중 오류: {e}")
        
        if password_match:
            raise HTTPException(status_code=400, detail="새 비밀번호는 기존 비밀번호와 동일할 수 없습니다.")
        
        # 비밀번호를 bcrypt로 해시화
        try:
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            hashed_password_str = hashed_password.decode('utf-8')
        except Exception as e:
            logger.error(f"비밀번호 해시화 실패: {e}")
            raise HTTPException(status_code=500, detail="비밀번호 처리 중 오류가 발생했습니다.")
        
        # 비밀번호 업데이트
        try:
            cursor.execute(
                "UPDATE vss_user SET PW = ? WHERE ID = ? AND EMAIL = ?",
                (hashed_password_str, username, email)
            )
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없거나 이메일이 일치하지 않습니다.")
            
            conn.commit()
        except mariadb.Error as e:
            logger.error(f"비밀번호 업데이트 중 데이터베이스 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
        # 비밀번호 재설정 성공 후 인증 코드 삭제
        del reset_password_codes[email]
        
        logger.info(f"비밀번호 재설정 성공: {username} ({email})")
        return {"success": True, "message": "비밀번호가 성공적으로 재설정되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"비밀번호 재설정 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"비밀번호 재설정 중 오류가 발생했습니다: {str(e)}")

# 동영상 메타데이터 추출 함수 (백그라운드 작업)
def extract_video_metadata(file_path: str, video_id: int, filename: str):
    """동영상 메타데이터를 추출하여 DB에 업데이트"""
    video = None
    try:
        # 파일 존재 확인
        if not os.path.exists(file_path):
            logger.warning(f"동영상 파일이 존재하지 않음: {file_path}")
            return
        
        # 동영상 파일 열기
        video = VideoFileClip(str(file_path))
        width = int(video.w) if video.w else None
        height = int(video.h) if video.h else None
        duration = float(video.duration) if video.duration else None
        video.close()
        video = None
        
        # 메타데이터 업데이트
        try:
            cursor.execute(
                """UPDATE vss_videos 
                   SET WIDTH = ?, HEIGHT = ?, DURATION = ? 
                   WHERE ID = ?""",
                (width, height, duration, video_id)
            )
            conn.commit()
            logger.info(f"동영상 메타데이터 업데이트 완료: {filename} (ID: {video_id})")
        except mariadb.Error as e:
            logger.error(f"메타데이터 DB 업데이트 실패: {e}")
        except Exception as e:
            logger.error(f"메타데이터 DB 업데이트 중 예상치 못한 오류: {e}")
    except FileNotFoundError as e:
        logger.warning(f"동영상 파일을 찾을 수 없음: {file_path}, 오류: {e}")
    except Exception as e:
        logger.warning(f"동영상 메타데이터 추출 실패: {e}", exc_info=True)
    finally:
        # 리소스 정리
        if video is not None:
            try:
                video.close()
            except:
                pass

# 동영상 업로드 및 조회 API
@app.post("/upload-video")
async def upload_video_to_db(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Form(...)
):
    """동영상 파일을 서버에 업로드하고 DB에 저장 (최적화됨)"""
    file_path = None
    try:
        # 입력 검증
        if not user_id or not user_id.strip():
            raise HTTPException(status_code=400, detail="사용자 ID를 입력해주세요.")
        
        user_id = user_id.strip()
        
        # 1. 파일 검증 (빠른 실패 - DB 쿼리 전에 검증)
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        file_ext = Path(file.filename).suffix.lower()
        allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv'}
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식입니다: {file_ext}")
        
        # 2. DB 쿼리 최적화: 사용자 검증과 중복 체크를 하나의 쿼리로 통합
        try:
            cursor.execute(
                """SELECT 
                       (SELECT COUNT(*) FROM vss_user WHERE ID = ?) as user_exists,
                       (SELECT COUNT(*) FROM vss_videos WHERE USER_ID = ? AND FILE_NAME = ?) as duplicate_exists""",
                (user_id, user_id, file.filename)
            )
            result = cursor.fetchone()
        except mariadb.Error as e:
            logger.error(f"사용자 및 중복 확인 중 데이터베이스 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
        if not result:
            raise HTTPException(status_code=500, detail="데이터베이스 조회 결과가 없습니다.")
        
        user_exists, duplicate_exists = result[0], result[1]
        
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
        
        # 4. 파일 저장 (최적화된 버퍼 크기 사용)
        # 버퍼 크기를 8MB로 설정하여 대용량 파일 처리 성능 향상
        BUFFER_SIZE = 8 * 1024 * 1024  # 8MB
        file_size = 0
        try:
            with open(file_path, "wb", buffering=BUFFER_SIZE) as buffer:
                shutil.copyfileobj(file.file, buffer, length=BUFFER_SIZE)
                file_size = buffer.tell()
        except OSError as e:
            logger.error(f"파일 저장 중 파일 시스템 오류: {e}")
            raise HTTPException(status_code=500, detail=f"파일 저장 중 오류가 발생했습니다: {str(e)}")
        except Exception as e:
            logger.error(f"파일 저장 중 예상치 못한 오류: {e}")
            raise HTTPException(status_code=500, detail=f"파일 저장 중 오류가 발생했습니다: {str(e)}")
        
        # 5. VIA 서버에 업로드하여 video_id 얻기
        global vss_client
        via_video_id = None
        
        # VIA 서버 초기화 시도
        try:
            if vss_client is None:
                vss_client = VSS(VIA_SERVER_URL)
                try:
                    vss_client.model = await vss_client.get_model()
                except HTTPException as e:
                    # VIA 서버 모델 조회 실패 (502 에러 등)
                    logger.warning(f"VIA 서버 모델 조회 실패: {e.detail}")
                    logger.warning("VIA 서버 없이 동영상 업로드를 진행합니다. VIDEO_ID는 None으로 저장됩니다.")
                    # vss_client는 초기화했지만 model은 None으로 유지
                    vss_client = None  # 다음 요청에서 다시 시도할 수 있도록
                except aiohttp.ClientError as e:
                    logger.warning(f"VIA 서버 연결 실패 (모델 조회): {e}")
                    logger.warning("VIA 서버 없이 동영상 업로드를 진행합니다. VIDEO_ID는 None으로 저장됩니다.")
                    vss_client = None
                except Exception as e:
                    logger.warning(f"VIA 서버 모델 조회 중 예상치 못한 오류: {e}")
                    logger.warning("VIA 서버 없이 동영상 업로드를 진행합니다. VIDEO_ID는 None으로 저장됩니다.")
                    vss_client = None
            
            # VIA 서버가 초기화되었고 model이 있는 경우에만 업로드 시도
            if vss_client is not None and hasattr(vss_client, 'model') and vss_client.model:
                try:
                    via_video_id = await vss_client.upload_video(str(file_path))
                    logger.info(f"VIA 서버 업로드 성공: video_id={via_video_id}")
                except aiohttp.ClientError as e:
                    logger.warning(f"VIA 서버 업로드 연결 실패: {e}")
                    # VIA 업로드 실패 시에도 DB에는 저장하되 VIDEO_ID는 None으로 저장
                    # 나중에 재시도할 수 있도록
                except Exception as e:
                    logger.warning(f"VIA 서버 업로드 실패: {e}")
                    # VIA 업로드 실패 시에도 DB에는 저장하되 VIDEO_ID는 None으로 저장
                    # 나중에 재시도할 수 있도록
            else:
                logger.warning("VIA 서버가 초기화되지 않아 업로드를 건너뜁니다. VIDEO_ID는 None으로 저장됩니다.")
        except HTTPException as e:
            # 예상치 못한 HTTPException 발생 시
            logger.warning(f"VIA 서버 초기화 중 HTTPException 발생: {e.detail}")
            logger.warning("VIA 서버 없이 동영상 업로드를 진행합니다. VIDEO_ID는 None으로 저장됩니다.")
            via_video_id = None
            # vss_client를 None으로 설정하여 다음 요청에서 다시 시도할 수 있도록
            vss_client = None
        except aiohttp.ClientError as e:
            logger.warning(f"VIA 서버 연결 실패: {e}")
            logger.warning("VIA 서버 없이 동영상 업로드를 진행합니다. VIDEO_ID는 None으로 저장됩니다.")
            via_video_id = None
            vss_client = None
        except Exception as e:
            logger.warning(f"VIA 서버 초기화 실패: {e}")
            logger.warning("VIA 서버 없이 동영상 업로드를 진행합니다. VIDEO_ID는 None으로 저장됩니다.")
            via_video_id = None
            vss_client = None
        
        # 6. DB 저장 (VIA 서버의 video_id 포함)
        try:
            cursor.execute(
                """INSERT INTO vss_videos 
                   (USER_ID, FILE_NAME, FILE_PATH, FILE_SIZE, FILE_URL, WIDTH, HEIGHT, DURATION, VIDEO_ID) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, file.filename, str(file_path), file_size, file_url, None, None, None, via_video_id)
            )
            # autocommit이 활성화되어 있으므로 명시적 커밋 불필요
            video_id = cursor.lastrowid
        except mariadb.Error as e:
            logger.error(f"동영상 DB 저장 중 데이터베이스 오류: {e}")
            # 파일이 저장되었지만 DB 저장 실패 시 파일 삭제
            if file_path and file_path.exists():
                try:
                    file_path.unlink()
                except:
                    pass
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
        # 7. 백그라운드 작업 설정 (메타데이터 추출)
        background_tasks.add_task(extract_video_metadata, str(file_path), video_id, file.filename)
        
        return {
            "success": True,
            "video_id": video_id,
            "file_url": f"http://localhost:8001{file_url}",
            "message": "동영상 업로드가 완료되었습니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"동영상 업로드 실패: {e}", exc_info=True)
        # 파일이 저장되었지만 DB 저장 실패 시 파일 삭제
        if file_path and file_path.exists():
            try:
                file_path.unlink()
            except Exception as cleanup_error:
                logger.warning(f"파일 정리 중 오류: {cleanup_error}")
        raise HTTPException(status_code=500, detail=f"동영상 업로드 중 오류가 발생했습니다: {str(e)}")

@app.get("/videos")
async def get_videos(user_id: str):
    """사용자의 동영상 목록 조회"""
    try:
        # 입력 검증
        if not user_id or not user_id.strip():
            raise HTTPException(status_code=400, detail="사용자 ID를 입력해주세요.")
        
        user_id = user_id.strip()
        
        # 사용자 존재 확인
        try:
            cursor.execute("SELECT ID FROM vss_user WHERE ID = ?", (user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        except mariadb.Error as e:
            logger.error(f"사용자 확인 중 데이터베이스 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
        # 동영상 목록 조회
        try:
            cursor.execute(
                """SELECT ID, FILE_NAME, FILE_URL, FILE_SIZE, WIDTH, HEIGHT, DURATION, CREATED_AT, VIDEO_ID 
                   FROM vss_videos 
                   WHERE USER_ID = ? 
                   ORDER BY CREATED_AT DESC""",
                (user_id,)
            )
            rows = cursor.fetchall()
        except mariadb.Error as e:
            logger.error(f"동영상 목록 조회 중 데이터베이스 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
        videos = []
        for row in rows:
            try:
                videos.append({
                    "id": row[0],
                    "title": row[1],
                    "file_url": f"http://localhost:8001{row[2]}",  # DB에 저장된 URL 그대로 사용
                    "fileSize": row[3],
                    "width": row[4],
                    "height": row[5],
                    "duration": row[6],
                    "date": row[7].strftime("%Y-%m-%d") if row[7] else None,
                    "video_id": row[8]  # VIA 서버의 video_id
                })
            except Exception as e:
                logger.warning(f"동영상 데이터 변환 중 오류 (ID: {row[0]}): {e}")
                continue
        
        return {"success": True, "videos": videos}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"동영상 목록 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"동영상 목록 조회 중 오류가 발생했습니다: {str(e)}")

@app.delete("/videos/{video_id}")
async def delete_video(video_id: int, user_id: str = Query(...)):
    """동영상 삭제"""
    try:
        # 입력 검증
        if not user_id or not user_id.strip():
            raise HTTPException(status_code=400, detail="사용자 ID를 입력해주세요.")
        if video_id <= 0:
            raise HTTPException(status_code=400, detail="동영상 ID는 양의 정수여야 합니다.")
        
        user_id = user_id.strip()
        logger.info(f"동영상 삭제 요청: video_id={video_id}, user_id={user_id}")
        
        # 동영상 소유권 확인 및 파일 경로, VIDEO_ID 조회
        try:
            cursor.execute(
                "SELECT FILE_PATH, FILE_URL, VIDEO_ID FROM vss_videos WHERE ID = ? AND USER_ID = ?",
                (video_id, user_id)
            )
            row = cursor.fetchone()
        except mariadb.Error as e:
            logger.error(f"동영상 조회 중 데이터베이스 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
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
            except mariadb.Error as e:
                logger.warning(f"요약 결과 삭제 중 데이터베이스 오류: {e}")
            except Exception as e:
                logger.warning(f"요약 결과 삭제 중 오류 발생: {e}")
        
        # vss_videos 테이블에서 동영상 삭제
        try:
            cursor.execute("DELETE FROM vss_videos WHERE ID = ? AND USER_ID = ?", (video_id, user_id))
            conn.commit()
            logger.info(f"DB에서 동영상 삭제 완료: video_id={video_id}")
        except mariadb.Error as e:
            logger.error(f"동영상 DB 삭제 중 데이터베이스 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
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
            except OSError as e:
                logger.warning(f"동영상 파일 삭제 중 파일 시스템 오류: {file_path}, 오류: {e}")
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
                # 동영상 파일명에서 확장자 제거하여 base_name 추출
                if file_path:
                    base_name = file_path.stem  # 확장자 제거
                elif file_url:
                    # FILE_URL에서 파일명 추출 후 확장자 제거
                    filename = file_url.replace("/video-files/", "").lstrip("/")
                    if filename:
                        base_name = Path(filename).stem
                    else:
                        base_name = None
                else:
                    base_name = None
                
                if base_name:
                    deleted_clips = 0
                    # clips 디렉토리의 모든 파일 확인
                    for clip_file in clips_dir.iterdir():
                        if clip_file.is_file() and clip_file.name.startswith(f"clip_{base_name}_"):
                            try:
                                clip_file.unlink()
                                deleted_clips += 1
                                logger.info(f"클립 파일 삭제 성공: {clip_file.name}")
                            except OSError as e:
                                logger.warning(f"클립 파일 삭제 중 파일 시스템 오류: {clip_file.name}, 오류: {e}")
                            except Exception as e:
                                logger.warning(f"클립 파일 삭제 실패: {clip_file.name}, 오류: {e}")
                    
                    if deleted_clips > 0:
                        logger.info(f"총 {deleted_clips}개의 클립 파일이 삭제되었습니다.")
                    else:
                        logger.info(f"삭제할 클립 파일이 없습니다. (base_name: {base_name})")
            except OSError as e:
                logger.warning(f"클립 디렉토리 접근 중 파일 시스템 오류: {e}")
            except Exception as e:
                logger.warning(f"클립 삭제 중 오류 발생: {e}")
        
        return {"success": True, "message": "동영상이 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"동영상 삭제 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"동영상 삭제 중 오류가 발생했습니다: {str(e)}")

class DeleteClipsRequest(BaseModel):
    clip_urls: List[str]

@app.post("/delete-clips")
async def delete_clips(request: DeleteClipsRequest):
    """클립 파일들을 삭제하는 엔드포인트"""
    try:
        # 입력 검증
        if not request.clip_urls or len(request.clip_urls) == 0:
            raise HTTPException(status_code=400, detail="삭제할 클립 URL 목록이 필요합니다.")
        
        clips_dir = Path("./clips")
        if not clips_dir.exists():
            return {"success": True, "message": "클립 디렉토리가 없습니다.", "deleted_count": 0}
        
        deleted_count = 0
        failed_count = 0
        
        for clip_url in request.clip_urls:
            try:
                if not clip_url or not clip_url.strip():
                    logger.warning(f"빈 클립 URL이 포함되어 있습니다.")
                    failed_count += 1
                    continue
                
                # URL에서 파일명 추출
                # 예: http://localhost:8001/clips/clip_filename.mp4 -> clip_filename.mp4
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
                    try:
                        clip_file_path.unlink()
                        deleted_count += 1
                        logger.info(f"클립 파일 삭제 성공: {filename}")
                    except OSError as e:
                        logger.error(f"클립 파일 삭제 중 파일 시스템 오류 ({filename}): {e}")
                        failed_count += 1
                else:
                    logger.warning(f"클립 파일을 찾을 수 없습니다: {filename}")
                    failed_count += 1
            except Exception as e:
                logger.error(f"클립 삭제 중 오류 발생 ({clip_url}): {e}", exc_info=True)
                failed_count += 1
        
        return {
            "success": True,
            "message": f"{deleted_count}개의 클립이 삭제되었습니다.",
            "deleted_count": deleted_count,
            "failed_count": failed_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"클립 삭제 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"클립 삭제 중 오류가 발생했습니다: {str(e)}")

class SaveSummaryRequest(BaseModel):
    video_id: str  # VIA 서버의 video_id (vss_videos.VIDEO_ID 컬럼 값)
    user_id: str
    summary_text: str
    via_video_id: Optional[str] = None  # 하위 호환성을 위해 유지

@app.post("/save-summary")
async def save_summary(request: SaveSummaryRequest):
    """요약 결과를 DB에 저장"""
    try:
        # 입력 검증
        if not request.video_id or not request.video_id.strip():
            raise HTTPException(status_code=400, detail="동영상 ID를 입력해주세요.")
        if not request.user_id or not request.user_id.strip():
            raise HTTPException(status_code=400, detail="사용자 ID를 입력해주세요.")
        if not request.summary_text or not request.summary_text.strip():
            raise HTTPException(status_code=400, detail="요약 텍스트를 입력해주세요.")
        
        video_id = request.video_id.strip()
        user_id = request.user_id.strip()
        summary_text = request.summary_text.strip()
        
        # 사용자 ID 검증
        try:
            cursor.execute("SELECT ID FROM vss_user WHERE ID = ?", (user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        except mariadb.Error as e:
            logger.error(f"사용자 확인 중 데이터베이스 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
        # 동영상 소유권 확인 (VIDEO_ID는 VIA 서버의 video_id이므로 vss_videos.VIDEO_ID로 조회)
        try:
            cursor.execute(
                "SELECT ID FROM vss_videos WHERE VIDEO_ID = ? AND USER_ID = ?",
                (video_id, user_id)
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="동영상을 찾을 수 없거나 권한이 없습니다.")
        except mariadb.Error as e:
            logger.error(f"동영상 확인 중 데이터베이스 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
        # 요약 결과 저장 또는 업데이트 (UNIQUE KEY로 중복 방지)
        # vss_summaries 테이블 구조:
        # - VIDEO_ID (VARCHAR): VIA 서버의 video_id (vss_videos.VIDEO_ID 컬럼 값)
        # - USER_ID (VARCHAR): 사용자 ID
        # - SUMMARY_TEXT (LONGTEXT): 요약 텍스트
        # - CREATED_AT (TIMESTAMP): 자동 설정
        # - UPDATED_AT (TIMESTAMP): 자동 설정
        try:
            cursor.execute(
                """INSERT INTO vss_summaries (VIDEO_ID, USER_ID, SUMMARY_TEXT) 
                   VALUES (?, ?, ?)
                   ON DUPLICATE KEY UPDATE 
                   SUMMARY_TEXT = VALUES(SUMMARY_TEXT),
                   UPDATED_AT = CURRENT_TIMESTAMP""",
                (video_id, user_id, summary_text)
            )
            conn.commit()
        except mariadb.Error as e:
            logger.error(f"요약 결과 저장 중 데이터베이스 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
        summary_id = cursor.lastrowid if cursor.rowcount == 1 else None
        if summary_id is None:
            # UPDATE인 경우 ID 조회
            try:
                cursor.execute(
                    "SELECT ID FROM vss_summaries WHERE VIDEO_ID = ? AND USER_ID = ?",
                    (video_id, user_id)
                )
                row = cursor.fetchone()
                summary_id = row[0] if row else None
            except mariadb.Error as e:
                logger.warning(f"요약 ID 조회 중 데이터베이스 오류: {e}")
        
        logger.info(f"요약 결과 저장 성공: 동영상 ID {video_id} (사용자: {user_id})")
        return {
            "success": True,
            "summary_id": summary_id,
            "message": "요약 결과가 저장되었습니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"요약 결과 저장 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"요약 결과 저장 중 오류가 발생했습니다: {str(e)}")

@app.get("/summaries/{video_id}")
async def get_summary(video_id: str, user_id: str = Query(...)):
    """특정 동영상의 요약 결과 조회"""
    try:
        # 입력 검증
        if not video_id or not video_id.strip():
            raise HTTPException(status_code=400, detail="동영상 ID를 입력해주세요.")
        if not user_id or not user_id.strip():
            raise HTTPException(status_code=400, detail="사용자 ID를 입력해주세요.")
        
        video_id = video_id.strip()
        user_id = user_id.strip()
        
        # 사용자 ID 검증
        try:
            cursor.execute("SELECT ID FROM vss_user WHERE ID = ?", (user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        except mariadb.Error as e:
            logger.error(f"사용자 확인 중 데이터베이스 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
        # 요약 결과 조회 (소유권 확인 포함)
        # VIDEO_ID는 VIA 서버의 video_id이므로 vss_videos.VIDEO_ID와 조인
        try:
            cursor.execute(
                """SELECT s.ID, s.SUMMARY_TEXT, s.CREATED_AT, s.UPDATED_AT
                   FROM vss_summaries s
                   INNER JOIN vss_videos v ON s.VIDEO_ID = v.VIDEO_ID
                   WHERE s.VIDEO_ID = ? AND s.USER_ID = ? AND v.USER_ID = ?""",
                (video_id, user_id, user_id)
            )
            row = cursor.fetchone()
        except mariadb.Error as e:
            logger.error(f"요약 결과 조회 중 데이터베이스 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
        if not row:
            return {
                "success": False,
                "message": "요약 결과를 찾을 수 없습니다."
            }
        
        try:
            return {
                "success": True,
                "summary": {
                    "id": row[0],
                    "summary_text": row[1],
                    "created_at": row[2].isoformat() if row[2] else None,
                    "updated_at": row[3].isoformat() if row[3] else None
                }
            }
        except Exception as e:
            logger.error(f"요약 결과 데이터 변환 중 오류: {e}")
            raise HTTPException(status_code=500, detail="요약 결과 데이터 변환 중 오류가 발생했습니다.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"요약 결과 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"요약 결과 조회 중 오류가 발생했습니다: {str(e)}")

@app.get("/summaries")
async def get_user_summaries(user_id: str = Query(...)):
    """사용자의 모든 요약 결과 조회"""
    try:
        # 입력 검증
        if not user_id or not user_id.strip():
            raise HTTPException(status_code=400, detail="사용자 ID를 입력해주세요.")
        
        user_id = user_id.strip()
        
        # 사용자 ID 검증
        try:
            cursor.execute("SELECT ID FROM vss_user WHERE ID = ?", (user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        except mariadb.Error as e:
            logger.error(f"사용자 확인 중 데이터베이스 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
        # 사용자의 모든 요약 결과 조회
        # VIDEO_ID는 VIA 서버의 video_id이므로 vss_videos.VIDEO_ID와 조인
        try:
            cursor.execute(
                """SELECT s.ID, s.VIDEO_ID, s.SUMMARY_TEXT, s.CREATED_AT, s.UPDATED_AT, v.FILE_NAME
                   FROM vss_summaries s
                   INNER JOIN vss_videos v ON s.VIDEO_ID = v.VIDEO_ID
                   WHERE s.USER_ID = ? AND v.USER_ID = ?
                   ORDER BY s.CREATED_AT DESC""",
                (user_id, user_id)
            )
            rows = cursor.fetchall()
        except mariadb.Error as e:
            logger.error(f"요약 결과 목록 조회 중 데이터베이스 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
        summaries = []
        for row in rows:
            try:
                summaries.append({
                    "id": row[0],
                    "video_id": row[1],
                    "summary_text": row[2],
                    "created_at": row[3].isoformat() if row[3] else None,
                    "updated_at": row[4].isoformat() if row[4] else None,
                    "video_name": row[5]
                })
            except Exception as e:
                logger.warning(f"요약 결과 데이터 변환 중 오류 (ID: {row[0]}): {e}")
                continue
        
        return {
            "success": True,
            "summaries": summaries,
            "count": len(summaries)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"요약 결과 목록 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"요약 결과 목록 조회 중 오류가 발생했습니다: {str(e)}")

class DeleteSummaryRequest(BaseModel):
    video_ids: List[int]  # vss_videos 테이블의 ID 목록 (내부 DB ID)
    user_id: str

@app.delete("/summaries")
async def delete_summaries(request: DeleteSummaryRequest):
    """선택된 동영상들의 요약 결과 삭제"""
    try:
        # 입력 검증
        if not request.user_id or not request.user_id.strip():
            raise HTTPException(status_code=400, detail="사용자 ID를 입력해주세요.")
        if not request.video_ids or len(request.video_ids) == 0:
            raise HTTPException(status_code=400, detail="동영상 ID 목록이 필요합니다.")
        
        user_id = request.user_id.strip()
        video_ids = request.video_ids
        
        # video_ids 유효성 검증
        if not all(isinstance(vid, int) and vid > 0 for vid in video_ids):
            raise HTTPException(status_code=400, detail="동영상 ID는 양의 정수여야 합니다.")
        
        # 사용자 ID 검증
        try:
            cursor.execute("SELECT ID FROM vss_user WHERE ID = ?", (user_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        except mariadb.Error as e:
            logger.error(f"사용자 확인 중 데이터베이스 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
        # 선택된 동영상들의 VIDEO_ID (VIA 서버의 video_id) 조회
        try:
            placeholders = ','.join(['?'] * len(video_ids))
            cursor.execute(
                f"SELECT VIDEO_ID FROM vss_videos WHERE ID IN ({placeholders}) AND USER_ID = ?",
                (*video_ids, user_id)
            )
            rows = cursor.fetchall()
        except mariadb.Error as e:
            logger.error(f"동영상 VIDEO_ID 조회 중 데이터베이스 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
        via_video_ids = [row[0] for row in rows if row[0]]  # None이 아닌 것만
        
        if not via_video_ids:
            return {
                "success": True,
                "message": "삭제할 요약 결과가 없습니다.",
                "deleted_count": 0
            }
        
        # 요약 결과 삭제
        try:
            via_placeholders = ','.join(['?'] * len(via_video_ids))
            cursor.execute(
                f"DELETE FROM vss_summaries WHERE VIDEO_ID IN ({via_placeholders}) AND USER_ID = ?",
                (*via_video_ids, user_id)
            )
            conn.commit()
            deleted_count = cursor.rowcount
        except mariadb.Error as e:
            logger.error(f"요약 결과 삭제 중 데이터베이스 오류: {e}")
            raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
        
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
        logger.error(f"요약 결과 삭제 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"요약 결과 삭제 중 오류가 발생했습니다: {str(e)}")

# ============================================================================
# 미들웨어 및 이벤트 핸들러
# ============================================================================
# ============================================================================
# 미들웨어 및 이벤트 핸들러
# ============================================================================
# CORS 설정 (Vue와 통신 가능하게)
# Vercel 배포 시: Vercel 도메인을 allow_origins에 추가 권장
# 환경 변수 VERCEL_URL이 있으면 자동으로 추가
vercel_domains = []
if os.getenv("VERCEL_URL"):
    vercel_domains.append(f"https://{os.getenv('VERCEL_URL')}")
if os.getenv("VERCEL_DEPLOYMENT_URL"):
    vercel_domains.append(f"https://{os.getenv('VERCEL_DEPLOYMENT_URL')}")

# 기본 허용 도메인 (로컬 개발 + Vercel)
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
] + vercel_domains

# CORS_ALLOWED_ORIGINS 환경 변수가 있으면 추가
if os.getenv("CORS_ALLOWED_ORIGINS"):
    allowed_origins.extend(os.getenv("CORS_ALLOWED_ORIGINS").split(","))

# 운영 환경에서는 특정 도메인만 허용, 개발 환경에서는 모든 도메인 허용
cors_origins = allowed_origins if os.getenv("ENVIRONMENT") != "production" else allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],  # 기본값은 모든 도메인 허용
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
            logger.info("✓ 데이터베이스 연결 성공 (startup)")
        except Exception as e:
            logger.warning(f"⚠️ 데이터베이스 연결 실패 (startup): {e}")
            logger.warning("⚠️ 첫 요청 시 연결을 다시 시도합니다.")
    
    logger.info("✓ 애플리케이션이 시작되었습니다. VIA 서버의 query_video를 사용합니다.")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 aiohttp 세션 종료"""
    global http_session
    if http_session and not http_session.closed:
        await http_session.close()
