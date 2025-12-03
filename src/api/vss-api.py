from fastapi import FastAPI, File, Form, UploadFile, Body, HTTPException, Request
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
from pathlib import Path

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
    logger.info(f"Sample video file found: {sample_file}")
else:
    logger.warning(f"Sample video file NOT found at: {sample_file}")
    logger.warning(f"Please ensure sample.mp4 exists in: {sample_dir}")

try:
    app.mount("/sample", StaticFiles(directory=str(sample_dir)), name="sample")
    logger.info(f"Successfully mounted /sample endpoint to {sample_dir}")
except Exception as e:
    logger.error(f"Failed to mount /sample endpoint: {e}")

# VIA 서버 주소
VIA_SERVER_URL = "http://172.16.7.64:8100"  # 환경에 맞게 수정

# Ollama 설정
# Ollama 서버 주소 (기본값: http://localhost:11434)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# 사용할 Ollama 모델 (예: llama3, mistral, qwen2.5 등)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# 질문-답변 방식: VIA 서버의 query_video만 사용
# 동영상 컨텍스트를 직접 활용하여 질문에 답변

# 전역 aiohttp 세션
http_session: Optional[aiohttp.ClientSession] = None

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
        with open(video_path, "rb") as f:
            file_content = f.read()
        data.add_field("file", file_content, filename=f"file_{self.f_count}")
        data.add_field("purpose", "vision")
        data.add_field("media_type", "video")
        
        async with session.post(self.files_endpoint, data=data) as response:
            self.f_count += 1
            json_data = await self.check_response(response)
            return json_data.get("id")  # return uploaded file id

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
            # check response
            json_data = await self.check_response(response)
            if isinstance(json_data, dict) and "choices" in json_data:
                message_content = json_data["choices"][0]["message"]["content"]
                return message_content
            else:
                # JSON이 아니거나 에러일 때는 원본 텍스트 또는 에러 메시지 반환
                return json_data

    async def query_video(self, video_id, model, chunk_size, temperature, seed, max_new_tokens, top_p, top_k, query):
        # VIA 서버는 max_tokens가 최대 1024까지만 허용
        if max_new_tokens > 1024:
            logger.warning(f"max_tokens {max_new_tokens}가 1024를 초과합니다. 1024로 제한합니다.")
            max_new_tokens = 1024
        
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

# 전역 VSS 클라이언트 (지연 초기화)
vss_client = None

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
    print(closest_value)
    return closest_value


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

