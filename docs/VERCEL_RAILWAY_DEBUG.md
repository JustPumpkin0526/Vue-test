# Vercel → Railway 요청 디버깅 가이드

Vercel에서 배포한 웹사이트에서 Railway API로 요청이 전달되지 않는 문제를 해결하는 방법입니다.

## 문제 진단

### 1. 브라우저 개발자 도구 확인 (가장 중요!)

브라우저 개발자 도구에서 실제로 어떤 요청이 전송되는지 확인:

1. **F12** 또는 **우클릭 → 검사** 클릭
2. **Network** 탭 열기
3. 페이지 새로고침 또는 로그인 시도
4. 요청 목록 확인:

**확인 사항:**
- 요청 URL이 `https://vssproject-production.up.railway.app`로 시작하는지
- 요청 URL이 `http://localhost:8001`로 시작하는지 (문제!)
- 요청이 전송되었는지 (요청이 보이지 않으면 JavaScript 에러 가능)
- CORS 에러가 있는지

### 2. 콘솔 에러 확인

브라우저 개발자 도구 → **Console** 탭에서:
- JavaScript 에러 확인
- API 요청 관련 에러 확인
- CORS 에러 확인

## 일반적인 원인 및 해결 방법

### 원인 1: Vercel 환경 변수 미설정 또는 미적용

**증상:**
- Network 탭에서 요청 URL이 `http://localhost:8001`로 표시됨
- Railway 로그에 요청이 없음

**해결:**

1. **Vercel 환경 변수 확인**
   - Vercel 대시보드 → 프로젝트 → Settings → Environment Variables
   - `VITE_API_BASE_URL`이 설정되어 있는지 확인
   - 값: `https://vssproject-production.up.railway.app`

2. **환경 변수 재확인**
   - Production, Preview, Development 모두 선택되어 있는지 확인
   - 값에 공백이나 오타가 없는지 확인

3. **프로젝트 재배포 (필수!)**
   - 환경 변수 변경 후 반드시 재배포 필요
   - Vercel 대시보드 → Deployments → 최신 배포 → Redeploy
   - 또는 GitHub에 푸시하여 자동 재배포

4. **빌드 로그 확인**
   - Vercel 대시보드 → Deployments → Build Logs
   - 환경 변수가 빌드 시점에 포함되었는지 확인

### 원인 2: 하드코딩된 localhost URL

**증상:**
- 일부 요청만 `localhost:8001`로 전송됨
- 특정 기능에서만 문제 발생

**해결:**

1. **코드 확인**
   - `src/pages/` 디렉토리의 모든 파일 확인
   - `http://localhost:8001` 또는 `localhost:8001` 검색
   - 모든 하드코딩된 URL을 `apiConfig`로 교체

2. **주요 파일 확인**
   - `Login.vue` - `apiConfig.endpoints.login` 사용 확인
   - `Register.vue` - `apiConfig.endpoints.*` 사용 확인
   - `Search.vue` - `apiConfig.endpoints.*` 사용 확인
   - `Summarize.vue` - `apiConfig.endpoints.*` 사용 확인

3. **import 확인**
   - 각 파일 상단에 `import apiConfig from '@/config/api';` 추가 확인

### 원인 3: CORS 문제로 요청 차단

**증상:**
- Network 탭에서 요청이 보이지만 실패함
- Console에 CORS 에러 메시지
- Railway 로그에 요청이 없음 (브라우저에서 차단됨)

**해결:**

1. **Railway CORS 설정 확인**
   - Railway → Variables 탭
   - `CORS_ALLOWED_ORIGINS` 환경 변수 확인
   - Vercel 도메인 포함 확인

2. **코드에서 CORS 설정 확인**
   - `src/api/vss-api.py`의 CORS 설정 확인
   - 모든 도메인 허용 설정 확인

### 원인 4: Railway API 서버 미실행

**증상:**
- 요청이 전송되지만 응답이 없음
- Railway 로그에 아무것도 없음

**해결:**

1. **Railway 로그 확인**
   - Railway 대시보드 → Deployments → View Logs
   - 애플리케이션이 정상적으로 시작되었는지 확인
   - 다음 메시지 확인:
     ```
     INFO:     Uvicorn running on http://0.0.0.0:XXXX
     ```

