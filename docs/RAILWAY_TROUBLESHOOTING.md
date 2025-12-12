# Railway 배포 문제 해결 가이드

## ⚠️ HTTPS/TLS 경고 메시지

Railway 로그에서 다음 메시지가 나타나는 경우:

```
automatic HTTPS is completely disabled for server
HTTP/2 skipped because it requires TLS
HTTP/3 skipped because it requires TLS
```

**이것은 경고일 뿐이며, Railway가 자동으로 HTTPS를 제공하므로 무시해도 됩니다.**

자세한 내용은 [Railway HTTPS/TLS 에러 해결 가이드](./RAILWAY_HTTPS_FIX.md)를 참고하세요.

## 502 Bad Gateway 에러 해결

Railway에서 `502 Bad Gateway` 에러가 발생하는 경우, 애플리케이션이 제대로 시작되지 않았거나 응답하지 않는 상태입니다.

### ⚠️ 가장 흔한 원인: 포트 설정 오류

Railway는 `$PORT` 환경 변수를 제공합니다. 하드코딩된 포트 번호를 사용하면 안 됩니다!

**❌ 잘못된 예:**
```dockerfile
CMD ["uvicorn", "vss-api:app", "--host", "0.0.0.0", "--port", "8001"]
```

**✅ 올바른 예:**
```dockerfile
CMD uvicorn vss-api:app --host 0.0.0.0 --port ${PORT:-8001}
```

또는 `railway.json`에서:
```json
{
  "deploy": {
    "startCommand": "cd src/api && uvicorn vss-api:app --host 0.0.0.0 --port $PORT"
  }
}
```

## 1. Railway 로그 확인

### Railway 대시보드에서 확인

1. Railway 프로젝트 → **Deployments** 탭
2. 최신 배포 클릭
3. **View Logs** 클릭
4. 에러 메시지 확인

### 일반적인 에러 원인

#### 1. 포트 설정 오류

**문제:**
- Railway는 `PORT` 환경 변수를 제공합니다
- 애플리케이션이 이 포트를 사용해야 합니다

**해결:**
Railway 환경 변수 확인:
- `PORT` 환경 변수가 자동으로 설정되어 있는지 확인
- 시작 명령어에서 `$PORT` 사용 확인

**시작 명령어 예시:**
```bash
# Root Directory가 src/api인 경우
uvicorn vss-api:app --host 0.0.0.0 --port $PORT

# Root Directory가 프로젝트 루트인 경우
cd src/api && uvicorn vss-api:app --host 0.0.0.0 --port $PORT
```

**⚠️ 중요:** `$PORT` 환경 변수를 반드시 사용해야 합니다. Railway가 자동으로 할당한 포트를 사용합니다.

#### 2. 작업 디렉토리 오류

**문제:**
- `vss-api.py` 파일을 찾을 수 없음

**해결:**
Railway 프로젝트 설정:
- **Root Directory**: `src/api` 설정
- 또는 시작 명령어에서 경로 지정:
  ```bash
  cd src/api && uvicorn vss-api:app --host 0.0.0.0 --port $PORT
  ```

#### 3. 의존성 설치 실패

**문제:**
- `requirements.txt` 파일이 없거나 잘못된 위치
- Python 패키지 설치 실패

**해결:**
- `requirements.txt` 파일이 프로젝트 루트 또는 `src/api/`에 있는지 확인
- Railway가 자동으로 감지하는지 확인
- 수동으로 Build Command 설정:
  ```bash
  pip install -r requirements.txt
  ```

#### 4. 환경 변수 누락

**문제:**
- 필수 환경 변수가 설정되지 않음
- 데이터베이스 연결 실패

**해결:**
Railway → Variables 탭에서 다음 환경 변수 확인:
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `VIA_SERVER_URL`
- 기타 필수 환경 변수

#### 5. FFmpeg 누락 (MoviePy 의존성)

**문제:**
- MoviePy가 FFmpeg를 찾을 수 없음

**해결:**
Railway는 기본적으로 FFmpeg가 설치되어 있지 않을 수 있습니다.

**옵션 1: Nixpacks 사용 (권장)**
프로젝트 루트에 `nixpacks.toml` 생성:
```toml
[phases.setup]
nixPkgs = ["python311", "ffmpeg"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "cd src/api && uvicorn vss-api:app --host 0.0.0.0 --port $PORT"
```

**옵션 2: Dockerfile 사용**
`Dockerfile`을 사용하여 Railway에 배포 (이미 생성됨)

## 2. Railway 설정 확인

### 필수 설정

1. **Root Directory**
   - `src/api` 또는 프로젝트 루트
   - `vss-api.py` 파일 위치에 맞게 설정

2. **Start Command**
   ```bash
   # Root Directory가 src/api인 경우
   uvicorn vss-api:app --host 0.0.0.0 --port $PORT
   
   # Root Directory가 프로젝트 루트인 경우
   cd src/api && uvicorn vss-api:app --host 0.0.0.0 --port $PORT
   ```
   
   **⚠️ 중요:** `$PORT`를 사용해야 합니다. 하드코딩된 포트 번호는 작동하지 않습니다!

