# Vercel + API 서버 배포 전략

## 아키텍처 개요

```
┌─────────────────┐         ┌─────────────────┐
│   Vercel        │         │   API 서버       │
│   (프론트엔드)   │ ──────► │   (FastAPI)      │
│   Vue.js        │  HTTP   │   별도 배포      │
└─────────────────┘         └─────────────────┘
```

## 배포 전략

### 옵션 1: 프론트엔드만 Vercel, API는 별도 서버 (권장)

**장점:**
- ✅ Vercel의 빠른 CDN 활용
- ✅ API 서버 독립적 운영
- ✅ 각각의 스케일링 가능
- ✅ API 서버에 더 많은 제어권

**단점:**
- ⚠️ 두 개의 배포 관리 필요
- ⚠️ CORS 설정 필요

**구현 방법:**

1. **프론트엔드 (Vercel)**
   - Vercel에 Vue.js 앱 배포
   - 환경 변수: `VITE_API_BASE_URL=https://your-api.com`

2. **백엔드 API (별도 서버)**
   - Railway, Render 등에 FastAPI 배포
   - CORS 설정으로 Vercel 도메인 허용

### 옵션 2: Vercel Serverless Functions 사용 (제한적)

Vercel은 Python 서버리스 함수를 지원하지만, FastAPI 전체 앱을 배포하기는 어렵습니다.

**제한사항:**
- ❌ 파일 시스템 접근 제한
- ❌ 장시간 실행 불가 (타임아웃)
- ❌ 대용량 파일 처리 어려움
- ❌ 영구 저장소 없음

**대안:**
- 핵심 API만 서버리스 함수로 변환
- 복잡한 로직은 별도 서버 유지

### 옵션 3: 전체를 Vercel에 배포 (비권장)

현재 프로젝트 구조상 권장하지 않습니다:
- FastAPI 앱이 복잡함
- 파일 업로드/처리 필요
- 데이터베이스 연결 필요
- 장시간 실행 작업 필요

## 권장 배포 구성

### 1. 프론트엔드: Vercel

```bash
# Vercel에 배포
vercel --prod
```

**환경 변수:**
```
VITE_API_BASE_URL=https://your-api.railway.app
```

### 2. 백엔드 API: Railway (배포 완료 ✅)

Railway에 API 서버가 배포되었습니다:
- **API URL**: `https://vssproject-production.up.railway.app`

**Railway 환경 변수 설정:**
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `VIA_SERVER_URL`
- `OLLAMA_BASE_URL`, `OLLAMA_MODEL`
- `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
- `CORS_ALLOWED_ORIGINS` (선택사항, Vercel 도메인)

### 3. CORS 설정

API 서버(`vss-api.py`)의 CORS 설정이 자동으로 Vercel 도메인을 허용하도록 업데이트되었습니다.

**Railway 환경 변수 (선택사항):**
```
CORS_ALLOWED_ORIGINS=https://your-app.vercel.app,https://your-app-git-main.vercel.app
```

또는 코드에서 자동으로 Vercel 도메인을 감지합니다 (환경 변수 `VERCEL_URL` 사용).

**수동 설정이 필요한 경우:**
Railway 대시보드에서 환경 변수 추가:
- `CORS_ALLOWED_ORIGINS`: Vercel 도메인을 쉼표로 구분하여 추가

## 환경 변수 관리

### Vercel (프론트엔드)

```
VITE_API_BASE_URL=https://vssproject-production.up.railway.app
```

**설정 방법:**
1. Vercel 대시보드 → 프로젝트 → Settings → Environment Variables
2. `VITE_API_BASE_URL` 추가
3. 값: `https://vssproject-production.up.railway.app`
4. 환경: Production, Preview, Development 모두 선택
5. 저장 후 재배포

### API 서버 (Railway 등)

```
DB_HOST=your-db-host
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-password
DB_NAME=vss
VIA_SERVER_URL=http://your-via-server:8101
OLLAMA_BASE_URL=http://your-ollama:11434
OLLAMA_MODEL=llama3
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

## 배포 체크리스트

### 프론트엔드 (Vercel)

- [ ] `vercel.json` 설정 완료
- [ ] 이미지 파일 Git에 커밋
- [ ] 환경 변수 `VITE_API_BASE_URL` 설정
- [ ] 빌드 성공 확인
- [ ] 배포 URL 확인

### 백엔드 API (별도 서버)

- [ ] API 서버 배포 완료
- [ ] 환경 변수 모두 설정
- [ ] CORS 설정 (Vercel 도메인 허용)
- [ ] API 엔드포인트 테스트
- [ ] 데이터베이스 연결 확인

## 테스트

### 1. 프론트엔드 테스트

```bash
# 로컬에서 API URL 확인
curl https://your-app.vercel.app
```

### 2. API 서버 테스트

```bash
# API 서버 헬스 체크
curl https://vssproject-production.up.railway.app/docs

# 또는 브라우저에서 접속
# https://vssproject-production.up.railway.app/docs
```

### 3. 통합 테스트

브라우저에서 Vercel 배포된 사이트 접속 후:
- 로그인 기능 테스트
- API 호출 확인 (브라우저 개발자 도구 Network 탭)

## 문제 해결

### CORS 오류

**증상:**
```
Access to fetch at 'https://api...' from origin 'https://app.vercel.app' has been blocked by CORS policy
```

**해결:**
API 서버의 CORS 설정에 Vercel 도메인 추가

### API 연결 실패

**증상:**
```
Failed to fetch
Network error
```

**해결:**
1. `VITE_API_BASE_URL` 환경 변수 확인
2. API 서버가 실행 중인지 확인
3. 방화벽/보안 그룹 설정 확인

### 환경 변수 미적용

**해결:**
1. Vercel 대시보드에서 환경 변수 재설정
2. 프로젝트 재배포
3. 환경 변수 이름이 `VITE_`로 시작하는지 확인

## 참고 자료

- [Vercel 공식 문서](https://vercel.com/docs)
- [Railway 배포 가이드](https://docs.railway.app/)
- [Render 배포 가이드](https://render.com/docs)
- [FastAPI CORS 설정](https://fastapi.tiangolo.com/tutorial/cors/)

