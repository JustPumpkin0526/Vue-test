# Railway 배포 체크리스트

## 502 Connection Refused 에러 해결

에러 로그에서 `connection refused`가 발생하는 경우, 다음을 확인하세요.

## 1. Railway 로그 확인 (가장 중요!)

Railway 대시보드에서:
1. 프로젝트 → **Deployments** 탭
2. 최신 배포 클릭
3. **View Logs** 클릭
4. 다음을 확인:

### 정상 시작 로그 예시
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:XXXX
```

### 에러 로그 예시
```
ModuleNotFoundError: No module named 'fastapi'
Connection refused: database connection failed
Port already in use
```

## 2. 필수 환경 변수 확인

Railway → Variables 탭에서 다음 변수들이 모두 설정되어 있는지 확인:

### 데이터베이스 연결 (필수)
```
DB_HOST=your-db-host
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=vss
```

### VIA 서버 (선택사항, 없어도 시작은 가능)
```
VIA_SERVER_URL=http://your-via-server:8101
```

### 기타 (선택사항)
```
OLLAMA_BASE_URL=http://your-ollama:11434
OLLAMA_MODEL=llama3
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

## 3. Railway 설정 확인

Railway → Settings → Deploy:

### 옵션 1: Dockerfile 사용 (권장)
- **Builder**: `Dockerfile`
- **Dockerfile Path**: `Dockerfile` (프로젝트 루트)
- **Root Directory**: (비워두기)

### 옵션 2: Nixpacks 사용
- **Builder**: `Nixpacks`
- **Root Directory**: (비워두기 또는 `src/api`)
- **Start Command**: `cd src/api && uvicorn vss-api:app --host 0.0.0.0 --port $PORT`

## 4. 데이터베이스 연결 문제

### 문제: 데이터베이스 연결 실패

**증상:**
- 로그에 `Connection refused` 또는 `Can't connect to MySQL server` 에러

**해결:**
1. **DB_HOST 확인**
   - 로컬 DB: `localhost` 또는 `127.0.0.1` (Railway에서는 작동하지 않음!)
   - 외부 DB: 실제 IP 주소 또는 도메인
   - Railway 내부 DB: Railway가 제공하는 내부 주소 사용

2. **방화벽 확인**
   - DB 서버의 방화벽에서 Railway IP 허용
   - 또는 DB 서버가 공개적으로 접근 가능한지 확인

3. **연결 테스트**
   ```bash
   # 로컬에서 테스트
   mysql -h your-db-host -P 3306 -u root -p
   ```

## 5. 애플리케이션 시작 실패

### 문제: 모듈을 찾을 수 없음

**증상:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**해결:**
1. `requirements.txt` 파일이 프로젝트 루트에 있는지 확인
2. Railway 로그에서 `pip install`이 성공했는지 확인
3. 필요시 Build Command 추가:
   ```bash
   pip install --upgrade pip && pip install -r requirements.txt
   ```

### 문제: FFmpeg 누락

**증상:**
```
MoviePy: ffmpeg not found
```

**해결:**
- Dockerfile을 사용하는 경우: FFmpeg가 이미 포함되어 있음
- Nixpacks를 사용하는 경우: `nixpacks.toml`에 `ffmpeg` 추가 확인

## 6. 포트 설정 문제

### 문제: 잘못된 포트 사용

**증상:**
- 로그에 `Address already in use` 또는 포트 관련 에러

**해결:**
1. `$PORT` 환경 변수 사용 확인
2. Dockerfile의 CMD 명령어 확인:
   ```dockerfile
   CMD ["sh", "-c", "uvicorn vss-api:app --host 0.0.0.0 --port ${PORT:-8001}"]
   ```
3. `railway.json`의 startCommand 확인:
   ```json
   "startCommand": "uvicorn vss-api:app --host 0.0.0.0 --port $PORT"
   ```

## 7. 시작 시간 초과

### 문제: 애플리케이션이 시작하는 데 너무 오래 걸림

**증상:**
- Railway가 타임아웃 전에 애플리케이션 시작을 기다림

**해결:**
1. **데이터베이스 연결 최적화**
   - 연결 풀 크기 줄이기
   - 타임아웃 설정 추가

2. **시작 시 무거운 작업 제거**
   - `@app.on_event("startup")`에서 무거운 작업 제거
   - 백그라운드 작업으로 이동

## 8. 디렉토리 구조 문제

### 문제: 파일을 찾을 수 없음

**증상:**
```
FileNotFoundError: [Errno 2] No such file or directory: './videos'
```

**해결:**
1. **상대 경로 확인**
   - `src/api/vss-api.py`에서 `./videos`는 `src/api/videos`를 의미
   - Railway에서는 작업 디렉토리가 중요

2. **절대 경로 사용 고려**
   ```python
   videos_dir = Path("/app/videos")  # Dockerfile의 WORKDIR 기준
   ```

## 9. 빠른 해결 방법

### 단계별 체크리스트

1. ✅ Railway 로그 확인 (가장 중요!)
2. ✅ 필수 환경 변수 설정 확인
3. ✅ 데이터베이스 연결 가능 여부 확인
4. ✅ `requirements.txt` 파일 존재 확인
5. ✅ Dockerfile 또는 Nixpacks 설정 확인
6. ✅ 포트 설정 (`$PORT` 사용) 확인
7. ✅ 재배포 시도

### 재배포 방법

1. **GitHub 푸시로 자동 재배포**
   ```bash
   git add .
   git commit -m "Fix Railway deployment"
   git push
   ```

2. **Railway에서 수동 재배포**
   - Railway 대시보드 → Deployments → 최신 배포 → Redeploy

3. **환경 변수 변경 후 재배포**
   - Variables 탭에서 환경 변수 수정
   - 자동으로 재배포됨

## 10. 로그 분석 팁

### 정상 시작 로그
```
Building...
Installing dependencies...
Starting...
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:XXXX (Press CTRL+C to quit)
```

### 일반적인 에러 패턴

1. **의존성 에러**
   ```
   ERROR: Could not find a version that satisfies the requirement
   ```

2. **데이터베이스 에러**
   ```
   Can't connect to MySQL server on 'xxx'
   ```

3. **포트 에러**
   ```
   Address already in use
   ```

4. **모듈 에러**
   ```
   ModuleNotFoundError: No module named 'xxx'
   ```

## 11. Railway 지원

문제가 계속되면:
1. Railway 대시보드 → Support
2. 로그와 함께 문의
3. 에러 메시지와 함께 상세 설명 제공

## 참고

- [Railway 공식 문서](https://docs.railway.app/)
- [Railway 문제 해결 가이드](./RAILWAY_TROUBLESHOOTING.md)

