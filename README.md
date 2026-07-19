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

<p align="center">
  <img src="https://github.com/user-attachments/assets/0e82014b-6a30-456e-b2e0-ca900637d38e" width="60%" alt="spass_site" />
</p>

<details>
<summary><h2>웹 버전 동작 방식에 대해서..</h2></summary>
<div markdown="1">

웹 버전(https://dubu-alt.github.io/spass-to-csv/)은 서버가 없는 정적 페이지입니다.
페이지를 여는 순간 변환 코드(JavaScript) 전체가 브라우저에 다운로드되고,
그 이후의 모든 동작은 사용자 컴퓨터 안에서만 실행됩니다.

**변환 과정**

1. 선택한 `.spass` 파일을 브라우저 메모리로 읽습니다 (업로드 아님)
2. 입력한 비밀번호로 PBKDF2-HMAC-SHA256(70,000회) 키를 만들어
   AES-256-CBC 복호화합니다 — 브라우저 내장 WebCrypto API 사용
3. 복호화된 Samsung Pass 테이블을 파싱해 선택한 형식(CSV/JSON)으로 변환합니다
4. 결과를 브라우저 메모리(Blob)에서 곧바로 내 컴퓨터에 다운로드합니다

파일과 비밀번호, 변환 결과는 어떤 서버에도 전송되지 않으며
브라우저에 저장(localStorage 등)되지도 않습니다.
Python 버전과 동일한 변환 로직이며, 동일 입력에 대해 동일한 출력을 생성합니다.

**안전장치**

- 외부 라이브러리/CDN 없이 HTML 파일 하나로 완결 — 외부 요청이 발생할 코드가 없음
- CSP(Content-Security-Policy) 적용 — 만에 하나 악성 코드가 끼어들어도
  브라우저가 모든 외부 전송(fetch, 폼 제출 등)을 차단
- HTTPS로만 제공되어 전송 중 코드 변조 불가

**직접 확인하는 방법**

- 변환 전에 개발자 도구(F12) → Network 탭을 열어두면 변환 중 네트워크 요청이
  하나도 발생하지 않는 것을 볼 수 있습니다
- 페이지를 연 뒤 인터넷을 끊고 변환해도 정상 동작합니다
- 저장소의 `docs/index.html`이 페이지의 전부이므로 코드 전체를 직접 검토할 수 있습니다

변환된 CSV/JSON에는 평문 비밀번호가 들어 있습니다.
다른 비밀번호 관리자로 가져오기가 끝나면 반드시 파일을 안전하게 삭제하세요.
</div>
</details>

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
<table>
  <tr>
    <td width="50%">
      <img src="https://github.com/user-attachments/assets/3af4c31c-8b4e-4976-a464-cd078e067783" width="100%" alt="Windows" />
    </td>
    <td width="50%">
      <img src="https://github.com/user-attachments/assets/eb18a964-f9ef-4d08-8d53-679f54f47bf7" width="100%" alt="mac_os" />
    </td>
  </tr>
    <!-- 설명 자막 행 (텍스트 중앙 정렬) -->
  <tr align="center">
    <td>Windows 버전 화면</td>
    <td>macOS 버전 화면</td>
</table>


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

## 처음 실행할 때 보안 경고가 뜨는 경우

이 앱은 개인 개발자가 무료로 배포하는 오픈소스라 유료 코드 서명 인증서가 없습니다.
그래서 처음 실행할 때 운영체제가 "확인되지 않은 앱"이라는 경고를 띄우는데,
악성 프로그램이라는 뜻이 아니라 서명이 없다는 뜻입니다. 아래 방법으로 한 번만
통과하면 다음부터는 경고 없이 실행됩니다.

### 맥 (macOS)

"확인되지 않은 개발자" 또는 "손상되었기 때문에 열 수 없습니다" 경고가 뜹니다.

1. 앱 아이콘을 **우클릭(Control+클릭) → 열기**를 선택합니다
2. 경고 창에 나타나는 **열기** 버튼을 누릅니다 (더블클릭과 달리 열기 버튼이 생깁니다)

macOS Sequoia(15) 이후 버전에서 우클릭 → 열기가 통하지 않으면:

1. 앱을 더블클릭해 경고를 한 번 띄운 뒤
2. **시스템 설정 → 개인정보 보호 및 보안**으로 이동해 아래쪽의
   **"그래도 열기"** 버튼을 누릅니다

그래도 안 되면 터미널에서 격리 속성을 제거합니다 (압축 푼 위치에 맞게 경로 수정):

​```bash
xattr -cr ~/Downloads/"SPass CSV Converter.app"
​```

### 윈도우 (Windows)

"Windows의 PC 보호" (SmartScreen) 파란 경고 창이 뜹니다.

1. 경고 창에서 **추가 정보**를 클릭합니다
2. 나타나는 **실행** 버튼을 누릅니다

백신 프로그램이 다운로드를 차단하는 경우 해당 파일을 예외(허용) 목록에
추가하면 됩니다. PyInstaller로 만든 서명 없는 실행 파일은 오탐이 흔합니다.
