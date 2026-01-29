# CICD 실습: Django → GitHub Actions → Azure App Service

이 문서는 레포지토리(루트: `CICD/`)의 **Azure 리소스(ARM) 배포**부터 **GitHub Actions(OIDC) 로그인/배포**까지 한 번에 따라할 수 있도록 정리한 최종 가이드입니다.

## 디렉토리 구성

- `Django_blog/` : Django 앱 소스(로컬 개발/테스트)
- `.github/workflows/django-ci-cd.yml` : CI/CD 워크플로
- `infra/arm/` : Azure 리소스 ARM 템플릿(이 문서 위치)

---

## 1) 로컬 실행 (Docker: 앱+DB)

```bash
cd Django_blog
cp .env.example .env
docker compose up --build
```

- 접속: http://localhost:8000

## 2) 로컬 테스트(pytest)

```bash
cd Django_blog
pip install -r requirements.txt
pytest
```

---

## 3) Azure 리소스 준비(ARM 배포)

이 폴더는 `instruct.md` 3단계(필요 Azure 리소스 구성)를 위해 ARM 템플릿을 제공합니다.

### 3.1 생성 리소스

- App Service Plan (Linux) **B1 Basic**
- App Service (Linux Web App) **Python 3.11**
- PostgreSQL Flexible Server **Burstable B1ms** + database + firewall rule(AllowAzureServices)
- Storage Account (선택사항)

> 참고(중요): App Service Plan을 **B1(Basic)** 으로 유지하는 구성이라 **VNet Integration을 사용하지 않습니다**.
> 따라서 PostgreSQL은 **Public access**로 생성되며, ARM에서 `AllowAzureServices(0.0.0.0)` 방화벽 규칙을 넣었습니다.

### 3.2 사전 준비

- Azure CLI 로그인

```bash
az login
az account show
```

> 현재 구독만 있고 Azure에 리소스가 하나도 없는 상태를 기준으로 작성합니다.

#### (선택) 구독 선택

여러 구독이 있는 경우, 사용할 구독을 먼저 선택하세요.

```bash
az account list -o table
az account set --subscription <subscription-id-or-name>
```

#### 리소스 그룹 생성

ARM 템플릿은 **리소스 그룹 단위 배포**(`az deployment group create`)이므로, 먼저 리소스 그룹을 생성해야 합니다.

```bash
# 예: koreacentral
az group create \
  --name <rg-name> \
  --location <location>
```

예시:

```bash
az group create --name rg-ohmyopen-dev --location koreacentral
```

### 3.3 ARM 템플릿 배포

템플릿 파일:
- `azuredeploy.json`
- `azuredeploy.parameters.example.json`

```bash
az deployment group create \
  --resource-group <rg-name> \
  --template-file infra/arm/azuredeploy.json \
  --parameters @infra/arm/azuredeploy.parameters.example.json \
  --parameters \
      pgAdminPassword='<strong-postgres-password>' \
      secretKey='<django-secret-key>'
```

> TIP: 이 문서는 `infra/arm/README.md`에 있지만, 위 명령은 **레포 루트(`CICD/`)에서 실행**하는 것을 기준으로 작성했습니다.
> 만약 현재 디렉토리가 `infra/arm/`라면 아래처럼 실행하세요.

```bash
az deployment group create \
  --resource-group <rg-name> \
  --template-file azuredeploy.json \
  --parameters @azuredeploy.parameters.example.json \
  --parameters \
      pgAdminPassword='<strong-postgres-password>' \
      secretKey='<django-secret-key>'
```

배포 outputs로 아래 값이 나오면, 이후 단계에서 사용합니다.

- `webAppName`
- `webAppUrl`
- `postgresHost`

### 3.4 배포 후 해야 할 일

- App Service Configuration에 env 값이 잘 들어갔는지 확인
  - `DEBUG=0`, `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL`
- GitHub Actions(2단계)에서 Azure deploy를 활성화하려면 GitHub Secrets(OIDC) 설정 필요

---

