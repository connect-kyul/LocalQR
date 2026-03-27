# LocalQR
로컬 네트워크에서 내부망을 이용하여 파일을 전달하는 서비스입니다.

# 맥/리눅스
- 맥/리눅스 환경에서는 어떻게 할까요 ?
```
# 1. 라이브러리 설치
python3 -m pip install qrcode

# 2. 프로그램 실행 (파일 경로는 본인에 맞게 수정)
python3 qrbeam.py "공유할파일경로.txt"
```
- 라이브러리 설치에서 막힐 경우, `--break-system-packages`를 뒤에 포함시켜주세요. (빠르게 사용하고 싶을 때)
- 만약 `externally-managed-environment` 에러가 발생한다면, 가상 환경(venv) 사용을 강력히 권장합니다. `--break-system-packages` 플래그는 시스템 라이브러리를 오염시켜 OS 동작에 문제를 일으킬 수 있으므로 주의가 필요합니다.

# 윈도우
- 윈도우 환경에서는 어떻게 할까요 ?
```
# 1. 라이브러리 설치
python -m pip install qrcode

# 2. 프로그램 실행 (파일 경로는 본인에 맞게 수정)
python qrbeam.py "공유할파일경로.txt"
```
