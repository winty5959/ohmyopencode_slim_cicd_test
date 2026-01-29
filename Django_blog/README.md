# Django Blog (CI/CD 실습)

상위 문서(레포 루트 기준 CI/CD + Azure 로그인/배포 가이드): `../README.md`

## 로컬 실행 (Docker: 앱+DB)

1) 환경변수 파일 준비

```bash
cp .env.example .env
```

2) 실행

```bash
docker compose up --build
```

3) 접속

http://localhost:8000

## 테스트

로컬에서 파이썬 환경을 준비한 뒤:

```bash
pip install -r requirements.txt
pytest
```
