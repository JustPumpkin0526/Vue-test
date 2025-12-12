FROM python:3.11-slim

ARG UID=1000
ARG GID=1000

RUN groupadd -g "${GID}" appgroup && \
    useradd --create-home --no-log-init -u "${UID}" -g "${GID}" appuser

WORKDIR /app

# 시스템 패키지 설치 (FFmpeg, MariaDB Connector/C 등)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY src/api/ ./src/api/

# 샘플 비디오 파일 복사 (선택사항)
COPY src/assets/ ./src/assets/

# .env 파일은 Railway 환경 변수로 관리되므로 복사하지 않음
# Railway에서 환경 변수를 직접 설정하면 됩니다

# 애플리케이션이 사용할 디렉토리 생성 및 권한 설정
# USER 전환 전에 root 권한으로 디렉토리 생성
RUN mkdir -p /app/src/api/clips /app/src/api/videos /app/src/api/tmp && \
    chown -R appuser:appgroup /app/src/api/clips /app/src/api/videos /app/src/api/tmp && \
    chown -R appuser:appgroup /app/src/assets 2>/dev/null || true

USER appuser:appgroup
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 작업 디렉토리를 src/api로 변경
WORKDIR /app/src/api

# Railway는 PORT 환경 변수를 제공하므로 이를 사용
# EXPOSE는 동적 포트를 지원하지 않으므로 범위로 지정
EXPOSE 8001

# vss-api.py 모듈 실행
# Railway의 PORT 환경 변수를 사용 (Railway가 자동으로 설정)
# Railway는 $PORT 환경 변수를 반드시 제공하므로 기본값 불필요
CMD ["uvicorn vss-api:app --host 0.0.0.0 --port $PORT"]