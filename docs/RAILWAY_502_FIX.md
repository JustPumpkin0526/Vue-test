# Railway 502 에러 즉시 해결 가이드

## 현재 문제

```
curl https://vssproject-production.up.railway.app/docs
{"status":"error","code":502,"message":"Application failed to respond"}
```

**의미**: Railway에서 애플리케이션이 응답하지 않거나 시작되지 않았습니다.

## 즉시 확인 사항

### ⚠️ 중요: railway.json 수정 필요

`railway.json`의 `startCommand`에서 `cd /app/src/api`를 제거해야 합니다. Dockerfile에서 이미 `WORKDIR /app/src/api`로 설정되어 있기 때문입니다.

**수정 전:**
```json
"startCommand": "cd /app/src/api && uvicorn vss-api:app --host 0.0.0.0 --port $PORT"
```

**수정 후:**
```json
"startCommand": "uvicorn vss-api:app --host 0.0.0.0 --port $PORT"
```

### 1. Railway 로그 확인 (가장 중요!)

Railway 대시보드:
1. 프로젝트 → **Deployments** 탭
2. 최신 배포 클릭
3. **View Logs** 클릭
4. 다음을 확인:

**정상 시작 로그:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:XXXX
✓ 데이터베이스 연결 성공 (startup)
✓ 애플리케이션이 시작되었습니다.
```

**에러 로그 예시:**
```
ModuleNotFoundError: No module named 'fastapi'
Can't connect to MySQL server
Connection refused
Port already in use
```

### 2. 포트 설정 확인

**확인 사항:**
- `railway.json`의 `startCommand`에서 `$PORT` 사용 확인
- `Dockerfile`의 `CMD`에서 `${PORT:-8001}` 사용 확인

**현재 설정:**
- ✅ `railway.json`: `uvicorn vss-api:app --host 0.0.0.0 --port $PORT`
- ✅ `Dockerfile`: `CMD uvicorn vss-api:app --host 0.0.0.0 --port ${PORT:-8001}`

### 3. 데이터베이스 연결 확인

**가능한 문제:**
- 데이터베이스 연결 실패로 애플리케이션이 시작되지 않음
- Railway 환경 변수에 DB 설정이 없음

**확인 방법:**
Railway → Variables 탭에서 다음 변수 확인:
```
DB_HOST=your-db-host
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=vss
```

**⚠️ 중요:**
- `localhost` 또는 `127.0.0.1`은 사용하지 마세요
- Railway는 외부 데이터베이스에 연결해야 합니다
- DB 서버의 방화벽에서 Railway IP 허용 필요

### 4. 애플리케이션 시작 확인

Railway 로그에서 다음 메시지 확인:

**정상:**
```
INFO:     Uvicorn running on http://0.0.0.0:XXXX
```

**문제:**
- 이 메시지가 없으면 애플리케이션이 시작되지 않음
- 포트 번호가 표시되지 않으면 포트 설정 문제

## 빠른 해결 방법

### 방법 1: Railway 로그 확인 후 문제 해결

1. **로그에서 정확한 에러 메시지 확인**
2. **에러 유형에 따라 해결:**

#### 데이터베이스 연결 실패
- Railway 환경 변수에 DB 설정 추가
- DB 서버 접근 가능 여부 확인

#### 모듈을 찾을 수 없음
- `requirements.txt` 확인
- Railway 빌드 로그에서 `pip install` 성공 여부 확인

#### 포트 문제
- `$PORT` 환경 변수 사용 확인
- `railway.json`의 `startCommand` 확인

### 방법 2: Railway 서비스 재시작

1. Railway 대시보드 → 프로젝트
2. 서비스 선택
3. **Settings** → **Restart** 클릭

### 방법 4: 환경 변수 재확인

Railway → Variables 탭에서 필수 변수 확인:

**데이터베이스 (필수):**
```
DB_HOST=your-db-host
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=vss
```

**VIA 서버 (선택사항):**
```
VIA_SERVER_URL=http://your-via-server:8101
```

## 단계별 체크리스트

### 1단계: 로그 확인
- [ ] Railway 로그 열기
- [ ] 애플리케이션 시작 메시지 확인
- [ ] 에러 메시지 확인

### 2단계: 환경 변수 확인
- [ ] DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME 설정 확인
- [ ] 값에 공백이나 오타가 없는지 확인

### 3단계: 포트 설정 확인
- [ ] `railway.json`의 `startCommand`에 `$PORT` 사용 확인
- [ ] `Dockerfile`의 `CMD`에 `${PORT:-8001}` 사용 확인

### 4단계: 재배포
- [ ] Railway 서비스 재시작
- [ ] 또는 GitHub에 푸시하여 자동 재배포

## 일반적인 해결 방법

### 데이터베이스 연결 문제

**증상:**
- 로그에 `Can't connect to MySQL server` 에러
- 또는 `Connection refused` 에러

**해결:**
1. Railway 환경 변수에 DB 설정 추가
2. DB 서버가 외부 접근 가능한지 확인
3. DB 서버 방화벽에서 Railway IP 허용

### 포트 설정 문제

**증상:**
- 로그에 `Address already in use` 에러
- 또는 포트 관련 에러

**해결:**
1. `railway.json`의 `startCommand` 확인
2. `$PORT` 환경 변수 사용 확인
3. 하드코딩된 포트 번호 제거

### 의존성 문제

**증상:**
- 로그에 `ModuleNotFoundError` 에러

**해결:**
1. `requirements.txt` 파일 확인
2. Railway 빌드 로그에서 `pip install` 성공 여부 확인
3. 필요시 빌드 명령어 추가

## 추가 디버깅

### Railway 로그에서 확인할 사항

1. **빌드 단계**
   - 의존성 설치 성공 여부
   - FFmpeg 설치 여부

2. **시작 단계**
   - 애플리케이션 시작 메시지
   - 포트 바인딩 메시지
   - 데이터베이스 연결 메시지

3. **런타임 에러**
   - 데이터베이스 연결 에러
   - 환경 변수 누락 에러
   - 모듈 import 에러

### 로컬에서 테스트

로컬에서 동일한 설정으로 테스트:

```bash
# 환경 변수 설정
export PORT=8001
export DB_HOST=your-db-host
export DB_PORT=3306
export DB_USER=root
export DB_PASSWORD=your-password
export DB_NAME=vss

# 애플리케이션 실행
cd src/api
uvicorn vss-api:app --host 0.0.0.0 --port $PORT
```

로컬에서 작동하면 Railway 설정 문제일 가능성이 높습니다.

## 참고

- [Railway 문제 해결 가이드](./RAILWAY_TROUBLESHOOTING.md)
- [Railway 배포 체크리스트](./RAILWAY_DEPLOYMENT_CHECKLIST.md)
- [Railway HTTPS/TLS 에러 해결](./RAILWAY_HTTPS_FIX.md)

