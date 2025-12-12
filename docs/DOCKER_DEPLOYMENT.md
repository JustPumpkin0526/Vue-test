# Docker를 사용한 API 서버 배포 가이드

이 가이드는 Docker를 사용하여 VSS API 서버를 배포하는 방법을 설명합니다.

## 목차

1. [사전 요구사항](#사전-요구사항)
2. [Dockerfile 수정](#dockerfile-수정)
3. [환경 변수 설정](#환경-변수-설정)
4. [Docker 이미지 빌드](#docker-이미지-빌드)
5. [Docker 컨테이너 실행](#docker-컨테이너-실행)
6. [Docker Compose 사용](#docker-compose-사용)
7. [배포 옵션](#배포-옵션)

## 사전 요구사항

- Docker 설치 (버전 20.10 이상 권장)
  - 설치 방법: [Docker 설치 가이드](./DOCKER_INSTALLATION.md) 참고
- Docker Compose 설치 (선택사항, 컨테이너 오케스트레이션용)
- 프로젝트 소스 코드
- 환경 변수 파일 (.env)

## Dockerfile 수정

현재 Dockerfile은 프로젝트 루트에 있지만, API 파일은 `src/api/` 디렉토리에 있습니다. 
다음과 같이 Dockerfile을 수정해야 합니다:

```dockerfile
FROM python:3.11-slim-buster

ARG UID=1000
ARG GID=1000

RUN groupadd -g "${GID}" appgroup && \
    useradd --create-home --no-log-init -u "${UID}" -g "${GID}" appuser

WORKDIR /app

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
COPY .env .env 2>/dev/null || true

USER appuser:appgroup
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 작업 디렉토리를 src/api로 변경
WORKDIR /app/src/api

EXPOSE 8001

# vss-api.py 모듈 실행
CMD ["uvicorn", "vss-api:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 주요 변경사항

1. **FFmpeg 설치**: MoviePy가 동영상 처리를 위해 필요
2. **작업 디렉토리 변경**: `src/api/`로 변경하여 모듈 경로 문제 해결
3. **환경 변수 파일 복사**: `.env` 파일을 컨테이너에 복사 (선택사항)

## 환경 변수 설정

`.env` 파일을 프로젝트 루트에 생성하거나, Docker 실행 시 환경 변수를 전달합니다.

### .env 파일 예시

```env
# 데이터베이스 설정
DB_HOST=172.16.15.69
DB_PORT=3306
DB_USER=root
DB_PASSWORD=pass0001!
DB_NAME=vss

# VIA 서버 설정
VIA_SERVER_URL=http://172.16.7.64:8101

# Ollama 설정
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# SMTP 설정 (이메일 인증용)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

## Docker 이미지 빌드

프로젝트 루트 디렉토리에서 다음 명령어를 실행합니다:

```bash
# 기본 빌드
docker build -t vss-api:latest .

# 빌드 인자 지정 (사용자 ID/그룹 ID)
docker build --build-arg UID=1000 --build-arg GID=1000 -t vss-api:latest .

# 태그 지정
docker build -t vss-api:v1.0.0 .
```

## Docker 컨테이너 실행

### 기본 실행

```bash
docker run -d \
  --name vss-api \
  -p 8001:8001 \
  --env-file .env \
  vss-api:latest
```

### 볼륨 마운트 (파일 저장용)

동영상, 클립, 임시 파일을 호스트에 저장하려면 볼륨을 마운트합니다:

```bash
docker run -d \
  --name vss-api \
  -p 8001:8001 \
  --env-file .env \
  -v $(pwd)/src/api/videos:/app/src/api/videos \
  -v $(pwd)/src/api/clips:/app/src/api/clips \
  -v $(pwd)/src/api/tmp:/app/src/api/tmp \
  vss-api:latest
```

### 환경 변수 직접 전달

`.env` 파일 대신 환경 변수를 직접 전달:

```bash
docker run -d \
  --name vss-api \
  -p 8001:8001 \
  -e DB_HOST=172.16.15.69 \
  -e DB_PORT=3306 \
  -e DB_USER=root \
  -e DB_PASSWORD=pass0001! \
  -e DB_NAME=vss \
  -e VIA_SERVER_URL=http://172.16.7.64:8101 \
  vss-api:latest
```

### 컨테이너 관리

```bash
# 컨테이너 시작
docker start vss-api

# 컨테이너 중지
docker stop vss-api

# 컨테이너 재시작
docker restart vss-api

# 컨테이너 로그 확인
docker logs vss-api

# 실시간 로그 확인
docker logs -f vss-api

# 컨테이너 삭제
docker rm vss-api

# 실행 중인 컨테이너 확인
docker ps

# 모든 컨테이너 확인 (중지된 것 포함)
docker ps -a
```

## Docker Compose 사용

여러 서비스를 함께 관리하거나 설정을 간소화하려면 Docker Compose를 사용합니다.

### docker-compose.yml 예시

```yaml
version: '3.8'

services:
  vss-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: vss-api
    ports:
      - "8001:8001"
    env_file:
      - .env
    volumes:
      - ./src/api/videos:/app/src/api/videos
      - ./src/api/clips:/app/src/api/clips
      - ./src/api/tmp:/app/src/api/tmp
    restart: unless-stopped
    environment:
      - PYTHONUNBUFFERED=1
    networks:
      - vss-network

networks:
  vss-network:
    driver: bridge
```

### Docker Compose 명령어

```bash
# 서비스 시작
docker-compose up -d

# 서비스 중지
docker-compose down

# 서비스 재시작
docker-compose restart

# 로그 확인
docker-compose logs -f

# 이미지 재빌드 후 시작
docker-compose up -d --build
```

## 배포 옵션

### 1. 단일 서버 배포

위의 Docker 실행 방법을 사용하여 단일 서버에 배포합니다.

### 2. 클라우드 플랫폼 배포

#### AWS (Amazon ECS / EKS)
- ECR(Elastic Container Registry)에 이미지 푸시
- ECS Task Definition 또는 EKS Deployment 생성

#### Google Cloud Platform (Cloud Run / GKE)
- Container Registry 또는 Artifact Registry에 이미지 푸시
- Cloud Run 서비스 생성 또는 GKE 클러스터에 배포

#### Azure (Container Instances / AKS)
- Azure Container Registry에 이미지 푸시
- Container Instances 또는 AKS에 배포

### 3. Docker Swarm / Kubernetes

대규모 배포를 위해 오케스트레이션 도구 사용:

- **Docker Swarm**: 간단한 클러스터링
- **Kubernetes**: 복잡한 배포 시나리오에 적합

## 문제 해결

### 포트 충돌

다른 포트를 사용하려면:

```bash
docker run -d --name vss-api -p 8002:8001 vss-api:latest
```

### 권한 문제

파일 생성 권한 문제가 발생하면:

```bash
# 호스트에서 디렉토리 권한 설정
sudo chown -R 1000:1000 src/api/videos src/api/clips src/api/tmp
```

### 로그 확인

문제 발생 시 로그를 확인:

```bash
docker logs vss-api
docker logs vss-api 2>&1 | grep ERROR
```

### 컨테이너 내부 접속

```bash
docker exec -it vss-api /bin/bash
```

## 보안 고려사항

1. **환경 변수 보호**: `.env` 파일을 Git에 커밋하지 마세요
2. **네트워크 격리**: 필요한 포트만 노출
3. **이미지 스캔**: 보안 취약점 스캔 도구 사용
4. **최소 권한 원칙**: 컨테이너는 최소한의 권한으로 실행

## 성능 최적화

1. **멀티 스테이지 빌드**: 이미지 크기 최소화
2. **캐시 활용**: Docker 빌드 캐시 최적화
3. **리소스 제한**: CPU/메모리 제한 설정

```bash
docker run -d \
  --name vss-api \
  --memory="2g" \
  --cpus="2" \
  -p 8001:8001 \
  --env-file .env \
  vss-api:latest
```

## 참고 자료

- [Docker 공식 문서](https://docs.docker.com/)
- [Docker Compose 문서](https://docs.docker.com/compose/)
- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/)

