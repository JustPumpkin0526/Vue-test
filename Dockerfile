FROM python:3.11-slim-buster

ARG UID=1000
ARG GID=1000

RUN groupadd -g "${GID}" appgroup && \
    useradd --create-home --no-log-init -u "${UID}" -g "${GID}" appuser

WORKDIR /app

# 시스템 패키지 설치 (FFmpeg 등 MoviePy 의존성)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY src/api/ ./src/api/

# .env 파일 복사 (선택사항, 없어도 됨)
COPY .env .env 2>/dev/null || true

USER appuser:appgroup
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 작업 디렉토리를 src/api로 변경
WORKDIR /app/src/api

# Railway는 PORT 환경 변수를 제공하므로 이를 사용
# EXPOSE는 동적 포트를 지원하지 않으므로 범위로 지정
EXPOSE 8001

# vss-api.py 모듈 실행
# Railway의 PORT 환경 변수를 사용하되, 없으면 8001 사용
# shell 형식 사용 (환경 변수 확장을 위해)
CMD uvicorn vss-api:app --host 0.0.0.0 --port ${PORT:-8001}