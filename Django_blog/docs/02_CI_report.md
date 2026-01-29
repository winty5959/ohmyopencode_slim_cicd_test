# 02_CI_report.md

본 문서는 `instruct.md`의 **2단계(GitHub Actions 워크플로우 작성)** 에서 수행한 작업 내역을 정리한 리포트입니다.

## 1. 목표(요구사항)

`instruct.md` 2단계 요구사항:

- `.github/workflows/django-ci-cd.yml` 생성
- **CI Job**: (원문은 master push 트리거) Python 환경 설정 → 의존성 설치 → DB 마이그레이션 테스트 → 유닛 테스트 실행
- **CD Job**: CI 성공 시 Azure App Service에 자동 배포

## 2. 현재 프로젝트 디렉토리 구조(경로 반영)

- GitHub 레포 루트(사용자 결정): `CICD/`
- Django 프로젝트 루트(`manage.py` 위치): `CICD/Django_blog/`
- GitHub Actions 워크플로 위치: `CICD/.github/workflows/django-ci-cd.yml`

## 3. 구현한 GitHub Actions 워크플로

### 3.1 생성/수정 파일

- `CICD/.github/workflows/django-ci-cd.yml`

### 3.2 트리거

- `push` to `main`
- `workflow_dispatch` (수동 실행)

> 참고: `instruct.md` 원문은 `master` 기준이었으나, 사용자 선택으로 `main` 트리거로 설정했습니다.

### 3.3 공통 환경값

- `PYTHON_VERSION: "3.11"`
- `APP_DIR: "Django_blog"`  
  - 모든 `run` 커맨드의 `working-directory`로 사용 (경로 의존성 관리)

## 4. CI Job 상세

Job 이름: `ci`

### 4.1 실행 환경

- Runner: `ubuntu-latest`
- 서비스 컨테이너: PostgreSQL (`postgres:16-alpine`)
  - healthcheck: `pg_isready`
  - 포트: `5432:5432`

### 4.2 수행 Steps

1) `actions/checkout@v4`
2) `actions/setup-python@v5`
   - `python-version: 3.11`
   - `pip cache` 활성화(`cache-dependency-path` 사용)
3) `pip install -r requirements.txt`
4) 마이그레이션 + 테스트
   - `python manage.py migrate`
   - `pytest`
   - 테스트용 환경변수:
     - `DEBUG=1`
     - `DATABASE_URL=postgres://bloguser:blogpass@localhost:5432/blogdb`

### 4.3 배포용 패키징(artifact)

- `zip -r app.zip .` 로 소스 패키징
- 제외 대상(예: 민감정보/불필요 산출물)
  - `.env`
  - `e2e_artifacts/*`
  - `staticfiles/*`
  - `__pycache__`, `*.pyc`, `.pytest_cache`, `.git*`

- 업로드: `actions/upload-artifact@v4`
  - artifact name: `cicd-app`
  - path: `Django_blog/app.zip`

## 5. CD(Job) 상세

Job 이름: `deploy`

### 5.1 구조

- `needs: ci` 로 CI 성공 이후에만 실행되도록 구성
- Azure 인증 방식: **OIDC(Service Principal)**
  - `permissions: id-token: write` 포함

### 5.2 현재 상태(의도된 스킵)

사용자 상황: “Azure App Service 정보/시크릿이 아직 없음”

따라서 아래 secrets가 모두 채워져 있을 때만 `deploy`가 실행되도록 `if:` 조건을 추가하여,
Azure 준비 전에는 자동으로 스킵되게 구성했습니다.

- `AZURE_WEBAPP_NAME`
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

### 5.3 Deploy Steps (Azure 준비 완료 시)

1) `actions/download-artifact@v4` 로 `app.zip` 다운로드
2) `azure/login@v2` (OIDC)
3) `azure/webapps-deploy@v2`
   - `app-name: ${{ secrets.AZURE_WEBAPP_NAME }}`
   - `package: app.zip`

## 6. 확인/테스트 방법(레포 푸시 후)

1) `main` 브랜치로 push
2) GitHub Actions에서 `django-ci-cd` 워크플로 실행 확인
3) CI job에서
   - Postgres 서비스 정상 기동
   - `migrate` 성공
   - `pytest` 성공
   - artifact 업로드 확인
4) Azure secrets 설정 전에는 `deploy` job이 스킵되는지 확인

---

## 부록: 관련 경로

- 워크플로 파일: `CICD/.github/workflows/django-ci-cd.yml`
- 요구사항 문서: `CICD/Django_blog/instruct.md`
