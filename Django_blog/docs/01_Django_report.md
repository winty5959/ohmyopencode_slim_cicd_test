# 01_Django_report.md

본 문서는 `/Users/seonung/Desktop/study/personal/project/ing_use/ohmyopencode_slim/CICD/Django_blog` 경로에서 수행한 **1단계(Django 프로젝트 준비)** 및 **검증(단위테스트/화면테스트/브라우저 E2E)** 작업 내역을 정리한 리포트입니다.

## 0. 기준 문서 확인

- 확인 파일: `instruct.md`
- 요구사항(1단계 요약)
  - Django 블로그 앱(게시글 CRUD, 모던 UI)
  - PostgreSQL 설정(로컬 docker 기반, 추후 Azure PostgreSQL로 전환 고려)
  - `requirements.txt` 작성(Django/psycopg2/gunicorn 등)
  - 유닛 테스트 최소 5개 이상
  - 테스트 프레임워크: pytest 또는 Django 기본 테스트

## 1. 사용자 결정(질문/답변)

- Django 프로젝트/앱 이름: **project=core, app=blog**
- 테스트 프레임워크: **pytest + pytest-django**
- Docker 범위(1단계): **앱 + DB 컨테이너화**

## 2. 구현 내역(1단계)

### 2.1 프로젝트 구조/핵심 파일

- Django 엔트리
  - `manage.py`
  - `core/settings.py`, `core/urls.py`, `core/asgi.py`, `core/wsgi.py`

- Blog 앱
  - 모델: `blog/models.py` (`Post`: title/content/created_at/updated_at)
  - CRUD 뷰(CBV): `blog/views.py`
  - URL: `blog/urls.py` (네임스페이스 `blog`)
  - 어드민: `blog/admin.py`
  - 폼: `blog/forms.py` (Bootstrap form-control 적용)
  - 마이그레이션: `blog/migrations/0001_initial.py`

### 2.2 UI(모던 디자인)

- Bootstrap 5 CDN 기반 템플릿 구성
  - `templates/base.html` (navbar, container, footer)
  - `templates/blog/post_list.html`
  - `templates/blog/post_detail.html`
  - `templates/blog/post_form.html`
  - `templates/blog/post_confirm_delete.html`

- 정적파일
  - `static/css/main.css`

### 2.3 환경변수/설정

- 예시 파일: `.env.example`
  - `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`
  - PostgreSQL 관련: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DATABASE_URL`

- DB 연결
  - `core/settings.py`에서 `DATABASE_URL`이 있으면 `dj-database-url`로 파싱

- 정적파일(WhiteNoise)
  - 개발(DEBUG=1)에서는 Manifest strict 문제 방지 위해 기본 `StaticFilesStorage` 사용
  - 배포(DEBUG=0)에서는 `CompressedManifestStaticFilesStorage` 사용

### 2.4 Docker(앱+DB)

- `docker-compose.yml`
  - `db`: `postgres:16-alpine` + healthcheck + 볼륨 `postgres_data`
  - `web`: `Dockerfile` 빌드 + `depends_on(db: healthy)` + `8000:8000`

- `Dockerfile`
  - Python 3.11 slim 기반
  - `requirements.txt` 설치
  - 실행 커맨드: migrate + collectstatic + gunicorn

### 2.5 의존성

- `requirements.txt`
  - Django, gunicorn, psycopg2-binary, dj-database-url, whitenoise, python-dotenv
  - pytest, pytest-django

## 3. 테스트(단위테스트/화면테스트)

### 3.1 pytest 설정

- `pytest.ini`
  - `DJANGO_SETTINGS_MODULE = core.settings`

### 3.2 테스트 파일/케이스

- 테스트 위치: `blog/tests/test_blog.py`
- 총 **11개** 테스트(작성 시점 기준)
  - 모델/CRUD 단위테스트
    - `__str__` 동작
    - create/update/delete POST 플로우
  - 화면(렌더링) 테스트(브라우저 없이 Django test client)
    - list/detail/create/update/delete-confirm 페이지 GET 200
    - 템플릿 사용 여부 확인
    - form field 존재 여부 확인

### 3.3 테스트 실행 결과

- 컨테이너 환경에서 실행:
  - `docker compose run --rm web pytest`
  - 결과: **11 passed**

## 4. 브라우저 E2E 화면 테스트(개발 검증 목적)

CI 포함이 아닌, 개발 완료 확인 목적의 브라우저 자동화로 CRUD 플로우를 실제 브라우저로 검증했습니다.

### 4.1 사용 도구

- `agent-browser` (로컬 브라우저 자동화)

### 4.2 수행 시나리오

대상: `http://localhost:8000`

1) 목록 진입
2) New Post 진입
3) 글 작성 후 저장
4) 상세 페이지 진입
5) 수정 페이지 진입 후 제목 수정/저장
6) 삭제 확인 페이지 진입 후 삭제
7) 목록 복귀 확인

### 4.3 산출물(스크린샷/영상)

- 폴더: `e2e_artifacts/`
- 스크린샷(성공 플로우):
  - `v2_01_list.png`
  - `v2_02_create.png`
  - `v2_03_list_after_create.png`
  - `v2_04_detail.png`
  - `v2_05_edit.png`
  - `v2_06_detail_after_edit.png`
  - `v2_07_delete_confirm.png`
  - `v2_08_list_after_delete.png`
- 영상(성공 플로우):
  - `blog_crud_flow_v2.webm`

### 4.4 참고(초기 E2E 실행 이슈)

- “New Post” 링크가 navbar/본문에 2개 존재하여 `find text "New Post"`가 strict mode 충돌을 발생
- 이후 locator를 더 구체화하여(v2) 정상 CRUD 시나리오 완료

## 5. 재현 방법(로컬)

### 5.1 실행

```bash
cd /Users/seonung/Desktop/study/personal/project/ing_use/ohmyopencode_slim/CICD/Django_blog
cp .env.example .env
docker compose up --build
```

브라우저 접속: `http://localhost:8000/`

### 5.2 단위/화면 테스트(pytest)

```bash
docker compose run --rm web pytest
```

### 5.3 브라우저 E2E(수동 재수행 시)

동일한 로컬 서버 기동 상태에서 `agent-browser`로 CRUD 플로우를 수행하며 스크린샷/영상 산출.

## 6. 작업 산출물 목록(요약)

- 런타임/앱
  - `manage.py`
  - `core/*`
  - `blog/*`
  - `blog/migrations/0001_initial.py`

- UI
  - `templates/*`
  - `static/css/main.css`

- 환경/도커
  - `.env.example`
  - `Dockerfile`
  - `docker-compose.yml`

- 테스트
  - `pytest.ini`
  - `blog/tests/test_blog.py`

- E2E 아티팩트
  - `e2e_artifacts/*`
