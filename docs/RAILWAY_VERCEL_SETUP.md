# Railway API + Vercel 프론트엔드 연동 가이드

Railway에 배포된 API 서버와 Vercel에 배포된 프론트엔드를 연동하는 방법입니다.

## 현재 배포 상태

- ⚠️ **API 서버**: `https://vssproject-production.up.railway.app` (Railway) - 502 에러 발생 중
- 🔄 **프론트엔드**: Vercel 배포 예정

### ⚠️ 502 에러 해결 필요

Railway에서 502 에러가 발생하는 경우, 다음을 확인하세요:

1. **Railway 로그 확인**: Railway 대시보드 → Deployments → View Logs
2. **포트 설정 확인**: `$PORT` 환경 변수 사용 여부
3. **시작 명령어 확인**: `railway.json` 또는 Railway 설정에서 확인

자세한 내용은 [Railway 문제 해결 가이드](./RAILWAY_TROUBLESHOOTING.md)를 참고하세요.

## 1. Vercel 환경 변수 설정

### Vercel 대시보드에서 설정

1. [Vercel 대시보드](https://vercel.com) 접속
2. 프로젝트 선택
3. **Settings** → **Environment Variables** 이동
4. 다음 환경 변수 추가:

| 이름 | 값 | 환경 |
|-----|-----|------|
| `VITE_API_BASE_URL` | `https://vssproject-production.up.railway.app` | Production, Preview, Development |

5. **Save** 클릭
6. 프로젝트 재배포 (자동 또는 수동)

### 또는 Vercel CLI 사용

```bash
# Vercel CLI 설치 (없는 경우)
npm i -g vercel

# 환경 변수 추가
vercel env add VITE_API_BASE_URL production
# 값 입력: https://vssproject-production.up.railway.app

# 재배포
vercel --prod
```

## 2. Railway SMTP 설정 (이메일 인증 코드 발송용)

회원가입 및 비밀번호 재설정 시 이메일 인증 코드를 발송하려면 SMTP 설정이 필요합니다.

### Railway 환경 변수 설정

Railway → Variables 탭에서 다음 환경 변수 추가:

**Gmail 사용 시 (권장):**
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

**⚠️ 중요:**
- Gmail의 경우 **앱 비밀번호**를 사용해야 합니다 (일반 비밀번호 작동 안 함)
- 앱 비밀번호 생성 방법: [Google 계정 설정](https://myaccount.google.com/apppasswords)
- 2단계 인증이 활성화되어 있어야 합니다

자세한 내용은 [Railway SMTP 설정 가이드](./RAILWAY_SMTP_SETUP.md)를 참고하세요.

## 3. Railway CORS 설정 (선택사항)

API 서버가 Vercel 도메인에서의 요청을 허용하도록 설정합니다.

### 자동 설정 (권장)

코드가 자동으로 Vercel 도메인을 감지하도록 업데이트되었습니다. 추가 설정 불필요합니다.

### 수동 설정 (필요한 경우)

Railway 대시보드에서 환경 변수 추가:

1. Railway 프로젝트 → **Variables** 탭
2. 다음 환경 변수 추가:

```
CORS_ALLOWED_ORIGINS=https://your-app.vercel.app,https://your-app-git-main.vercel.app
```

**참고**: Vercel 도메인은 배포 후 확인할 수 있습니다.

## 4. 배포 확인

### API 서버 확인

```bash
# API 문서 확인
curl https://vssproject-production.up.railway.app/docs

# 또는 브라우저에서 접속
# https://vssproject-production.up.railway.app/docs
```

### 프론트엔드 확인

1. Vercel 배포 완료 후 배포 URL 확인
2. 브라우저 개발자 도구 → Network 탭 열기
3. 페이지 로드 후 API 요청 확인:
   - 요청 URL이 `https://vssproject-production.up.railway.app`로 시작하는지 확인
   - CORS 오류가 없는지 확인

## 5. 테스트

### 로그인 테스트

1. Vercel 배포된 사이트 접속
2. 로그인 페이지에서 테스트 계정으로 로그인
3. Network 탭에서 `/login` 요청 확인
4. 성공적으로 로그인되는지 확인

### API 연결 테스트

브라우저 콘솔에서:

```javascript
// API 연결 테스트
fetch('https://vssproject-production.up.railway.app/docs')
  .then(res => res.text())
  .then(data => console.log('API 연결 성공'))
  .catch(err => console.error('API 연결 실패:', err));
```

## 6. 문제 해결

### CORS 오류

**증상:**
```
Access to fetch at 'https://vssproject-production.up.railway.app/...' 
from origin 'https://your-app.vercel.app' has been blocked by CORS policy
```

**해결:**
1. Railway 환경 변수에 `CORS_ALLOWED_ORIGINS` 추가
2. Vercel 도메인을 정확히 입력 (프로토콜 포함)
3. Railway 서비스 재시작

### API 연결 실패

**증상:**
```
Failed to fetch
Network error
```

**해결:**
1. `VITE_API_BASE_URL` 환경 변수 확인
2. Vercel 프로젝트 재배포
3. Railway API 서버가 실행 중인지 확인

### 환경 변수 미적용

**해결:**
1. Vercel 대시보드에서 환경 변수 재확인
2. 프로젝트 재배포 (Settings → Deployments → Redeploy)
3. 빌드 로그에서 환경 변수 확인

## 7. 프로덕션 체크리스트

- [ ] Railway API 서버 배포 완료
- [ ] API 서버 URL 확인: `https://vssproject-production.up.railway.app`
- [ ] Railway SMTP 환경 변수 설정 (이메일 인증용)
- [ ] Vercel 환경 변수 `VITE_API_BASE_URL` 설정
- [ ] Vercel 프론트엔드 배포 완료
- [ ] CORS 설정 확인 (필요시)
- [ ] 로그인 기능 테스트
- [ ] 회원가입 인증 코드 발송 테스트
- [ ] API 요청 테스트
- [ ] 브라우저 콘솔 에러 확인

## 참고

- Railway API URL은 변경될 수 있습니다 (프로젝트 재배포 시)
- Railway 무료 티어는 일정 시간 후 서비스가 일시 중지될 수 있습니다
- 프로덕션 환경에서는 커스텀 도메인 사용 권장

