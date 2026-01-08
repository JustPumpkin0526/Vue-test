"""VSS API 메인 애플리케이션"""
import asyncio
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging

# 로깅 설정 먼저 초기화
from config.logging_config import setup_logging
setup_logging()

logger = logging.getLogger(__name__)

# ==================== asyncio 예외 핸들러 설정 ====================
def ignore_connection_reset(loop, context):
    """ConnectionResetError를 무시하는 asyncio 예외 핸들러"""
    exception = context.get('exception')
    if isinstance(exception, ConnectionResetError):
        # ConnectionResetError는 클라이언트가 연결을 끊었을 때 발생하는 정상적인 동작
        # 로그에 기록하지 않고 무시
        return
    
    # 다른 예외는 기본 핸들러로 전달
    loop.default_exception_handler(context)

# asyncio 이벤트 루프에 예외 핸들러 설정
if sys.platform == 'win32':
    # Windows에서만 설정 (ProactorBasePipeTransport는 Windows에서만 사용)
    try:
        loop = asyncio.get_event_loop()
        if loop is not None:
            loop.set_exception_handler(ignore_connection_reset)
    except RuntimeError:
        # 이벤트 루프가 아직 생성되지 않은 경우, 나중에 설정
        pass

# 설정 import
from config.settings import (
    VIDEOS_DIR, CLIPS_DIR, CONVERTED_VIDEOS_DIR, PROFILE_IMAGES_DIR, SAMPLE_DIR
)

# 데이터베이스 연결 초기화
from database.connection import db_pool, conn, cursor