@app.post("/generate-clips")
async def generate_clips(
    request: Request,
    files: List[UploadFile] = File(None),
    prompt: str = Form(...)
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
        for upfile in upload_list:
            file_path = os.path.basename(upfile.filename)
            tmp_path = f"./tmp/{file_path}"

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

            os.makedirs("./tmp", exist_ok=True)
            # 업로드용 임시 파일 실제 저장 (기존 누락으로 인해 FileNotFoundError / 빈 처리 발생 가능)
            with open(tmp_path, "wb") as buffer:
                shutil.copyfileobj(upfile.file, buffer)

            logger.info(f"Uploaded video saved to {tmp_path}")

            video_id = await vss_client.upload_video(tmp_path)

            video_clips = []
            # MoviePy에 파일 경로(문자열)로 전달
            video = VideoFileClip(tmp_path)
            duration = video.duration or 0
            logger.info(f"Video duration: {duration} seconds for {tmp_path}")
            
            # chunk_duration 계산: 동영상 길이의 1/10을 가장 가까운 값으로 반올림
            chunk_duration = await get_recommended_chunk_size(duration)

            num_frames_per_chunk = chunk_duration // 4

            # summarize_video 실행 전에 Ollama를 사용하여 prompt 값 변경
            try:
                logger.info(f"Ollama를 사용하여 prompt 개선: {OLLAMA_MODEL} (서버: {OLLAMA_BASE_URL})")
                
                # Ollama API 호출을 위한 프롬프트 구성
                ollama_prompt = f"""다음은 동영상 요약을 위한 프롬프트입니다.
                                원본 프롬프트: {prompt}
                                위 프롬프트를 영어로 수정하고, 타임스탬프 출력을 요청하도록 자연스럽게 개선해주세요.
                                또한 문장 구조를 이루게 하고 500자 이내로 작성해주세요. 개선된 prompt 이외에 내용은 출력하지 마세요."""
                
                # Ollama API 호출 (aiohttp 사용)
                session = await get_session()
                ollama_url = f"{OLLAMA_BASE_URL}/api/chat"
                payload = {
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert at improving video summarization prompts. Improve the given prompt to be more effective and natural in English, and include a request for timestamp output."
                        },
                        {
                            "role": "user",
                            "content": ollama_prompt
                        }
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 1000  # 최대 토큰 수
                    }
                }
                
                async with session.post(
                    ollama_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)  # Ollama는 로컬 실행이므로 시간 여유 있게
                ) as ollama_response:
                    if ollama_response.status == 200:
                        ollama_data = await ollama_response.json()
                        improved_prompt = ollama_data.get("message", {}).get("content", "")
                        if improved_prompt:
                            print(f"Ollama로 prompt 개선 성공: {len(improved_prompt)} 문자")
                            prompt = improved_prompt.strip()  # 개선된 prompt로 교체
                            print(f"개선된 prompt: {prompt}")
                        else:
                            print("Ollama 응답에 content가 없습니다. 원본 prompt를 사용합니다.")
                    else:
                        error_text = await ollama_response.text()
                        print(f"Ollama API 호출 실패 (HTTP {ollama_response.status}): {error_text}")
                        print("원본 prompt를 사용합니다.")
                        # 원본 prompt 사용
            except aiohttp.ClientConnectorError as e:
                print(f"Ollama 서버에 연결할 수 없습니다: {e}")
                print("Ollama가 실행 중인지 확인하세요: ollama serve")
                print("원본 prompt를 사용합니다.")
            except Exception as e:
                print(f"Ollama를 사용한 prompt 개선 중 오류 발생: {e}")
                print("원본 prompt를 사용합니다.")
                # 오류 발생 시 원본 prompt 사용

            result = await vss_client.summarize_video(
                video_id,
                prompt,
                "You will be given captions from sequential clips of a video. Aggregate captions in the format start_time:end_time:caption based on whether captions are related to one another or create a continuous scene.",
                "Based on the available information, generate a summary that captures the important events in the video. The summary should be organized chronologically and in logical sections. This should be a concise, yet descriptive summary of all the important events. The format should be intuitive and easy for a user to read and understand what happened. Format the output in Markdown so it can be displayed nicely. Timestamps are in seconds so please format them as SS.SSS",
                chunk_duration,
                model,
                num_frames_per_chunk,
                0,
                0,
                80,
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

            print(result)
            
            # prompt를 질문으로 처리: VIA 서버의 query_video 사용
            # 동영상 컨텍스트를 직접 활용하여 질문에 답변
            try:
                logger.info(f"VIA 서버의 query_video를 사용하여 질문 처리: {prompt}")
                
                # query_video 파라미터 설정
                query_chunk_size = chunk_duration  # 요약에 사용한 chunk_duration과 동일하게
                query_temperature = 0.7
                query_seed = 42
                query_max_tokens = 1024  # VIA 서버는 최대 1024까지만 허용
                query_top_p = 0.9
                query_top_k = 50
                
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
                result = query_result  # VIA 서버의 답변으로 result 업데이트
                logger.info(f"VIA 서버 질문-답변 성공: {len(result)} 문자")
                print(f"VIA 서버 답변: {result}")
            except Exception as via_error:
                logger.warning(f"VIA 서버 query_video 실패: {via_error}")
                logger.warning("원본 result를 사용합니다.")
            
            num_clips = random.randint(0, 3)
            logger.info(f"Number of clips to generate: {num_clips}")
            base_name, _ = os.path.splitext(file_path)
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
                "video": file_path,
                "clips": video_clips
            })

    except Exception as e:
        logger.error(f"Error processing uploaded video(s): {e}")
        raise HTTPException(status_code=500, detail=f"Error processing uploaded video(s): {e}")

    print("All clips generated successfully.")
    print(f"Returned clips payload: {json.dumps({'clips': grouped_clips}, ensure_ascii=False)}")
    return JSONResponse(content={"clips": grouped_clips})


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

    os.makedirs("./tmp", exist_ok=True)
    file_path = f"./tmp/{file.filename}"
    # 업로드용 임시 파일 실제 저장 (기존 누락으로 인해 FileNotFoundError / 빈 처리 발생 가능)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    video_id = await vss_client.upload_video(file_path)

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
    
    # 전역 vss_client 사용 선언 (누락 시 UnboundLocalError 발생)
    global vss_client
    
    if vss_client is None:
        vss_client = VSS(VIA_SERVER_URL)
        vss_client.model = await vss_client.get_model()
    
    session = await get_session()
    async with session.get(VIA_SERVER_URL + "/models", timeout=aiohttp.ClientTimeout(total=10)) as resp:
        if resp.status >= 400:
            raise HTTPException(status_code=502, detail=f"VIA /models returned status {resp.status}")
        resp_json = await resp.json()
        model = resp_json["data"][0]["id"]
    
    if file and not video_id:
        os.makedirs("./tmp", exist_ok=True)
        file_path = f"./tmp/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        video_id = await vss_client.upload_video(file_path)
    elif not video_id:
        raise HTTPException(status_code=400, detail="video_id 또는 file 중 하나는 필요합니다.")
        
    result = await vss_client.query_video(video_id, model, chunk_size, temperature, seed, max_new_tokens, top_p, top_k, query)

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

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 aiohttp 세션 생성"""
    await get_session()
    logger.info("✓ 애플리케이션이 시작되었습니다. VIA 서버의 query_video를 사용합니다.")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 aiohttp 세션 종료"""
    global http_session
    if http_session and not http_session.closed:
        await http_session.close()
