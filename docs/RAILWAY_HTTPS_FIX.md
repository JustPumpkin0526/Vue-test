# Railway HTTPS/TLS 에러 해결 가이드

## 문제 상황

Railway 로그에서 다음 메시지가 나타나는 경우:

```
automatic HTTPS is completely disabled for server
HTTP/2 skipped because it requires TLS
HTTP/3 skipped because it requires TLS
```

## 원인

이 메시지는 Railway의 Caddy 프록시가 TLS/HTTPS를 설정하지 못했다는 의미입니다. 하지만 이것은 **경고**일 뿐이며, Railway는 자동으로 HTTPS를 제공합니다.

**중요**: Railway는 자동으로 HTTPS를 제공하므로, 애플리케이션은 HTTP로 리스닝하면 됩니다.

## 해결 방법

### 1. 애플리케이션이 올바른 포트에서 리스닝하는지 확인

Railway는 `$PORT` 환경 변수를 제공합니다. 애플리케이션이 이 포트에서 리스닝해야 합니다.

**확인 사항:**

1. **Dockerfile 확인**
   ```dockerfile
   CMD uvicorn vss-api:app --host 0.0.0.0 --port ${PORT:-8001}
   ```
   - `$PORT` 환경 변수 사용 확인

2. **railway.json 확인**
   ```json
   {
     "deploy": {
       "startCommand": "cd /app/src/api && uvicorn vss-api:app --host 0.0.0.0 --port $PORT"
     }
   }
   ```
   - `$PORT` 환경 변수 사용 확인

### 2. Railway 로그에서 애플리케이션 시작 확인

Railway 대시보드 → Deployments → View Logs에서 다음 메시지 확인:

**정상 시작:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:XXXX
```

**문제:**
- 애플리케이션이 시작되지 않음
- 포트 관련 에러

### 3. Railway 서비스 상태 확인

Railway 대시보드에서:
1. 프로젝트 → 서비스 상태 확인
2. "Running" 상태인지 확인
3. URL이 정상적으로 할당되었는지 확인

### 4. API 서버 직접 테스트

```bash
# HTTPS URL로 직접 접속 테스트
curl https://vssproject-production.up.railway.app/docs

# 또는 브라우저에서
# https://vssproject-production.up.railway.app/docs
```

**정상 응답이면:**
- Railway가 자동으로 HTTPS를 제공하고 있음
- 애플리케이션은 정상 작동 중
- 경고 메시지는 무시해도 됨

**502 에러면:**
- 애플리케이션이 시작되지 않았거나 포트 문제
- Railway 문제 해결 가이드 참고

## 이 경고 메시지가 나타나는 이유

Railway는 내부적으로 Caddy 웹서버를 사용하여:
1. 자동 HTTPS 인증서 관리
2. HTTP → HTTPS 리다이렉트
3. 로드 밸런싱

경고 메시지는 Caddy의 내부 설정 관련이지만, Railway가 자동으로 처리하므로 **무시해도 됩니다**.

## 실제 문제인지 확인

### 정상 작동 확인

1. **API 서버 접속 테스트**
   ```bash
   curl https://vssproject-production.up.railway.app/docs
   ```
   - 정상 응답이면 문제 없음

2. **Vercel에서 요청 테스트**
   - 브라우저 개발자 도구 → Network 탭
   - 요청이 성공하는지 확인
   - Railway 로그에 요청이 기록되는지 확인

### 실제 문제인 경우

다음 증상이 있으면 문제입니다:

1. **502 Bad Gateway**
   - 애플리케이션이 시작되지 않음
   - 포트 설정 문제

2. **요청이 Railway에 도달하지 않음**
   - Vercel 환경 변수 문제
   - CORS 문제

3. **연결 타임아웃**
   - 애플리케이션이 크래시됨
   - 데이터베이스 연결 실패

## 문제 해결 체크리스트

- [ ] Railway 로그에서 애플리케이션 시작 메시지 확인
- [ ] API 서버 직접 접속 테스트 (`/docs` 엔드포인트)
- [ ] Railway 서비스가 "Running" 상태인지 확인
- [ ] `$PORT` 환경 변수 사용 확인
- [ ] Vercel에서 요청이 성공하는지 확인

## 추가 리소스

- [Railway 문제 해결 가이드](./RAILWAY_TROUBLESHOOTING.md)
- [Railway + Vercel 연동 가이드](./RAILWAY_VERCEL_SETUP.md)
- [Vercel → Railway 디버깅 가이드](./VERCEL_RAILWAY_DEBUG.md)

## 결론

**이 경고 메시지는 일반적으로 무시해도 됩니다.** Railway가 자동으로 HTTPS를 제공하므로, 애플리케이션이 HTTP로 리스닝하면 됩니다.

실제 문제가 있는지 확인하려면:
1. API 서버 직접 접속 테스트
2. Vercel에서 요청이 성공하는지 확인
3. Railway 로그에서 실제 에러 확인