2. **API 서버 직접 테스트**
   ```bash
   curl https://vssproject-production.up.railway.app/docs
   ```
   - 정상 응답이면 서버는 실행 중
   - 502 에러면 서버가 실행되지 않음

3. **Railway 서비스 상태 확인**
   - Railway 대시보드 → 프로젝트
   - 서비스가 "Running" 상태인지 확인

### 원인 5: 네트워크 문제

**증상:**
- 요청이 전송되지만 타임아웃
- Network 탭에서 요청이 "Failed" 또는 "Pending" 상태

**해결:**

1. **Railway URL 접근 확인**
   - 브라우저에서 직접 접속: `https://vssproject-production.up.railway.app/docs`
   - 접속 가능하면 네트워크 문제 아님

2. **방화벽 확인**
   - 회사 네트워크나 방화벽에서 Railway 도메인 차단 가능
   - 다른 네트워크에서 테스트

## 단계별 디버깅 체크리스트

### 1단계: 브라우저에서 확인

- [ ] 개발자 도구 → Network 탭 열기
- [ ] 로그인 또는 API 요청 시도
- [ ] 요청 URL 확인 (`localhost:8001`인지 `railway.app`인지)
- [ ] 요청 상태 확인 (성공/실패)
- [ ] Console 탭에서 에러 확인

### 2단계: Vercel 설정 확인

- [ ] Vercel 환경 변수 `VITE_API_BASE_URL` 설정 확인
- [ ] 값이 정확한지 확인 (`https://vssproject-production.up.railway.app`)
- [ ] 환경(Production, Preview, Development) 모두 선택 확인
- [ ] 최근 재배포 여부 확인

### 3단계: Railway 설정 확인

- [ ] Railway 서비스가 "Running" 상태인지 확인
- [ ] Railway 로그에서 애플리케이션 시작 메시지 확인
- [ ] API 서버 직접 접속 테스트 (`/docs` 엔드포인트)
- [ ] CORS 설정 확인

### 4단계: 코드 확인

- [ ] `src/config/api.js`에서 `API_BASE_URL` 확인
- [ ] 모든 페이지에서 `apiConfig` 사용 확인
- [ ] 하드코딩된 `localhost:8001` 검색 및 제거

## 빠른 테스트 방법

### 브라우저 콘솔에서 직접 테스트

Vercel 배포된 사이트에서 브라우저 콘솔(F12) 열고:

```javascript
// 1. 환경 변수 확인
console.log('API URL:', import.meta.env.VITE_API_BASE_URL);

// 2. API 연결 테스트
fetch('https://vssproject-production.up.railway.app/docs')
  .then(res => res.text())
  .then(data => console.log('✅ API 연결 성공'))
  .catch(err => console.error('❌ API 연결 실패:', err));

// 3. 로그인 테스트
fetch('https://vssproject-production.up.railway.app/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'test', password: 'test' })
})
  .then(res => res.json())
  .then(data => console.log('✅ 로그인 요청 성공:', data))
  .catch(err => console.error('❌ 로그인 요청 실패:', err));
```

### 로컬에서 빌드 테스트

```bash
# 환경 변수 설정
export VITE_API_BASE_URL=https://vssproject-production.up.railway.app

# 빌드
npm run build

# 빌드된 파일 확인
grep -r "localhost:8001" dist/
# 결과가 없어야 함 (localhost가 없어야 정상)
```

## 문제 해결 후 확인

문제를 해결한 후:

1. **브라우저 캐시 클리어**
   - 하드 리프레시: `Ctrl+Shift+R` (Windows) 또는 `Cmd+Shift+R` (Mac)
   - 또는 개발자 도구 → Network 탭 → "Disable cache" 체크

2. **재테스트**
   - 로그인 시도
   - Network 탭에서 요청 URL 확인
   - Railway 로그에서 요청 확인

3. **확인 사항**
   - ✅ 요청 URL이 `https://vssproject-production.up.railway.app`로 시작
   - ✅ 요청이 성공적으로 전송됨
   - ✅ Railway 로그에 요청이 기록됨
   - ✅ API 응답이 정상적으로 수신됨

## 추가 리소스

- [CORS 에러 해결 가이드](./CORS_FIX_GUIDE.md)
- [Railway + Vercel 연동 가이드](./RAILWAY_VERCEL_SETUP.md)
- [Railway 문제 해결 가이드](./RAILWAY_TROUBLESHOOTING.md)