# 유틸리티 import
from utils.helpers import get_session
# http_session을 전역으로 접근하기 위해
import utils.helpers as utils_helpers

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리 (startup 및 shutdown)"""
    # Startup
    # Windows에서 asyncio 예외 핸들러 설정 (이벤트 루프가 생성된 후)
    if sys.platform == 'win32':
        try:
            loop = asyncio.get_running_loop()
            loop.set_exception_handler(ignore_connection_reset)
        except RuntimeError:
            # 이벤트 루프가 없는 경우 무시
            pass
    
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
    
    yield  # 애플리케이션이 실행되는 동안 여기서 대기
    
    # Shutdown
    if utils_helpers.http_session and not utils_helpers.http_session.closed:
        await utils_helpers.http_session.close()
        logger.info("aiohttp 세션이 종료되었습니다.")

app = FastAPI(lifespan=lifespan)

# Serve generated clips as static files under /clips
CLIPS_DIR.mkdir(exist_ok=True)
app.mount("/clips", StaticFiles(directory=str(CLIPS_DIR.resolve())), name="clips")

# Serve uploaded videos as static files under /video-files (API 엔드포인트와 충돌 방지)
VIDEOS_DIR.mkdir(exist_ok=True)
app.mount("/video-files", StaticFiles(directory=str(VIDEOS_DIR.resolve())), name="video-files")

# Serve converted videos as static files under /converted-videos
CONVERTED_VIDEOS_DIR.mkdir(exist_ok=True)
app.mount("/converted-videos", StaticFiles(directory=str(CONVERTED_VIDEOS_DIR.resolve())), name="converted-videos")

# Serve profile images as static files under /profile-images
PROFILE_IMAGES_DIR.mkdir(exist_ok=True)
app.mount("/profile-images", StaticFiles(directory=str(PROFILE_IMAGES_DIR.resolve())), name="profile-images")

# Serve sample videos as static files under /sample
SAMPLE_DIR.mkdir(exist_ok=True, parents=True)
logger.info(f"Serving sample videos from: {SAMPLE_DIR}")

# sample.mp4 파일 존재 여부 확인
sample_file = SAMPLE_DIR / "sample.mp4"
if sample_file.exists():
    logger.info(f"샘플 동영상을 찾았습니다. : {sample_file}")
else:
    logger.warning(f"샘플 동영상은 해당 경로에 없습니다. : {sample_file}")

try:
    app.mount("/sample", StaticFiles(directory=str(SAMPLE_DIR.resolve())), name="sample")
    logger.info(f"/sample 엔드포인트를 {SAMPLE_DIR}에 성공적으로 마운트했습니다.")
except Exception as e:
    logger.error(f"/sample 엔드포인트를 마운트하는데 실패했습니다. : {e}")

# CORS 설정 (Vue와 통신 가능하게)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영에서는 도메인 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
from routers import auth, users, summarize, reports, search

app.include_router(auth.router, tags=["auth"])
app.include_router(users.router, tags=["users"])
app.include_router(summarize.router, tags=["summarize"])
app.include_router(reports.router, tags=["reports"])
app.include_router(search.router, tags=["search"])

# 기존 vss-api.py의 나머지 엔드포인트는 점진적으로 라우터로 마이그레이션
# 현재는 기존 파일을 직접 import하여 사용
try:
    # vss-api.py를 모듈로 import하여 엔드포인트 가져오기
    import sys
    import importlib.util
    
    # vss-api.py를 동적으로 import
    vss_api_path = Path(__file__).parent / "vss-api.py"
    spec = importlib.util.spec_from_file_location("vss_api", str(vss_api_path))
    vss_api = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vss_api)
    
    # vss-api.py의 전역 변수를 main.py의 것으로 교체
    # 이렇게 하면 generate_clips 등이 main.py의 데이터베이스 연결을 사용합니다
    if hasattr(vss_api, 'cursor'):
        vss_api.cursor = cursor
    if hasattr(vss_api, 'conn'):
        vss_api.conn = conn
    if hasattr(vss_api, 'db_pool'):
        vss_api.db_pool = db_pool
    
    # ensure_db_connection 함수도 main.py의 것을 사용하도록 교체
    from database.connection import ensure_db_connection as main_ensure_db_connection
    if hasattr(vss_api, 'ensure_db_connection'):
        vss_api.ensure_db_connection = main_ensure_db_connection
    
    # vss_client와 http_session도 utils.helpers의 것을 사용하도록 교체
    from utils.helpers import (
        ensure_vss_client as main_ensure_vss_client,
        get_session as main_get_session,
        get_via_model as main_get_via_model,
        create_summarize_prompt as main_create_summarize_prompt,
        build_query_prompt as main_build_query_prompt,
        get_recommended_chunk_size as main_get_recommended_chunk_size,
        build_summarize_params as main_build_summarize_params,
        build_query_video_params as main_build_query_video_params
    )
    import utils.helpers as utils_helpers_module
    from utils.video_utils import parse_timestamps as main_parse_timestamps
    
    if hasattr(vss_api, 'ensure_vss_client'):
        vss_api.ensure_vss_client = main_ensure_vss_client
    if hasattr(vss_api, 'get_session'):
        vss_api.get_session = main_get_session
    if hasattr(vss_api, 'get_via_model'):
        vss_api.get_via_model = main_get_via_model
    
    # vss_client 전역 변수도 utils.helpers의 것을 사용하도록 설정
    # generate_clips에서 global vss_client를 사용하므로 모듈 레벨 변수를 동기화
    # ensure_vss_client를 래핑하여 vss-api.vss_client도 업데이트되도록 함
    original_ensure_vss_client = main_ensure_vss_client
    async def synced_ensure_vss_client():
        """vss_client를 초기화하고 vss-api 모듈의 전역 변수도 동기화"""
        client = await original_ensure_vss_client()
        if hasattr(vss_api, 'vss_client'):
            vss_api.vss_client = client
        return client
    
    if hasattr(vss_api, 'ensure_vss_client'):
        vss_api.ensure_vss_client = synced_ensure_vss_client
    if hasattr(vss_api, 'create_summarize_prompt'):
        vss_api.create_summarize_prompt = main_create_summarize_prompt
    if hasattr(vss_api, 'build_query_prompt'):
        vss_api.build_query_prompt = main_build_query_prompt
    if hasattr(vss_api, 'get_recommended_chunk_size'):
        vss_api.get_recommended_chunk_size = main_get_recommended_chunk_size
    if hasattr(vss_api, 'build_summarize_params'):
        vss_api.build_summarize_params = main_build_summarize_params
    if hasattr(vss_api, 'build_query_video_params'):
        vss_api.build_query_video_params = main_build_query_video_params
    if hasattr(vss_api, 'parse_timestamps'):
        vss_api.parse_timestamps = main_parse_timestamps
    
    # _save_summary_to_db 함수도 services.video_service의 것을 사용
    from services.video_service import _save_summary_to_db as main_save_summary_to_db
    if hasattr(vss_api, '_save_summary_to_db'):
        vss_api._save_summary_to_db = main_save_summary_to_db
    
    # 필요한 상수들도 config.settings에서 가져와서 설정
    from config.settings import (
        DEFAULT_QUERY_TIMESTAMP_SUFFIX, CLIP_CLEANUP_AGE, API_BASE_URL,
        UNSUPPORTED_VIDEO_FORMATS
    )
    if hasattr(vss_api, 'DEFAULT_QUERY_TIMESTAMP_SUFFIX'):
        vss_api.DEFAULT_QUERY_TIMESTAMP_SUFFIX = DEFAULT_QUERY_TIMESTAMP_SUFFIX
    if hasattr(vss_api, 'CLIP_CLEANUP_AGE'):
        vss_api.CLIP_CLEANUP_AGE = CLIP_CLEANUP_AGE
    if hasattr(vss_api, 'API_BASE_URL'):
        vss_api.API_BASE_URL = API_BASE_URL
    if hasattr(vss_api, 'UNSUPPORTED_VIDEO_FORMATS'):
        vss_api.UNSUPPORTED_VIDEO_FORMATS = UNSUPPORTED_VIDEO_FORMATS
    
    # 디렉토리 경로도 main.py의 것으로 교체
    if hasattr(vss_api, 'videos_dir'):
        vss_api.videos_dir = VIDEOS_DIR
    if hasattr(vss_api, 'converted_videos_dir'):
        vss_api.converted_videos_dir = CONVERTED_VIDEOS_DIR
    if hasattr(vss_api, 'clips_dir'):
        vss_api.clips_dir = CLIPS_DIR
    
    # build_file_url 함수도 utils.helpers의 것을 사용
    from utils.helpers import build_file_url as main_build_file_url
    if hasattr(vss_api, 'build_file_url'):
        vss_api.build_file_url = main_build_file_url
    
    # 디렉토리 경로도 main.py의 것으로 교체 (중요: 파일 저장 위치 통일)
    if hasattr(vss_api, 'videos_dir'):
        vss_api.videos_dir = VIDEOS_DIR
        logger.info(f"videos_dir을 {VIDEOS_DIR}로 교체했습니다.")
    if hasattr(vss_api, 'converted_videos_dir'):
        vss_api.converted_videos_dir = CONVERTED_VIDEOS_DIR
    if hasattr(vss_api, 'clips_dir'):
        # clips_dir은 함수 내부에서 정의되므로 전역 변수로 교체할 수 없음
        # 대신 함수 내부에서 사용하는 경로를 확인해야 함
        pass
    
    # 기존 앱의 라우트를 새 앱에 복사 (auth와 users 제외)
    excluded_paths = {"/login", "/send-verification-code", "/verify-email-code", 
                      "/register", "/send-reset-password-code", "/verify-reset-password-code",
                      "/reset-password", "/debug/email-check"}
    
    loaded_routes = []
    for route in vss_api.app.routes:
        # auth와 users 라우터에 포함된 경로는 제외
        if hasattr(route, 'path'):
            route_path = route.path
            if any(route_path.startswith(excluded) for excluded in excluded_paths):
                continue
            # /user/ 경로도 제외
            if route_path.startswith("/user/"):
                continue
            loaded_routes.append(route_path)
        app.routes.append(route)
    
    logger.info(f"기존 vss-api.py의 엔드포인트를 로드했습니다. (총 {len(loaded_routes)}개 라우트)")
    if "/videos" in loaded_routes:
        logger.info("/videos 엔드포인트가 성공적으로 로드되었습니다.")
    else:
        logger.warning("/videos 엔드포인트가 로드되지 않았습니다!")
except Exception as e:
    logger.error(f"기존 vss-api.py 로드 실패: {e}")
    logger.warning("일부 엔드포인트가 작동하지 않을 수 있습니다.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