3. **Build Command** (선택사항)
   ```bash
   pip install -r requirements.txt
   ```

### 환경 변수 확인

Railway → Variables 탭에서 다음 변수들이 설정되어 있는지 확인:

```
# 데이터베이스
DB_HOST=your-db-host
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=vss

# VIA 서버
VIA_SERVER_URL=http://your-via-server:8101

# Ollama (선택사항)
OLLAMA_BASE_URL=http://your-ollama:11434
OLLAMA_MODEL=llama3

# SMTP (선택사항)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

## 3. 로컬 테스트

Railway에 배포하기 전에 로컬에서 테스트:

```bash
# src/api 디렉토리로 이동
cd src/api

# 환경 변수 설정 (로컬)
export PORT=8001
export DB_HOST=your-db-host
# ... 기타 환경 변수

# 애플리케이션 실행
uvicorn vss-api:app --host 0.0.0.0 --port $PORT
```

## 4. Railway 배포 설정 예시

### 방법 1: Nixpacks (자동 감지)

프로젝트 루트에 `nixpacks.toml` 생성 (이미 생성됨):

```toml
[phases.setup]
nixPkgs = ["python311", "ffmpeg"]

[phases.install]
cmds = [
  "pip install --upgrade pip",
  "pip install -r requirements.txt"
]

[start]
cmd = "cd src/api && uvicorn vss-api:app --host 0.0.0.0 --port $PORT"
```

**⚠️ 중요:** `$PORT` 환경 변수를 사용해야 합니다!

### 방법 2: Railway 설정에서 직접 지정

Railway 대시보드 → Settings → Deploy:

- **Root Directory**: `src/api` (또는 프로젝트 루트)
- **Start Command**: 
  - Root Directory가 `src/api`인 경우: `uvicorn vss-api:app --host 0.0.0.0 --port $PORT`
  - Root Directory가 루트인 경우: `cd src/api && uvicorn vss-api:app --host 0.0.0.0 --port $PORT`
- **Build Command**: (비워두거나 `pip install -r requirements.txt`)

**⚠️ 중요:** `$PORT` 환경 변수를 사용해야 합니다!

### 방법 3: Dockerfile 사용 (권장)

이미 `Dockerfile`이 있으므로 Railway에서 Dockerfile을 사용하도록 설정:

Railway → Settings → Deploy:
- **Builder**: `Dockerfile`
- **Dockerfile Path**: `Dockerfile` (프로젝트 루트)
- **Docker Build Context**: `.` (프로젝트 루트)

**Dockerfile이 `$PORT` 환경 변수를 사용하도록 수정되었습니다:**
```dockerfile
ENV PORT=8001
CMD uvicorn vss-api:app --host 0.0.0.0 --port ${PORT:-8001}
```

또는 `railway.json` 파일을 사용하여 시작 명령어를 오버라이드할 수 있습니다.

## 5. 일반적인 해결 방법

### 단계별 체크리스트

1. ✅ Railway 로그 확인
2. ✅ `requirements.txt` 파일 존재 확인
3. ✅ `vss-api.py` 파일 경로 확인
4. ✅ 시작 명령어 확인 (`$PORT` 사용)
5. ✅ 환경 변수 모두 설정 확인
6. ✅ 데이터베이스 연결 가능한지 확인
7. ✅ 포트 설정 확인 (Railway의 `$PORT` 사용)

### 빠른 해결 방법

1. **Railway 프로젝트 삭제 후 재생성**
   - 새로운 프로젝트 생성
   - GitHub 저장소 연결
   - 설정 다시 확인

2. **로컬에서 Docker 테스트**
   ```bash
   docker build -t vss-api .
   docker run -p 8001:8001 -e PORT=8001 vss-api
   ```

3. **Railway 지원팀 문의**
   - Railway 대시보드 → Support
   - 로그와 함께 문의

## 6. 디버깅 팁

### Railway 로그에서 확인할 사항

1. **빌드 단계**
   - 의존성 설치 성공 여부
   - FFmpeg 설치 여부

2. **시작 단계**
   - 애플리케이션 시작 메시지
   - 포트 바인딩 메시지
   - 에러 스택 트레이스

3. **런타임 에러**
   - 데이터베이스 연결 에러
   - 환경 변수 누락 에러
   - 모듈 import 에러

### 로그 예시

**정상 시작:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**에러 예시:**
```
ModuleNotFoundError: No module named 'fastapi'
Connection refused: database connection failed
Port already in use
```

## 7. Railway 설정 파일

### railway.json (이미 생성됨)

프로젝트 루트에 `railway.json` 파일이 생성되었습니다:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn vss-api:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**⚠️ 중요:** `startCommand`에서 `$PORT` 환경 변수를 사용합니다. Railway가 자동으로 할당한 포트를 사용합니다.

## 참고 자료

- [Railway 공식 문서](https://docs.railway.app/)
- [Railway Python 가이드](https://docs.railway.app/guides/python)
- [Railway 문제 해결](https://docs.railway.app/troubleshooting)