## 4) GitHub Actions → Azure 로그인(OIDC) → 배포 설정

이 프로젝트는 배포 인증 방식으로 **OIDC(Service Principal + federated credential)** 를 사용합니다.

### 4.1 GitHub Actions 워크플로 확인

- 파일: `.github/workflows/django-ci-cd.yml`
- 트리거: `push` to `main`
- `deploy` job은 아래 Azure 관련 Secrets가 모두 설정되어야 실행됩니다(그 전에는 자동 스킵).

### 4.2 Azure: Service Principal + Federated Credential 생성

아래는 **공식 문서 흐름**(App registration + SP + federated credential) 기반 예시입니다.

문서:
- GitHub OIDC → Azure: https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-azure
- App Service + GitHub Actions(OIDC): https://learn.microsoft.com/en-us/azure/app-service/deploy-github-actions?tabs=openid%2Caspnetcore

#### (1) Entra 앱(App registration) 및 SP 생성

```bash
APP_ID=$(az ad app create --display-name "gh-oidc-<project>" --query appId -o tsv)
SP_OBJECT_ID=$(az ad sp create --id "$APP_ID" --query id -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
```

#### (2) RBAC 권한 부여(리소스 그룹 범위 권장)

```bash
az role assignment create \
  --role "Contributor" \
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/<rg-name>" \
  --assignee-object-id "$SP_OBJECT_ID" \
  --assignee-principal-type ServicePrincipal
```

#### (3) Federated Credential 추가(main 브랜치)

`ORG/REPO`를 GitHub 저장소로 바꿔주세요.

```bash
cat > credential.json <<'JSON'
{
  "name": "github-oidc-main",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:ORG/REPO:ref:refs/heads/main",
  "description": "GitHub OIDC for main",
  "audiences": ["api://AzureADTokenExchange"]
}
JSON

az ad app federated-credential create \
  --id "$APP_ID" \
  --parameters credential.json
```

### 4.3 GitHub Secrets 설정

GitHub 저장소 → **Settings → Secrets and variables → Actions → New repository secret**

- `AZURE_CLIENT_ID` = 위에서 만든 `APP_ID`
- `AZURE_TENANT_ID` = `TENANT_ID`
- `AZURE_SUBSCRIPTION_ID` = `SUBSCRIPTION_ID`
- `AZURE_WEBAPP_NAME` = ARM 배포 output의 `webAppName`

### 4.4 배포 테스트

1) `main`에 push
2) GitHub Actions에서 `django-ci-cd` 워크플로 실행 확인
3) CI가 성공하면 deploy job이 실행(Secrets 설정 완료 시)

---

## 5) App Service 환경변수(프로덕션)

ARM 템플릿이 기본적으로 App Settings에 아래 값을 넣도록 되어 있습니다.

- `DEBUG=0`
- `SECRET_KEY` (ARM 파라미터 secureString)
- `ALLOWED_HOSTS` (기본: `<webAppName>.azurewebsites.net`)
- `DATABASE_URL` (PostgreSQL 연결 문자열, `sslmode=require` 포함)

> Django 설정상, `DEBUG=0`인 경우 `SECRET_KEY`는 반드시 실제 값으로 설정되어야 합니다(기본값이면 실행 중 에러).

---

## 6) 보안 체크리스트(푸시 전 필수)

### 6.1 절대 커밋하면 안 되는 것

- `Django_blog/.env` (로컬 개발용)
- `**/e2e_artifacts/*` (스크린샷/영상)
- `**/staticfiles/*`
- 비밀번호/토큰/키가 들어있는 JSON/YAML

현재 레포에는 `.gitignore`가 위 항목들을 무시하도록 설정되어 있습니다.
단, **이미 git에 추적(tracked)된 파일은 .gitignore로 제거되지 않습니다.**

### 6.2 푸시 전 점검 커맨드

```bash
git status
git add -n .
```

만약 실수로 `.env` 등이 스테이징/추적되었다면:

```bash
git rm --cached Django_blog/.env
git rm --cached -r Django_blog/e2e_artifacts
```
