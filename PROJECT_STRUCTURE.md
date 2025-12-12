# 프로젝트 구조

VSS (Video Summarization System) 프로젝트의 폴더 구조 및 파일 설명입니다.

## 📁 전체 구조

```
Vue-test/
├── .github/                    # GitHub Actions 워크플로우
│   └── workflows/
│       └── deploy.yml          # GitHub Pages 자동 배포 설정
│
├── docs/                       # 📚 문서 및 가이드
│   ├── README.md               # 문서 목차
│   ├── DEPLOYMENT_GUIDE.md     # 프론트엔드 배포 가이드
│   ├── INTELLIVIX_SMTP_SETUP.md # Intellivix SMTP 설정
│   └── SMTP_SETUP_GUIDE.md     # 일반 SMTP 설정
│
├── scripts/                    # 🔧 유틸리티 스크립트
│   └── setup_smtp.py           # SMTP 설정 도우미
│
├── vss-summarize.py            # NVIDIA VSS 요약 스크립트 (별도)
│
├── sql/                        # 💾 데이터베이스 스크립트
│   ├── create_vss_user_table.sql
│   ├── create_vss_videos_table.sql
│   └── create_vss_summaries_table.sql
│
├── src/                        # 소스 코드
│   ├── api/                    # 🔌 백엔드 API 서버
│   │   ├── vss-api.py          # FastAPI 메인 애플리케이션
│   │   ├── requirements.txt    # Python 의존성
│   │   ├── clips/              # 생성된 클립 저장 (런타임 생성)
│   │   ├── videos/             # 업로드된 동영상 저장 (런타임 생성)
│   │   └── tmp/                # 임시 파일 (런타임 생성)
│   │
│   ├── assets/                 # 정적 리소스
│   │   ├── icons/              # 아이콘 이미지
│   │   │   ├── Intellivix_logo.png
│   │   │   ├── report.svg
│   │   │   ├── search.svg
│   │   │   ├── setting.png
│   │   │   └── summary.svg
│   │   ├── sample/             # 샘플 파일
│   │   │   └── sample.mp4     # 샘플 동영상
│   │   ├── tailwind.css        # Tailwind CSS
│   │   └── vue.svg
│   │
│   ├── components/             # Vue 컴포넌트
│   │   ├── HeaderBar.vue       # 헤더 바
│   │   ├── Pagination.vue      # 페이지네이션
│   │   └── SidebarNav.vue      # 사이드바 네비게이션
│   │
│   ├── config/                 # 설정 파일
│   │   └── api.js              # API 엔드포인트 설정
│   │
│   ├── pages/                  # 페이지 컴포넌트
│   │   ├── Login.vue           # 로그인 페이지
│   │   ├── Register.vue        # 회원가입 페이지
│   │   ├── ResetPassword.vue   # 비밀번호 재설정
│   │   ├── Search.vue          # 동영상 검색
│   │   ├── Setting.vue         # 설정 페이지
│   │   ├── Summarize.vue       # 동영상 요약
│   │   └── Report.vue          # 보고서 페이지
│   │
│   ├── router/                 # 라우터 설정
│   │   └── index.js            # Vue Router 설정
│   │
│   ├── services/               # 서비스 레이어
│   │   └── api.js              # API 호출 서비스
│   │
│   ├── stores/                 # Pinia 상태 관리
│   │   ├── settingStore.js     # 설정 스토어
│   │   └── summaryVideoStore.js # 요약 동영상 스토어
│   │
│   ├── App.vue                 # 루트 컴포넌트
│   └── main.js                 # 애플리케이션 진입점
│
├── public/                     # 정적 공용 파일
│   ├── favicon.ico
│   └── vite.svg
│
├── dist/                       # 빌드 결과물 (생성됨)
│
├── node_modules/               # Node.js 의존성 (생성됨)
│
├── .gitignore                  # Git 제외 파일 목록
├── package.json                # Node.js 프로젝트 설정
├── package-lock.json           # 의존성 잠금 파일
├── vite.config.js              # Vite 빌드 설정
├── tailwind.config.js          # Tailwind CSS 설정
├── postcss.config.cjs          # PostCSS 설정
├── README.md                   # 프로젝트 메인 README
└── PROJECT_STRUCTURE.md        # 이 파일
```

## 📂 주요 폴더 설명

### `docs/`
모든 문서 및 가이드 파일이 포함된 폴더입니다.
- 배포 가이드
- 설정 가이드
- 문제 해결 가이드

### `scripts/`
유틸리티 스크립트 폴더입니다.
- `setup_smtp.py`: SMTP 설정을 위한 도우미 스크립트

### `sql/`
데이터베이스 관련 SQL 스크립트입니다.
- 테이블 생성 스크립트
- 마이그레이션 스크립트

### `src/api/`
백엔드 API 서버 폴더입니다.
- FastAPI 애플리케이션
- Python 의존성 파일
- 런타임 생성 폴더 (`clips/`, `videos/`, `tmp/`)

### `src/assets/`
정적 리소스 폴더입니다.
- 아이콘 이미지
- 샘플 파일

### `src/components/`
재사용 가능한 Vue 컴포넌트입니다.

### `src/pages/`
페이지 컴포넌트입니다.

### `src/stores/`
Pinia 상태 관리 스토어입니다.

## 🚫 Git에 포함되지 않는 파일/폴더

다음 항목들은 `.gitignore`에 의해 제외됩니다:

- `node_modules/` - Node.js 의존성
- `dist/` - 빌드 결과물
- `__pycache__/` - Python 캐시
- `*.pyc`, `*.pyo` - Python 컴파일 파일
- `.env` - 환경 변수 파일
- `src/api/clips/` - 런타임 생성 클립
- `src/api/videos/` - 런타임 생성 동영상
- `src/api/tmp/` - 임시 파일

## 🔧 설정 파일

### 프론트엔드
- `package.json` - Node.js 프로젝트 설정 및 의존성
- `vite.config.js` - Vite 빌드 도구 설정
- `tailwind.config.js` - Tailwind CSS 설정

### 백엔드
- `src/api/requirements.txt` - Python 패키지 의존성

## 📝 파일 명명 규칙

- **컴포넌트**: PascalCase (예: `HeaderBar.vue`)
- **페이지**: PascalCase (예: `Login.vue`)
- **스토어**: camelCase (예: `settingStore.js`)
- **설정 파일**: kebab-case 또는 camelCase (예: `api.js`, `vite.config.js`)

## 🚀 배포 관련

### GitHub Pages 배포
- 빌드 결과물: `dist/` 폴더
- 자동 배포: `.github/workflows/deploy.yml`

## 📚 관련 문서

- 배포 가이드: `docs/DEPLOYMENT_GUIDE.md`
- 프로젝트 README: `README.md`

