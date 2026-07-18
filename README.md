# SPass CSV Converter

Samsung Pass에서 내보낸 `spass_export_data.spass` 파일을 CSV 또는 Bitwarden JSON으로 변환하는 맥/윈도우용 변환기입니다.

## 중요한 안내

`.spass` 형식은 공개 표준은 아니지만, 알려진 Samsung Pass 내보내기 구조를 지원합니다. 프로그램은 내보내기 비밀번호로 파일을 로컬에서 복호화한 뒤 Chrome/Edge CSV, Proton Pass CSV, Bitwarden JSON 또는 원본 필드 CSV로 저장합니다.

비밀번호 우회 기능은 없으며, 출력 파일에는 평문 비밀번호가 들어갑니다. 가져오기가 끝난 뒤 CSV/JSON 파일은 안전하게 삭제하세요.

복호화/파싱 로직은 MIT 라이선스의 [misterpfister8/spasstocsv](https://github.com/misterpfister8/spasstocsv)를 참고해 보완했습니다. 자세한 출처는 `THIRD_PARTY_NOTICES.md`에 정리했습니다.

## 사용 방법

### 1. 설치 없이 웹에서 사용 (가장 쉬움)

브라우저에서 [https://dubu-alt.github.io/spass-to-csv/](https://dubu-alt.github.io/spass-to-csv/) 를 열고 `.spass` 파일을 끌어다 놓은 뒤 비밀번호를 입력하면 끝입니다. 복호화와 변환은 전부 브라우저 안에서만 실행되며 파일과 비밀번호는 어떤 서버에도 전송되지 않습니다. 인터넷을 끊고 사용해도 됩니다.

> 저장소 관리자: GitHub 저장소 Settings → Pages → Source를 **GitHub Actions**로 설정하면 `docs/index.html`이 자동 배포됩니다.

### 2. 맥/윈도우 앱 다운로드

[Releases](https://github.com/dubu-alt/spass-to-csv/releases)에서 맥용 zip 또는 윈도우용 `.exe`를 받아 더블클릭하면 됩니다. `v1.0.0`처럼 `v`로 시작하는 태그를 푸시하면 GitHub Actions가 자동으로 빌드해서 Releases에 올립니다.

```bash
git tag v1.0.0 && git push origin v1.0.0
```

### 3. Python으로 직접 실행

처음 한 번만 아래 명령으로 프로그램을 설치합니다.

```bash
python3 -m pip install -e .
```

### 화면 앱으로 실행

```bash
python3 -m spass_csv_converter --gui
```

화면에서 `spass_export_data.spass` 파일을 고르고 Samsung Pass에서 설정했던 내보내기 비밀번호를 입력한 뒤 형식을 선택해 변환합니다. 비밀번호 표시 토글, 변환 후 저장 폴더 열기 버튼을 지원하며, `pip install "spass-csv-converter[gui]"`로 `tkinterdnd2`를 설치하면 창에 파일을 끌어다 놓을 수도 있습니다.
<p align="center">
  <img src="https://github.com/user-attachments/assets/3cdbee2d-2dec-4317-9341-eec93b2e86a7" width="600" alt="SPass CSV Converter GUI">
</p>

### 명령어로 실행

```bash
python3 -m spass_csv_converter spass_export_data.spass output.csv --format chrome
```

비밀번호는 화면에 보이지 않게 입력됩니다. 자동화가 필요하면 표준 입력으로 넘길 수 있습니다.

```bash
printf '내보내기-비밀번호\n' | python3 -m spass_csv_converter \
  --password-stdin \
  spass_export_data.spass \
  output.csv \
  --format proton
```

## 맥 앱 만들기

맥에서 아래 명령을 실행합니다.

```bash
chmod +x scripts/build_macos.sh
./scripts/build_macos.sh
```

완료되면 `dist/` 폴더에 실행 파일이 생깁니다.

## 윈도우 앱 만들기

윈도우 PowerShell에서 아래 명령을 실행합니다. 윈도우용 `.exe`는 윈도우에서 빌드해야 합니다.

```powershell
.\scripts\build_windows.ps1
```

완료되면 `dist\` 폴더에 `.exe` 파일이 생깁니다.

## GitHub에서 맥/윈도우 파일 자동 만들기

이 저장소를 GitHub에 올리면 `.github/workflows/build.yml` 워크플로가 맥과 윈도우용 실행 파일을 각각 빌드하고 artifact로 올립니다.

## 지원하는 입력 구조

- Samsung Pass 암호화 `.spass`: `Base64(salt + IV + AES-256-CBC 암호문)`
- PBKDF2-HMAC-SHA256 70,000회 키 파생
- 복호화 후 semicolon 기반 Samsung Pass 테이블
- 보조 fallback: JSON, plist, CSV, XML, SQLite, ZIP 기반 읽기 가능한 파일

## 출력 형식

- `chrome`: Chrome/Edge/1Password용 `name,url,username,password,note`
- `proton`: Proton Pass Generic CSV `name,url,username,password,note,totp`
- `raw`: Samsung Pass password 테이블 필드 그대로 CSV
- `bitwarden-json`: 로그인, 보안 노트, 카드, 주소를 Bitwarden JSON으로 저장

## 개발 확인

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test*.py' -v
```
