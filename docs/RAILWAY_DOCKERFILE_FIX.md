# Railway Dockerfile 에러 해결 가이드

## 문제 상황

Railway에서 다음 에러가 발생하는 경우:

### 에러 1: Dockerfile을 찾을 수 없음
```
Dockerfile `Dockerfile` does not exist
```

**의미**: Railway가 Dockerfile을 찾을 수 없습니다.

### 에러 2: Dockerfile 빌드 실패
```
ERROR: failed to build: failed to solve: failed to compute cache key: 
failed to calculate checksum of ref ... "/||": not found
```

**의미**: Dockerfile의 `COPY .env` 명령어에서 쉘 리다이렉션을 사용할 수 없습니다.

## 원인

### 에러 1의 원인:
1. **Dockerfile이 프로젝트 루트에 없음**
2. **railway.json의 dockerfilePath 설정이 잘못됨**
3. **Railway의 Root Directory 설정이 잘못됨**

### 에러 2의 원인:
1. **Dockerfile에서 쉘 리다이렉션 사용**
   - `COPY .env .env 2>/dev/null || true` 같은 명령어는 작동하지 않음
   - Dockerfile의 `COPY` 명령어는 쉘 명령어가 아님
2. **`.env` 파일이 빌드 컨텍스트에 없음**
   - `.env` 파일이 `.gitignore`에 있어서 Git에 커밋되지 않음
   - Railway 빌드 시 `.env` 파일이 없어서 `COPY` 명령어 실패

## 해결 방법

### ⚠️ 중요: Dockerfile 수정

#### 에러 2 해결: .env 파일 복사 명령어 제거

Dockerfile에서 `.env` 파일 복사 명령어를 제거해야 합니다:

**수정 전:**
```dockerfile
# .env 파일 복사 (선택사항, 없어도 됨)
COPY .env .env 2>/dev/null || true
```

**수정 후:**
```dockerfile
# .env 파일은 Railway 환경 변수로 관리되므로 복사하지 않음
# Railway에서 환경 변수를 직접 설정하면 됩니다
```

**이유:**
- Dockerfile의 `COPY` 명령어는 쉘 리다이렉션을 지원하지 않음
- Railway에서는 환경 변수를 직접 설정하므로 `.env` 파일이 필요 없음
- `.env` 파일은 보안상 Git에 커밋하지 않는 것이 좋음

#### 에러 3 해결: 베이스 이미지 업데이트

Debian Buster가 더 이상 지원되지 않으므로 더 최신 베이스 이미지를 사용해야 합니다:

**수정 전:**
```dockerfile
FROM python:3.11-slim-buster
```

**수정 후:**
```dockerfile
FROM python:3.11-slim
```

**이유:**
- Debian Buster는 지원이 종료되어 저장소를 찾을 수 없음
- `python:3.11-slim`은 최신 Debian 버전(Bullseye 또는 Bookworm)을 사용
- 더 안정적이고 보안 업데이트가 제공됨

#### 에러 4 해결: MariaDB Connector/C 설치

`mariadb` Python 패키지를 설치하려면 MariaDB Connector/C가 필요합니다:

**수정 전:**
```dockerfile
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*
```

**수정 후:**
```dockerfile
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
```

**이유:**
- `mariadb` Python 패키지는 MariaDB Connector/C를 시스템에 설치해야 함
- `default-libmysqlclient-dev`: MariaDB Connector/C 개발 라이브러리
- `build-essential`: C 컴파일러 및 빌드 도구 (일부 Python 패키지 빌드에 필요)

#### 에러 5 해결: PORT 환경 변수 확장 문제

Railway의 `$PORT` 환경 변수가 확장되지 않는 경우:

**수정 전:**
```dockerfile
CMD uvicorn vss-api:app --host 0.0.0.0 --port ${PORT:-8001}
```

**수정 후:**
```dockerfile
CMD ["sh", "-c", "uvicorn vss-api:app --host 0.0.0.0 --port ${PORT:-8001}"]
```

**이유:**
- Dockerfile의 `CMD`는 기본적으로 exec 형식으로 실행되어 환경 변수 확장이 안 됨
- 쉘 형식(`["sh", "-c", "..."]`)을 사용하면 환경 변수가 제대로 확장됨
- `${PORT:-8001}`: `PORT` 환경 변수가 없으면 기본값 `8001` 사용

**railway.json 설정:**
- Dockerfile의 `CMD`를 사용하므로 `startCommand`는 생략 가능
- 또는 `startCommand`를 제거하고 Dockerfile의 `CMD`만 사용 (권장)
```json
{
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**주의:**
- Railway의 `startCommand`는 단일 명령어만 지원하므로 `cd` 같은 쉘 명령어를 직접 사용할 수 없음
- Dockerfile의 `WORKDIR`이 이미 설정되어 있으므로 `cd`가 필요 없음

### 방법 1: railway.json 수정 (에러 1 해결)

`railway.json`의 `dockerfilePath`를 명시적으로 설정:

```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "./Dockerfile"
  }
}
```

**또는 절대 경로 사용:**
```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  }
}
```

### 방법 2: Railway 대시보드에서 설정

Railway 대시보드에서:

1. 프로젝트 → **Settings** → **Deploy**
2. **Root Directory** 확인:
   - 프로젝트 루트: 비워두기 또는 `.`
   - `src/api` 디렉토리: `src/api` (권장하지 않음)
3. **Dockerfile Path** 확인:
   - 프로젝트 루트에 있으면: `Dockerfile` 또는 `./Dockerfile`
   - 다른 위치에 있으면: 상대 경로 지정

### 방법 3: Dockerfile 위치 확인

Dockerfile이 프로젝트 루트에 있는지 확인:

```bash
# 프로젝트 루트에서
ls -la Dockerfile

# 또는 Windows에서
dir Dockerfile
```

**Dockerfile이 다른 위치에 있는 경우:**
- `railway.json`의 `dockerfilePath`를 해당 경로로 수정
- 또는 Dockerfile을 프로젝트 루트로 이동

## 현재 프로젝트 구조

```
Vue-test/
├── Dockerfile          ← 프로젝트 루트에 있음
├── railway.json
├── requirements.txt
├── src/
│   └── api/
│       └── vss-api.py
└── ...
```

**올바른 설정:**
- Root Directory: `.` (프로젝트 루트)
- Dockerfile Path: `Dockerfile` 또는 `./Dockerfile`

## 확인 방법

### 1. 파일 존재 확인

```bash
# 프로젝트 루트에서
ls -la | grep Dockerfile

# 또는
cat Dockerfile
```

### 2. railway.json 확인

```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "./Dockerfile"  // 또는 "Dockerfile"
  }
}
```

### 3. Railway 설정 확인

Railway 대시보드:
1. 프로젝트 → Settings → Deploy
2. Root Directory 확인
3. Dockerfile Path 확인

## 문제 해결 체크리스트

- [ ] Dockerfile이 프로젝트 루트에 있는지 확인
- [ ] `railway.json`의 `dockerfilePath` 설정 확인
- [ ] Railway 대시보드의 Root Directory 설정 확인
- [ ] Railway 대시보드의 Dockerfile Path 설정 확인
- [ ] 변경사항 커밋 및 푸시
- [ ] Railway 재배포

## 추가 리소스

- [Railway 문제 해결 가이드](./RAILWAY_TROUBLESHOOTING.md)
- [Railway 502 에러 해결](./RAILWAY_502_FIX.md)

