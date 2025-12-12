# Railway 502 에러 빠른 해결 가이드

## 현재 문제

에러 로그:
```
"connection refused"
"upstreamAddress": ""
"upstreamErrors": [{"error":"connection refused"}]
```

**의미**: 애플리케이션이 시작되지 않았거나 포트에서 리스닝하지 않음

## 즉시 확인 사항

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
```

**에러 로그 예시:**
```
ModuleNotFoundError: No module named 'fastapi'
Can't connect to MySQL server
Connection refused
```

### 2. 필수 환경 변수 확인

Railway → **Variables** 탭에서 확인:

```
DB_HOST=your-db-host
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=vss
```

**⚠️ 중요**: 데이터베이스 연결이 실패하면 애플리케이션이 시작되지 않을 수 있습니다!

### 3. 데이터베이스 연결 테스트

로컬에서 테스트:
```bash
mysql -h your-db-host -P 3306 -u root -p
```

**문제:**
- `localhost` 또는 `127.0.0.1`을 사용하면 안 됩니다!
- Railway는 외부 데이터베이스에 연결해야 합니다
- DB 서버의 방화벽에서 Railway IP 허용 필요

## 수정 사항

### 1. Dockerfile 수정
- `$PORT` 환경 변수 사용
- CMD 명령어 수정

### 2. 데이터베이스 연결 개선
- 모듈 레벨 연결 실패 시에도 애플리케이션 시작 계속
- 첫 요청 시 재연결 시도

### 3. railway.json 수정
- 시작 명령어에 작업 디렉토리 명시

## 다음 단계

1. **변경사항 커밋 및 푸시**
   ```bash
   git add .
   git commit -m "Fix Railway deployment: DB connection and port handling"
   git push
   ```

2. **Railway 자동 재배포 대기**
   - GitHub 푸시 후 자동으로 재배포됨

3. **로그 확인**
   - Railway → Deployments → View Logs
   - 정상 시작 메시지 확인

4. **API 테스트**
   ```bash
   curl https://vssproject-production.up.railway.app/docs
   ```

## 여전히 문제가 있다면

1. **Railway 로그의 정확한 에러 메시지 확인**
2. **데이터베이스 연결 가능 여부 확인**
3. **환경 변수 재확인**
4. **Railway 지원팀 문의** (필요시)

## 참고

- [Railway 문제 해결 가이드](./RAILWAY_TROUBLESHOOTING.md)
- [Railway 배포 체크리스트](./RAILWAY_DEPLOYMENT_CHECKLIST.md)

