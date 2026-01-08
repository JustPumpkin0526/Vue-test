"""헬퍼 유틸리티 함수"""
from typing import Optional
import aiohttp
import logging
from fastapi import HTTPException
from config.settings import (
    API_BASE_URL, VIA_SERVER_URL, VIA_MODEL_TIMEOUT,
    OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT, DEFAULT_NUM_FRAMES_PER_CHUNK,
    DEFAULT_SUMMARIZE_PROMPT, DEFAULT_QUERY_TIMESTAMP_SUFFIX,
    DEFAULT_VIA_TARGET_RESPONSE_TIME, DEFAULT_VIA_TARGET_USECASE_EVENT_DURATION,
    DEFAULT_FRAME_WIDTH, DEFAULT_FRAME_HEIGHT, DEFAULT_TOP_K, DEFAULT_TOP_P,
    DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, DEFAULT_SEED, DEFAULT_BATCH_SIZE,
    DEFAULT_RAG_BATCH_SIZE, DEFAULT_RAG_TOP_K, DEFAULT_SUMMARIZE_TOP_P,
    DEFAULT_SUMMARIZE_TEMPERATURE, DEFAULT_SUMMARIZE_MAX_TOKENS,
    DEFAULT_CHAT_TOP_P, DEFAULT_CHAT_TEMPERATURE, DEFAULT_CHAT_MAX_TOKENS,
    DEFAULT_NOTIFICATION_TOP_P, DEFAULT_NOTIFICATION_TEMPERATURE,
    DEFAULT_NOTIFICATION_MAX_TOKENS, DEFAULT_ENABLE_AUDIO,
    DEFAULT_CAPTION_SUMMARIZATION_PROMPT, DEFAULT_SUMMARY_AGGREGATION_PROMPT,
    DEFAULT_QUERY_TEMPERATURE, DEFAULT_QUERY_SEED, DEFAULT_QUERY_MAX_TOKENS,
    DEFAULT_QUERY_TOP_P, DEFAULT_QUERY_TOP_K
)

logger = logging.getLogger(__name__)

# 전역 변수
http_session: Optional[aiohttp.ClientSession] = None
vss_client = None

# VSS 클래스를 나중에 import (순환 참조 방지)
VSS = None

def _set_vss_class(vss_class):
    """VSS 클래스를 설정 (순환 참조 방지)"""
    global VSS
    VSS = vss_class

async def get_session():
    """전역 aiohttp 세션 가져오기 또는 생성"""
    global http_session
    if http_session is None or http_session.closed:
        http_session = aiohttp.ClientSession()
    return http_session

async def ensure_vss_client():
    """VSS 클라이언트 초기화 (중복 초기화 방지)"""
    global vss_client, VSS
    if VSS is None:
        from services.vss_client import VSS as VSSClass
        VSS = VSSClass
    
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

def build_file_url(file_url: str) -> str:
    """파일 URL 생성 (API 베이스 URL 포함)"""
    if file_url.startswith('http'):
        return file_url
    return f"{API_BASE_URL}{file_url}"

async def create_summarize_prompt(user_prompt: str) -> str:
    logger.info(f"user_prompt: {user_prompt}")
    logger.info(f"DEFAULT_SUMMARIZE_PROMPT: {DEFAULT_SUMMARIZE_PROMPT}")
    """
    Ollama를 사용하여 요약 프롬프트 생성
    
    Args:
        user_prompt: 사용자가 입력한 프롬프트
    
    Returns:
        생성된 요약 프롬프트 (Ollama 실패 시 기본 프롬프트 반환)
    """
    try:
        # Ollama API 호출을 위한 프롬프트 구성
        ollama_prompt = f"""사용자 질문: "{user_prompt}"

기본 프롬프트 형태 (참고용):
"{DEFAULT_SUMMARIZE_PROMPT}"

작업 요청:
위 기본 프롬프트의 구조, 스타일, 형식을 그대로 유지하면서, 사용자 질문의 주제와 내용을 반영한 새로운 비디오 요약 프롬프트를 작성해주세요.

중요 지침:
1. 기본 프롬프트의 전체 구조와 톤을 그대로 유지하세요.
2. "You are a video monitoring system"과 같은 역할 정의 부분을 포함하세요.
3. 타임스탬프 관련 지시사항(시작 시간과 종료 시간 포함)을 유지하세요.
4. 사용자 질문의 핵심 주제와 요구사항을 프롬프트에 자연스럽게 통합하세요.
5. 기본 프롬프트의 영어 문체와 형식을 그대로 따르세요.
6. 프롬프트 텍스트만 출력하세요. 설명이나 예시는 포함하지 마세요.
        """
        
        # Ollama API 호출 (aiohttp 사용)
        session = await get_session()
        ollama_url = f"{OLLAMA_BASE_URL}/api/chat"
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": """You are a prompt generator. Your task is to transform user questions into video summarization prompts.

CRITICAL RULES - YOU MUST FOLLOW:
1. Return ONLY the prompt text itself. No examples, no samples, no timestamps.
2. Do NOT include example outputs like "00:05:00, 00:06:00 A person is seen..." or any timestamp examples.
3. Do NOT add any preface, explanation, quotes, or additional text.
4. Do NOT say things like "Here is...", "Sure", "The prompt is...", or "Here's the prompt:".
5. Output the prompt directly without any formatting, examples, or explanations.
6. Start directly with the prompt text. Do not include any introductory phrases.
7. The output must be a complete, usable prompt that can be directly used for video summarization."""
                },
                {
                    "role": "user",
                    "content": ollama_prompt
                }
            ],
            "stream": False,
            "options": {
                "temperature": 0.4, 
                "num_predict": 1000
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


def build_summarize_params(
    video_id: str,
    chunk_duration: int,
    model: str,
    prompt: str = DEFAULT_SUMMARIZE_PROMPT,
    cs_prompt: str = DEFAULT_CAPTION_SUMMARIZATION_PROMPT,
    sa_prompt: str = DEFAULT_SUMMARY_AGGREGATION_PROMPT,
    num_frames_per_chunk: Optional[int] = DEFAULT_NUM_FRAMES_PER_CHUNK,
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

