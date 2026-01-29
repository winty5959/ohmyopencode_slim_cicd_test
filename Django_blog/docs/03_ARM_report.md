# 03_ARM_report.md

본 문서는 `instruct.md`의 **3단계(Azure 리소스 구성)** 수행 내역(리소스 식별 및 ARM 템플릿 작성/수정)을 기록합니다.

## 1. 목표(요구사항)

- Django 앱을 Azure App Service에 배포할 수 있도록 필요한 Azure 리소스를 식별
- 해당 리소스를 **ARM 템플릿(JSON)** 으로 재현 가능하게 작성

## 2. 전제/결정사항

- 리소스 배포 location: `azuredeploy.json`의 `location` 파라미터 기본값을 **`[resourceGroup().location]`** 으로 설정
  - 즉, 리소스 그룹 생성 시 지정한 지역을 그대로 따름
- App Service Plan: **Linux / B1(Basic)** 유지
  - 결과적으로 **VNet Integration 미사용**
- DB 네트워크: B1 플랜 제약으로 인해 PostgreSQL은 **Public access** 구성
  - 템플릿에 `AllowAzureServices(0.0.0.0)` 방화벽 룰 포함
- Storage Account: **포함(createStorage=true 기본값)**

## 3. 산출물(생성/수정 파일)

### 3.1 ARM 템플릿 파일

- `CICD/infra/arm/azuredeploy.json`
  - App Service Plan, Web App, Postgres Flexible Server(+DB+FW), Storage Account 생성
- `CICD/infra/arm/azuredeploy.parameters.example.json`
  - 예시 파라미터 파일

### 3.2 최종 가이드 문서

- `CICD/infra/arm/README.md`
  - Azure에 **리소스가 하나도 없는 상태(구독만 있음)** 를 기준으로,
    - `az login`
    - (선택) `az account set`
    - `az group create`
    - `az deployment group create`
    - OIDC(Service Principal + federated credential) 설정 및 GitHub Secrets 설정
    까지 end-to-end 명령어를 포함

## 4. ARM 템플릿에 포함된 리소스(요약)

### 4.1 App Service Plan (Linux)

- 타입: `Microsoft.Web/serverfarms`
- sku: `B1` / `Basic`
- Linux 설정: `reserved: true`

### 4.2 App Service (Linux Web App)

- 타입: `Microsoft.Web/sites`
- 런타임: `PYTHON|3.11` (`linuxFxVersion`)
- HTTPS only: `httpsOnly: true`

#### App Settings (Microsoft.Web/sites/config)

프로덕션에 필요한 환경변수를 템플릿에서 주입:

- `DEBUG=0`
- `SECRET_KEY` = 템플릿 파라미터 `secretKey` (secureString)
- `ALLOWED_HOSTS`
  - 파라미터가 비어있으면 `<webAppName>.azurewebsites.net`로 기본 설정
- `DATABASE_URL`
  - 템플릿에서 PostgreSQL FQDN 기반으로 생성 (`sslmode=require` 포함)
- 배포 관련
  - `WEBSITE_RUN_FROM_PACKAGE=1`
  - `SCM_DO_BUILD_DURING_DEPLOYMENT=true`

### 4.3 PostgreSQL Flexible Server

- 타입: `Microsoft.DBforPostgreSQL/flexibleServers`
- sku: `Standard_B1ms` (Burstable)
- 버전: `16`
- 네트워크: `publicNetworkAccess: Enabled`
- 하위 리소스
  - database: `flexibleServers/databases`
  - firewall rule: `flexibleServers/firewallRules` (`AllowAzureServices`)

### 4.4 Storage Account (옵션)

- 타입: `Microsoft.Storage/storageAccounts`
- sku: `Standard_LRS`
- 조건부 생성: `createStorage` 파라미터 (기본 `true`)

## 5. 파라미터/출력(Outputs)

### 주요 파라미터

- `namePrefix` + `uniqueString(resourceGroup().id)` 조합으로 전역 유니크가 필요한 이름을 자동 생성
- `pgAdminPassword`(secureString), `secretKey`(secureString)

### outputs

- `webAppName`, `webAppUrl`
- `postgresHost`, `postgresDatabase`
- `storageAccountName` (createStorage=true일 때)

## 6. 배포 중 발생한 템플릿 오류 및 수정

### 오류

- (InvalidTemplate) `storageAccountName`의 기본값 계산에서 `substring(..., 0, 24)` 사용
  - 생성된 문자열 길이가 24보다 짧은 경우(예: 21) ARM이 실패

### 수정

- `substring` 길이를 `min(length(...), 24)`로 변경하여, 문자열 길이가 24 미만이어도 항상 유효하도록 보정
  - 변경 위치: `CICD/infra/arm/azuredeploy.json`의 `storageAccountName.defaultValue`

## 7. 검증

- 템플릿 JSON 구문 정합성 확인(로컬에서 `python3 -m json.tool`로 검증)
- Azure 배포는 리소스 그룹 생성 이후 `az deployment group create`로 수행하도록 문서에 명시
