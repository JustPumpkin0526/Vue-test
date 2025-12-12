# @intellivix.ai 이메일 SMTP 설정 가이드

## 설정 방법

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 아래 내용을 추가하세요.

## 옵션 1: Google Workspace 사용 (권장)

@intellivix.ai 도메인이 Google Workspace를 사용하는 경우:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@intellivix.ai
SMTP_PASSWORD=your-app-password-here
SMTP_FROM_EMAIL=noreply@intellivix.ai
```

### Google Workspace 앱 비밀번호 생성 방법:

1. Google Admin Console 접속: https://admin.google.com/
2. 해당 사용자 계정으로 로그인
3. Google 계정 설정: https://myaccount.google.com/
4. **보안** → **2단계 인증** 활성화
5. **앱 비밀번호** 생성
   - 앱: 메일
   - 기기: 기타(맞춤 이름) → "VSS" 입력
6. 생성된 16자리 비밀번호를 `.env` 파일의 `SMTP_PASSWORD`에 입력

## 옵션 2: Microsoft 365 사용

@intellivix.ai 도메인이 Microsoft 365를 사용하는 경우:

```env
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USER=noreply@intellivix.ai
SMTP_PASSWORD=your-password-here
SMTP_FROM_EMAIL=noreply@intellivix.ai
```

### Microsoft 365 설정:

1. Microsoft 365 Admin Center 접속
2. 해당 사용자 계정의 비밀번호 사용
3. 또는 앱 비밀번호 생성 (2단계 인증 활성화 시)

## 옵션 3: 자체 메일 서버 사용

자체 메일 서버를 운영하는 경우:

```env
SMTP_SERVER=mail.intellivix.ai
SMTP_PORT=587
SMTP_USER=noreply@intellivix.ai
SMTP_PASSWORD=your-password-here
SMTP_FROM_EMAIL=noreply@intellivix.ai
```

## 실제 이메일 주소 예시

실제 사용할 이메일 주소로 변경하세요:
- `noreply@intellivix.ai` (자동 발신용)
- `support@intellivix.ai` (고객 지원용)
- `admin@intellivix.ai` (관리자용)
- 또는 다른 이메일 주소

## 빠른 설정

1. 프로젝트 루트에 `.env` 파일 생성
2. 위의 설정 중 하나를 복사하여 붙여넣기
3. `SMTP_USER`와 `SMTP_PASSWORD`를 실제 값으로 변경
4. FastAPI 서버 재시작

## 테스트

설정 후 다음 명령어로 연결을 테스트할 수 있습니다:

```bash
python setup_smtp.py test
```

## 문제 해결

### 인증 실패 시:
- Google Workspace: 앱 비밀번호 사용 확인
- Microsoft 365: 2단계 인증 시 앱 비밀번호 필요
- 비밀번호에 특수문자가 있으면 따옴표로 감싸기

### 연결 실패 시:
- 방화벽에서 포트 587 또는 465 허용 확인
- SMTP 서버 주소 확인
- 네트워크 연결 확인

