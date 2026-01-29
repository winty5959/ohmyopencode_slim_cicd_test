# 04_CD_report.md

본 문서는 CD(Continuous Deployment) 단계에서 발생한 **GitHub Actions 워크플로 유효성 오류**를 해소하기 위해 수행한 작업 내역을 기록합니다.

## 1. 문제 상황

- 증상: GitHub Actions에서 워크플로가 실행되지 않고 아래 오류로 **워크플로 파일이 invalid** 처리됨

  - `Invalid workflow file: .github/workflows/django-ci-cd.yml#L1`
  - 원인 메시지: `Unrecognized named-value: 'secrets'` (job-level `if` 구문에서 secrets 참조)

## 2. 원인

- GitHub Actions의 **job-level `if:` 조건식에서는 `secrets` 컨텍스트를 사용할 수 없음**
- 기존 `deploy` job에서 아래와 같은 방식으로 secrets 존재 여부를 job-level `if`에서 검사하려 했고, 이로 인해 YAML이 유효하지 않게 됨
  - `secrets.AZURE_WEBAPP_NAME != '' && ...`

## 3. 조치 내용(수정 사항)

수정 파일:

- `CICD/.github/workflows/django-ci-cd.yml`

### 3.1 precheck job 추가

- `precheck` job을 추가하여, **step 내에서** Azure 관련 secrets 4개가 모두 존재하는지 확인
- 확인 결과를 job output으로 전달

관련 위치:

- `precheck` job 추가: 워크플로 **13–28 라인**
  - output: `deploy_enabled=true/false`

### 3.2 deploy job 조건식 수정

- `deploy` job이 `precheck` 결과를 사용하도록 변경

관련 위치:

- `deploy.needs`: `[ci, precheck]`
- `deploy.if`: `${{ needs.precheck.outputs.deploy_enabled == 'true' }}`
  - 워크플로 **93–96 라인**

## 4. 기대 동작

- Azure 관련 secrets가 모두 설정되어 있으면:
  - `precheck` → `deploy_enabled=true`
  - `ci` 성공 후 `deploy` job이 실행되어 Azure 배포 수행

- secrets가 하나라도 비어 있으면:
  - `precheck` → `deploy_enabled=false`
  - `ci`는 정상 실행되지만 `deploy`는 **skip**

## 5. 사용자 후속 작업(필수)

GitHub 저장소 Secrets에 아래 값을 설정해야 CD가 동작합니다.

- `AZURE_WEBAPP_NAME`
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

설정 후 `main` 브랜치에 push(또는 workflow_dispatch 수동 실행)하면, CI 통과 후 deploy job이 실행됩니다.
