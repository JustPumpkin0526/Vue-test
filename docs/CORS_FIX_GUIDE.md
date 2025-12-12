# CORS 에러 해결 가이드

## 문제 상황

```
Access to XMLHttpRequest at 'http://localhost:8001/login' 
from origin 'https://vss-project.vercel.app' 
has been blocked by CORS policy
```

## 원인

1. **프론트엔드가 하드코딩된 `localhost:8001` 사용**
   - Vercel 환경 변수가 적용되지 않음
   - 빌드 시점에 환경 변수가 없으면 기본값(`localhost:8001`) 사용

2. **Railway API 서버의 CORS 설정**
   - Vercel 도메인이 허용되지 않음

## 해결 방법

### 1. Vercel 환경 변수 설정 (필수)

Vercel 대시보드에서:

1. 프로젝트 → **Settings** → **Environment Variables**
2. 다음 환경 변수 추가:

| 이름 | 값 | 환경 |
|-----|-----|------|
| `VITE_API_BASE_URL` | `https://vssproject-production.up.railway.app` | Production, Preview, Development |

3. **Save** 클릭
4. **프로젝트 재배포** (중요!)

**⚠️ 중요**: 환경 변수 변경 후 반드시 재배포해야 합니다!

### 2. 코드 수정 완료

모든 하드코딩된 `localhost:8001`을 `apiConfig`로 교체했습니다:

- ✅ `Login.vue` - `apiConfig.endpoints.login` 사용
- ✅ `Register.vue` - `apiConfig.endpoints.*` 사용
- ✅ `ResetPassword.vue` - `apiConfig.endpoints.*` 사용
- ✅ `Search.vue` - `apiConfig.endpoints.*` 사용
- ✅ `Summarize.vue` - `apiConfig.endpoints.*` 사용

### 3. Railway CORS 설정 확인

Railway API 서버가 Vercel 도메인을 허용하도록 설정:

**방법 1: 환경 변수 사용 (권장)**

Railway → Variables 탭에서:

```
CORS_ALLOWED_ORIGINS=https://vss-project.vercel.app,https://vss-project-git-main.vercel.app
```

**방법 2: 코드에서 자동 감지**

현재 코드는 `VERCEL_URL` 환경 변수를 자동으로 감지합니다. Railway에서 이 변수를 설정할 필요는 없습니다.

### 4. 재배포 및 확인

#### Vercel 재배포

1. **자동 재배포**: GitHub에 푸시하면 자동 재배포
2. **수동 재배포**: Vercel 대시보드 → Deployments → Redeploy

#### 확인 방법

1. **브라우저 개발자 도구 → Network 탭**
2. **로그인 시도**
3. **요청 URL 확인**:
   - ✅ 정상: `https://vssproject-production.up.railway.app/login`
   - ❌ 문제: `http://localhost:8001/login`

4. **CORS 에러 확인**:
   - ✅ 정상: 요청이 성공적으로 전송됨
   - ❌ 문제: CORS 에러 메시지 표시

## 문제 해결 체크리스트

- [ ] Vercel 환경 변수 `VITE_API_BASE_URL` 설정
- [ ] Vercel 프로젝트 재배포 완료
- [ ] Railway CORS 설정 확인 (필요시)
- [ ] 브라우저에서 요청 URL 확인
- [ ] CORS 에러 해결 확인

## 추가 문제 해결

### 여전히 `localhost:8001`을 사용하는 경우

1. **환경 변수 확인**:
   ```bash
   # Vercel CLI로 확인
   vercel env ls
   ```

2. **빌드 로그 확인**:
   - Vercel 대시보드 → Deployments → Build Logs
   - 환경 변수가 빌드 시점에 포함되었는지 확인

3. **브라우저 캐시 클리어**:
   - 개발자 도구 → Network 탭 → "Disable cache" 체크
   - 또는 하드 리프레시 (Ctrl+Shift+R)

### CORS 에러가 계속 발생하는 경우

1. **Railway 로그 확인**:
   - Railway 대시보드 → Deployments → View Logs
   - CORS 관련 에러 메시지 확인

2. **CORS 설정 확인**:
   - `src/api/vss-api.py`의 CORS 설정 확인
   - `allow_origins`에 Vercel 도메인 포함 확인

3. **프리플라이트 요청 확인**:
   - 브라우저 개발자 도구 → Network 탭
   - OPTIONS 요청이 성공하는지 확인

## 참고

- [Vercel 환경 변수 문서](https://vercel.com/docs/concepts/projects/environment-variables)
- [Railway CORS 설정](./RAILWAY_VERCEL_SETUP.md)

