"""로깅 설정"""
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime
from .settings import LOGS_DIR

def setup_logging():
    """로깅 설정 초기화"""
    # 로그 디렉토리 생성
    LOGS_DIR.mkdir(exist_ok=True)
    
    # 오늘 날짜를 파일명에 포함
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = LOGS_DIR / f"vss-api-{today}.log"
    uvicorn_log_file = LOGS_DIR / f"uvicorn-{today}.log"
    uvicorn_access_log_file = LOGS_DIR / f"uvicorn-access-{today}.log"
    
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

