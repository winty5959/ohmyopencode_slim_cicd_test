## 실습 시나리오 개요

간단한 Django 블로그 애플리케이션을 개발하고, GitHub에 코드를 푸시할 때마다 자동으로 테스트를 실행한 후 Azure App Service에 배포하는 CI/CD 파이프라인을 구축합니다.

## 단계별 실습 가이드

## 1단계: Django 프로젝트 준비

- 간단한 Django 블로그 앱 생성 (게시글 CRUD 기능. 일반적이고 모던한 디자인)
- PostgreSQL 데이터베이스 설정 (일단은 로컬 docker로 구성하되, 향후에는 Azure PostgreSQL Flexible Server 사용. 참고로 현재 Docker desktop은 켜져 있음.)
- `requirements.txt` 작성 (Django, psycopg2, gunicorn 등)
- 유닛 테스트 작성 (최소 5개 이상의 테스트 케이스)
- `pytest` 또는 Django 기본 테스트 프레임워크 사용

## 2단계: GitHub Actions 워크플로우 작성

`.github/workflows/django-ci-cd.yml` 파일을 생성하여 다음 작업을 자동화합니다:

- **CI (Continuous Integration) Job**: master 브랜치에 push될 때 트리거되어 Python 환경 설정, 의존성 설치, 데이터베이스 마이그레이션 테스트, 유닛 테스트 실행
- **CD (Continuous Deployment) Job**: CI가 성공하면 Azure App Service에 자동 배포

## 3단계: Azure 리소스 구성

GitHub Actions에서 Azure에 배포하기 위해 Deployment Center에서 GitHub 연동을 설정합니다. Azure는 자동으로 GitHub Actions 워크플로우를 생성해줍니다.

## 4단계: 환경 변수 설정

Azure App Service의 Configuration 섹션에서 다음을 설정합니다:

- `SECRET_KEY`: Django 시크릿 키
- `DATABASE_URL`: PostgreSQL 연결 문자열
- `ALLOWED_HOSTS`: 앱 도메인
- `DEBUG`: False (프로덕션 환경)

## 5단계: 배포 테스트

코드를 수정하고 master 브랜치에 push하면 GitHub Actions가 자동으로 테스트를 실행하고 Azure에 배포하는 과정을 확인합니다.

## 필요한 Azure 리소스

## 필수 리소스

| **리소스** | **용도** | **권장 스펙** |
| --- | --- | --- |
| **App Service Plan** | Django 앱 호스팅 | B1 Basic (Linux) |
| **App Service** | 웹 애플리케이션 실행 환경 | Python 3.11 런타임 |
| **PostgreSQL Flexible Server** | 데이터베이스 | Burstable B1ms (1 vCore, 2GB RAM) |
| **Storage Account** (선택사항) | 정적/미디어 파일 저장 | Standard LRS |

==== 안농 ====