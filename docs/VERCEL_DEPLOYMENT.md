# Vercel을 사용한 프론트엔드 배포 가이드

이 가이드는 Vercel을 사용하여 Vue.js 프론트엔드를 배포하는 방법을 설명합니다.

## ⚠️ 중요: API 서버는 별도 배포 필요

**Vercel은 프론트엔드(정적 사이트) 배포에 최적화되어 있습니다.**

현재 프로젝트 구조:
- **프론트엔드 (Vue.js)**: Vercel에 배포 가능 ✅
- **백엔드 API (FastAPI)**: 별도 서버 필요 ⚠️

Vercel에서 FastAPI를 직접 배포하는 것은 제한적이므로, **API 서버는 별도로 배포**해야 합니다.

## 목차

1. [사전 요구사항](#사전-요구사항)
2. [Vercel 설정](#vercel-설정)
3. [환경 변수 설정](#환경-변수-설정)
4. [빌드 설정](#빌드-설정)
5. [문제 해결](#문제-해결)

## 사전 요구사항

- GitHub 계정
- Vercel 계정 (https://vercel.com)
- 프로젝트가 GitHub 저장소에 푸시되어 있어야 함

## Vercel 설정

### 1. Vercel 계정 생성 및 프로젝트 연결

1. [Vercel](https://vercel.com)에 가입/로그인
2. "Add New Project" 클릭
3. GitHub 저장소 선택
4. 프로젝트 설정:
   - **Framework Preset**: Vite
   - **Root Directory**: `./` (프로젝트 루트)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

### 2. vercel.json 설정 파일 생성

프로젝트 루트에 `vercel.json` 파일을 생성합니다:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

## 환경 변수 설정

### ⚠️ 필수: API 서버 URL 설정

프론트엔드가 API 서버에 연결하려면 API 서버 URL을 환경 변수로 설정해야 합니다.

### Vercel 대시보드에서 설정

1. 프로젝트 → Settings → Environment Variables
2. 다음 환경 변수 추가:

```
VITE_API_BASE_URL=https://vssproject-production.up.railway.app
```

**중요**: 
- `VITE_` 접두사가 필수입니다 (Vite 환경 변수 규칙)
- 프로덕션, 프리뷰, 개발 환경별로 설정 가능
- HTTPS URL 사용 권장 (Railway는 자동으로 HTTPS 제공)

### 환경별 설정 예시

- **Production**: `https://vssproject-production.up.railway.app`
- **Preview**: `https://vssproject-production.up.railway.app` (또는 별도 API 서버)
- **Development**: `http://localhost:8001` (로컬 개발용)

### API 서버 배포 옵션

API 서버(FastAPI)는 다음 플랫폼 중 하나에 배포해야 합니다:

1. **Railway** (권장)
   - Python 앱 배포 용이
   - 자동 배포 지원
   - 무료 티어 제공

2. **Render**
   - Python 앱 배포 지원
   - 무료 티어 제공

3. **AWS / GCP / Azure**
   - 엔터프라이즈급 솔루션
   - 유료 (일부 무료 티어)

4. **자체 서버**
   - VPS 또는 물리 서버
   - Docker 사용 가능

5. **Vercel Serverless Functions** (제한적)
   - FastAPI 전체 앱 배포는 어려움
   - 개별 엔드포인트를 함수로 변환 필요 (복잡함)

### 또는 vercel.json에 포함 (비권장)

```json
{
  "env": {
    "VITE_API_BASE_URL": "https://your-api-server.com"
  }
}
```

## 빌드 설정

### package.json 확인

`package.json`에 빌드 스크립트가 있는지 확인:

```json
{
  "scripts": {
    "build": "vite build",
    "dev": "vite"
  }
}
```

## 문제 해결

### 1. 이미지 파일 누락 오류

**에러 메시지:**
```
Could not load /vercel/path0/src/assets/icons/Intellivix_logo.png
```

**해결 방법:**

#### 방법 1: 파일이 Git에 커밋되었는지 확인

```bash
# Git에 파일이 포함되어 있는지 확인
git ls-files src/assets/icons/Intellivix_logo.png

# 파일이 없다면 추가
git add src/assets/icons/Intellivix_logo.png
git commit -m "Add Intellivix logo image"
git push
```

#### 방법 2: .gitignore 확인

`.gitignore` 파일에 이미지 파일이 제외되어 있지 않은지 확인:

```gitignore
# assets 폴더는 커밋해야 함
# src/assets/icons/  # 이 줄이 있으면 제거
```

#### 방법 3: 파일 경로 확인

파일이 실제로 존재하는지 확인:

```bash
# Windows
dir src\assets\icons\Intellivix_logo.png

# Linux/Mac
ls -la src/assets/icons/Intellivix_logo.png
```

#### 방법 4: 대체 이미지 사용

파일을 찾을 수 없는 경우, Base64 인코딩된 이미지나 외부 URL 사용:

```vue
<!-- HeaderBar.vue -->
<script setup>
// 방법 1: 외부 URL 사용
const logoUrl = ref('https://your-cdn.com/logo.png');

// 방법 2: Base64 인코딩
const logoUrl = ref('data:image/png;base64,iVBORw0KGgoAAAANS...');

// 방법 3: 조건부 로딩
import logoUrlDefault from '@/assets/icons/Intellivix_logo.png';
const logoUrl = ref(logoUrlDefault);
</script>
```

### 2. 빌드 명령어 오류

**해결 방법:**

`vercel.json`에서 빌드 명령어 명시:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist"
}
```

### 3. 라우팅 오류 (404)

**해결 방법:**

`vercel.json`에 rewrites 규칙 추가:

```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

### 4. 환경 변수 미적용

**해결 방법:**

1. Vercel 대시보드에서 환경 변수 재설정
2. 프로젝트 재배포
3. 환경 변수 이름이 `VITE_`로 시작하는지 확인

## 배포 워크플로우

### 자동 배포

1. GitHub에 코드 푸시
2. Vercel이 자동으로 빌드 및 배포
3. 배포 완료 후 URL 확인

### 수동 배포

```bash
# Vercel CLI 설치
npm i -g vercel

# 로그인
vercel login

# 배포
vercel

# 프로덕션 배포
vercel --prod
```

## 커스텀 도메인 설정

1. Vercel 대시보드 → 프로젝트 → Settings → Domains
2. 도메인 추가
3. DNS 설정 안내에 따라 DNS 레코드 추가

## 성능 최적화

### 1. 이미지 최적화

- WebP 형식 사용
- 적절한 크기로 리사이즈
- CDN 사용 (Vercel 자동 제공)

### 2. 빌드 최적화

`vite.config.js`에서 최적화 설정:

```javascript
export default {
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router'],
        },
      },
    },
  },
}
```

## 모니터링

Vercel 대시보드에서 다음을 확인할 수 있습니다:

- 배포 히스토리
- 빌드 로그
- 성능 메트릭
- 에러 로그

## API 서버 배포

**중요**: 현재 프로젝트의 FastAPI 백엔드는 Vercel에 직접 배포할 수 없습니다.

API 서버는 별도로 배포해야 합니다. 자세한 내용은:
- [Vercel + API 서버 배포 전략](./VERCEL_API_DEPLOYMENT.md)

### 빠른 해결책

1. **프론트엔드**: Vercel에 배포 (현재 가이드)
2. **API 서버**: Railway, Render 등 별도 플랫폼에 배포
3. **연결**: Vercel 환경 변수에 API 서버 URL 설정

## 참고 자료

- [Vercel 공식 문서](https://vercel.com/docs)
- [Vite 배포 가이드](https://vitejs.dev/guide/static-deploy.html)
- [Vue.js 배포 가이드](https://vuejs.org/guide/scaling-up/deployment.html)
- [Vercel + API 서버 배포 전략](./VERCEL_API_DEPLOYMENT.md)

