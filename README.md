# SPass CSV Converter

Samsung Pass에서 내보낸 `spass_export_data.spass` 파일을 CSV로 변환하는 맥/윈도우용 변환기입니다.

## 중요한 안내

`.spass` 형식은 공개된 표준 포맷이 아닙니다. 이 프로그램은 파일 안의 데이터가 JSON, CSV, XML, SQLite, ZIP 압축 파일처럼 읽을 수 있는 구조일 때 CSV로 변환합니다. 파일이 Samsung 전용 방식으로 암호화되어 있으면 비밀번호를 우회하거나 복호화하지 않으며, 변환할 수 없다는 메시지를 보여줍니다.

## 사용 방법

처음 한 번만 아래 명령으로 프로그램을 설치합니다.

```bash
python3 -m pip install -e .
```

### 화면 앱으로 실행

```bash
python3 -m spass_csv_converter --gui
```

화면에서 `spass_export_data.spass` 파일을 고르고 `Convert to CSV`를 누르면 같은 위치에 CSV 파일을 저장할 수 있습니다.

### 명령어로 실행

```bash
python3 -m spass_csv_converter spass_export_data.spass output.csv
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

- JSON 또는 plist 안의 계정 목록
- CSV 형태의 내보내기
- XML 안의 반복 레코드
- SQLite 데이터베이스
- 위 파일들이 들어 있는 ZIP 기반 `.spass` 파일

## 개발 확인

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test*.py' -v
```
