"""애플리케이션 설정"""
import os
from pathlib import Path
from typing import Optional

# .env 파일 지원 (python-dotenv가 설치되어 있는 경우)
try:
    from dotenv import load_dotenv
    # 현재 스크립트 위치 기준으로 .env 파일 찾기
    env_path = Path(__file__).parent.parent.parent.parent / ".env"  # config/ -> api/ -> src/ -> 프로젝트 루트
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # 프로젝트 루트에 없으면 현재 디렉토리에서 찾기
        load_dotenv()
except ImportError:
    pass  # python-dotenv가 없으면 시스템 환경 변수 사용

# ==================== API 설정 ====================
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")

# ==================== VIA 서버 설정 ====================
VIA_SERVER_URL = "http://172.16.7.64:8101"
VIA_MODEL_TIMEOUT = 10  # VIA 모델 조회 타임아웃 (초)
VIA_UPLOAD_TIMEOUT_MIN = 60  # 최소 업로드 타임아웃 (초)
VIA_UPLOAD_TIMEOUT_MAX = 600  # 최대 업로드 타임아웃 (초)
VIA_UPLOAD_TIMEOUT_PER_MB = 10  # 1MB당 타임아웃 (초)

# ==================== Ollama 설정 ====================
# 같은 서버에서 실행 중이면 localhost 사용, 다른 서버면 해당 IP 주소 사용
# 기본 포트는 11434입니다 (Ollama 기본 포트)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_TIMEOUT = 60  # Ollama API 타임아웃 (초)

# ==================== 파일 설정 ====================
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv'}
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
FILE_BUFFER_SIZE = 16 * 1024 * 1024  # 16MB (업로드 성능 최적화)
CLIP_CLEANUP_AGE = 86400  # 클립 파일 정리 기준 시간 (24시간, 초)
UNSUPPORTED_VIDEO_FORMATS = {'.avi', '.mkv', '.flv', '.wmv'}  # 변환이 필요한 비디오 형식

# ==================== 타임아웃 설정 ====================
DEFAULT_VIA_TARGET_RESPONSE_TIME = 2 * 60  # 초
DEFAULT_VIA_TARGET_USECASE_EVENT_DURATION = 10  # 초

# ==================== 정규식 패턴 ====================
EMAIL_REGEX = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
IP_PATTERN = r'^(\d{1,3}\.){3}\d{1,3}$'

# ==================== 이메일 설정 ====================
EMAIL_CODE_EXPIRY_MINUTES = 10

# ==================== VIA 서버 요약 기본 설정 ====================
DEFAULT_SUMMARIZE_PROMPT = "You are a video monitoring system. Describe the events in this video and look for any anomalies. Start each sentence with the start and end timestamp of the event."
DEFAULT_CAPTION_SUMMARIZATION_PROMPT = "You will be given captions from sequential clips of a video. Aggregate captions in the format start_time:end_time:caption based on whether captions are related to one another or create a continuous scene."
DEFAULT_SUMMARY_AGGREGATION_PROMPT = "Based on the available information, generate a summary that captures the important events in the video. The summary should be organized chronologically and in logical sections. This should be a concise, yet descriptive summary of all the important events. The format should be intuitive and easy for a user to read and understand what happened. Format the output in Markdown so it can be displayed nicely. Timestamps are in seconds so please format them as SS.SSS"

# ==================== VIA 서버 요약 파라미터 기본값 ====================
DEFAULT_NUM_FRAMES_PER_CHUNK = 90
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

# ==================== VIA 서버 질의(query) 기본 설정 ====================
DEFAULT_QUERY_TEMPERATURE = 0.3
DEFAULT_QUERY_SEED = 42
DEFAULT_QUERY_MAX_TOKENS = 1024  # VIA 서버는 최대 1024까지만 허용
DEFAULT_QUERY_TOP_P = 1.0
DEFAULT_QUERY_TOP_K = 80
DEFAULT_QUERY_TIMESTAMP_SUFFIX = " 장면의 시작 타임스탬프와 종료 타임스탬프를 추출하여 반드시 '시작시간-끝시간' 형태로만 출력해주세요. 타임스탬프 형식은 초 단위(예: 10.5-120.3) 또는 분:초 형식(예: 1:30-2:45)일 수 있습니다. 타임스탬프만 출력하고 다른 설명은 포함하지 마세요."

# ==================== 데이터베이스 설정 ====================
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")  # 환경 변수에서 로드 (필수)
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "vss")

# ==================== SMTP 설정 ====================
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)

# ==================== 디렉토리 경로 ====================
BASE_DIR = Path(__file__).parent.parent
VIDEOS_DIR = BASE_DIR / "videos"
CLIPS_DIR = BASE_DIR / "clips"
CONVERTED_VIDEOS_DIR = BASE_DIR / "converted-videos"
PROFILE_IMAGES_DIR = BASE_DIR / "profile-images"
TMP_DIR = BASE_DIR / "tmp"
LOGS_DIR = BASE_DIR / "logs"
SAMPLE_DIR = BASE_DIR.parent / "assets" / "sample"

