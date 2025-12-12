# Docker 설치 가이드

이 가이드는 다양한 운영 체제에서 Docker를 설치하는 방법을 설명합니다.

## 목차

1. [Windows 설치](#windows-설치)
2. [macOS 설치](#macos-설치)
3. [Linux 설치](#linux-설치)
4. [설치 확인](#설치-확인)
5. [문제 해결](#문제-해결)

## Windows 설치

### 방법 1: Docker Desktop (권장)

Docker Desktop은 Windows에서 Docker를 사용하는 가장 쉬운 방법입니다.

#### 요구사항
- Windows 10 64-bit: Pro, Enterprise, 또는 Education (Build 19041 이상)
- Windows 11 64-bit: Home 또는 Pro (Build 22000 이상)
- WSL 2 기능 활성화 필요
- 가상화 기능 활성화 필요 (BIOS에서)

#### 설치 단계

1. **WSL 2 설치 확인**
   ```powershell
   # PowerShell을 관리자 권한으로 실행
   wsl --install
   ```
   
   또는 수동으로:
   - 제어판 → 프로그램 → Windows 기능 켜기/끄기
   - "Linux용 Windows 하위 시스템" 체크
   - "가상 머신 플랫폼" 체크
   - 재부팅

2. **Docker Desktop 다운로드**
   - [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) 다운로드
   - 또는 직접 다운로드: https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe

3. **설치 실행**
   - 다운로드한 `Docker Desktop Installer.exe` 실행
   - 설치 옵션에서 "Use WSL 2 instead of Hyper-V" 선택 (권장)
   - 설치 완료 후 재부팅

4. **Docker Desktop 실행**
   - 시작 메뉴에서 "Docker Desktop" 실행
   - 초기 설정 완료 대기 (몇 분 소요)
   - 시스템 트레이에 Docker 아이콘이 표시되면 준비 완료

#### WSL 2 백엔드 설정

Docker Desktop이 WSL 2를 사용하도록 설정:

1. Docker Desktop 실행
2. Settings → General → "Use the WSL 2 based engine" 체크
3. Settings → Resources → WSL Integration
4. 사용할 Linux 배포판 선택 (예: Ubuntu)
5. Apply & Restart

### 방법 2: Docker Engine (Linux 컨테이너)

WSL 2 없이 직접 설치하려면:

```powershell
# Chocolatey 사용
choco install docker-desktop

# 또는 Scoop 사용
scoop install docker
```

## macOS 설치

### 방법 1: Docker Desktop (권장)

#### 요구사항
- macOS 10.15 (Catalina) 이상
- Apple Silicon (M1/M2) 또는 Intel 프로세서 지원

#### 설치 단계

1. **Docker Desktop 다운로드**
   - [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) 다운로드
   - Apple Silicon: https://desktop.docker.com/mac/main/arm64/Docker.dmg
   - Intel: https://desktop.docker.com/mac/main/amd64/Docker.dmg

2. **설치 실행**
   - 다운로드한 `.dmg` 파일 열기
   - Docker 아이콘을 Applications 폴더로 드래그
   - Applications에서 Docker 실행
   - 시스템 설정에서 보안 허용 (필요시)

3. **초기 설정**
   - Docker Desktop 실행
   - 초기 설정 완료 대기
   - 메뉴 바에 Docker 아이콘이 표시되면 준비 완료

### 방법 2: Homebrew 사용

```bash
# Homebrew로 설치
brew install --cask docker

# 또는 Docker Desktop 직접 설치
brew install docker
```

## Linux 설치

### Ubuntu / Debian

#### Docker Engine 설치

```bash
# 1. 이전 버전 제거 (있는 경우)
sudo apt-get remove docker docker-engine docker.io containerd runc

# 2. 필수 패키지 설치
sudo apt-get update
sudo apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 3. Docker의 공식 GPG 키 추가
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 4. Docker 저장소 추가
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. Docker Engine 설치
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 6. Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker

# 7. 사용자를 docker 그룹에 추가 (sudo 없이 사용)
sudo usermod -aG docker $USER

# 8. 로그아웃 후 다시 로그인 (또는 다음 명령어 실행)
newgrp docker
```

#### Docker Compose 설치

Docker Desktop을 사용하지 않는 경우:

```bash
# Docker Compose V2 (권장, Docker Engine에 포함됨)
# 위의 설치 과정에서 이미 설치됨

# 또는 수동 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### CentOS / RHEL / Fedora

```bash
# 1. 필수 패키지 설치
sudo yum install -y yum-utils

# 2. Docker 저장소 추가
sudo yum-config-manager \
    --add-repo \
    https://download.docker.com/linux/centos/docker-ce.repo

# 3. Docker Engine 설치
sudo yum install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 4. Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker

# 5. 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER
newgrp docker
```

### Arch Linux

```bash
# pacman으로 설치
sudo pacman -S docker docker-compose

# Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker

# 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER
newgrp docker
```

## 설치 확인

설치가 완료되었는지 확인:

```bash
# Docker 버전 확인
docker --version

# Docker Compose 버전 확인
docker compose version
# 또는 (구버전)
docker-compose --version

# Docker 실행 테스트
docker run hello-world
```

성공적으로 실행되면 다음과 같은 메시지가 표시됩니다:

```
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

## 문제 해결

### Windows

#### WSL 2 관련 문제

```powershell
# WSL 2 버전 확인
wsl --list --verbose

# WSL 2로 업그레이드
wsl --set-version Ubuntu 2

# 기본 버전 설정
wsl --set-default-version 2
```

#### 가상화 비활성화 문제

1. BIOS/UEFI 설정 진입
2. 가상화 기능 활성화:
   - Intel: "Intel Virtualization Technology (VT-x)"
   - AMD: "AMD-V" 또는 "SVM Mode"
3. 저장 후 재부팅

#### Docker Desktop이 시작되지 않음

- Windows 기능에서 "Hyper-V" 활성화 확인
- WSL 2 업데이트 확인
- Docker Desktop 재설치

### macOS

#### Apple Silicon (M1/M2) 호환성

일부 이미지는 아직 ARM64를 지원하지 않을 수 있습니다. 
다음과 같이 플랫폼을 지정:

```bash
docker build --platform linux/amd64 -t my-image .
```

#### 권한 문제

```bash
# Docker Desktop 재시작
# 또는
sudo chmod 666 /var/run/docker.sock
```

### Linux

#### 권한 문제 (Permission denied)

```bash
# 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# 로그아웃 후 다시 로그인
# 또는
newgrp docker

# 확인
groups
```

#### Docker 서비스가 시작되지 않음

```bash
# 서비스 상태 확인
sudo systemctl status docker

# 서비스 시작
sudo systemctl start docker

# 로그 확인
sudo journalctl -u docker
```

#### 방화벽 문제

```bash
# 방화벽 규칙 확인 (UFW)
sudo ufw status

# Docker 네트워크 허용
sudo ufw allow from 172.17.0.0/16
```

## 추가 리소스

- [Docker 공식 문서](https://docs.docker.com/)
- [Docker Desktop 문서](https://docs.docker.com/desktop/)
- [Docker Compose 문서](https://docs.docker.com/compose/)

## 다음 단계

Docker 설치가 완료되면 다음 가이드를 참고하세요:

- [Docker 배포 가이드](./DOCKER_DEPLOYMENT.md) - API 서버 배포 방법

