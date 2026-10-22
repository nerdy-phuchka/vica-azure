param(
  [Parameter(Mandatory=$true)][string]$ResourceGroup,
  [Parameter(Mandatory=$true)][string]$Location,
  [Parameter(Mandatory=$true)][string]$ModelName,
  [Parameter(Mandatory=$true)][string]$ModelVersion,
  [Parameter(Mandatory=$true)][string]$EntraTenantId,
  [Parameter(Mandatory=$true)][string]$ApiAudience,
  [Parameter(Mandatory=$true)][string]$SpaClientId,
  [Parameter(Mandatory=$true)][string]$ApiScope,
  [string]$Prefix='vca',
  [string]$ImageTag='pilot-001',
  [string]$PilotAllowedCidr='',
  [switch]$ProvisionFoundation,
  [switch]$RotateDatabasePassword
)
$ErrorActionPreference='Stop'
$packageRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
function Check-Az { if($LASTEXITCODE -ne 0){throw 'Azure CLI command failed. See the preceding service error.'} }
Get-Command az -ErrorAction Stop | Out-Null
az account show --output none
Check-Az
if($Prefix -notmatch '^[a-z][a-z0-9]{1,5}$'){throw 'Prefix must be 2â€“6 lowercase alphanumeric characters.'}
Write-Host 'Preflight: confirm the selected region, model/version, quota and processing geography before continuing.'
az bicep build --file (Join-Path $PSScriptRoot '01_foundation.bicep') --stdout | Out-Null
Check-Az
az bicep build --file (Join-Path $PSScriptRoot '02_applications.bicep') --stdout | Out-Null
Check-Az
az group create --name $ResourceGroup --location $Location --output none
Check-Az
$priorRaw=az deployment group show --resource-group $ResourceGroup --name vca-foundation --query properties.outputs --output json 2>$null
$hasFoundation=$LASTEXITCODE -eq 0 -and $priorRaw
if($hasFoundation -and -not $ProvisionFoundation){
  $foundation=$priorRaw|ConvertFrom-Json
  Write-Host 'Reusing the existing foundation and database secret; deploying application images only.'
}else{
  if($hasFoundation -and -not $RotateDatabasePassword){throw 'Foundation updates rotate the database password. Use -RotateDatabasePassword only for a coordinated rotation, or omit -ProvisionFoundation.'}
$secretBytes=New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Fill($secretBytes)
$databasePassword=[Convert]::ToBase64String($secretBytes)+'aA1!'
$parameterFile=Join-Path ([System.IO.Path]::GetTempPath()) ('vca-parameters-'+[guid]::NewGuid()+'.json')
try {
  # No secret is interpolated into shell commands or printed. Temporary parameters are deleted in finally.
  @{parameters=@{location=@{value=$Location};prefix=@{value=$Prefix};databasePassword=@{value=$databasePassword};modelName=@{value=$ModelName};modelVersion=@{value=$ModelVersion}}}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $parameterFile -Encoding utf8
  $foundationRaw=az deployment group create --resource-group $ResourceGroup --name vca-foundation --template-file (Join-Path $PSScriptRoot '01_foundation.bicep') --parameters ('@'+$parameterFile) --query properties.outputs --output json
  Check-Az
  $foundation=$foundationRaw|ConvertFrom-Json
} finally {if(Test-Path -LiteralPath $parameterFile){Remove-Item -LiteralPath $parameterFile};$databasePassword=$null}
}
$principal=$foundation.runtimePrincipalId.value
$assignments=@(
  @('Storage Blob Data Contributor',$foundation.storageId.value),
  @('Key Vault Secrets User',$foundation.vaultId.value),
  @('Cognitive Services User',$foundation.documentId.value),
  @('Cognitive Services OpenAI User',$foundation.openAiId.value),
  @('Search Index Data Contributor',$foundation.searchId.value),
  @('Search Service Contributor',$foundation.searchId.value),
  @('Azure Service Bus Data Sender',$foundation.busId.value),
  @('Azure Service Bus Data Receiver',$foundation.busId.value),
  @('AcrPull',$foundation.registryId.value)
)
foreach($assignment in $assignments){
  az role assignment create --assignee-object-id $principal --assignee-principal-type ServicePrincipal --role $assignment[0] --scope $assignment[1] --output none
  Check-Az
}
# ACR cloud builds avoid requiring local Docker; registry build quota/network must permit dependencies.
az acr build --registry $foundation.registryName.value --image ('vca-api:'+$ImageTag) --file 03_Backend/Dockerfile $packageRoot --no-logs
Check-Az
az acr build --registry $foundation.registryName.value --image ('vca-web:'+$ImageTag) --file 04_Frontend/Dockerfile --build-arg NEXT_PUBLIC_AUTH_MODE=entra --build-arg ('NEXT_PUBLIC_ENTRA_CLIENT_ID='+$SpaClientId) --build-arg ('NEXT_PUBLIC_ENTRA_TENANT_ID='+$EntraTenantId) --build-arg ('NEXT_PUBLIC_API_SCOPE='+$ApiScope) $packageRoot --no-logs
Check-Az
$applicationParameters=@{parameters=@{
  location=@{value=$Location};prefix=@{value=$Prefix};environmentId=@{value=$foundation.environmentId.value};
  runtimeIdentityId=@{value=$foundation.runtimeIdentityId.value};runtimeClientId=@{value=$foundation.runtimeClientId.value};
  registryServer=@{value=$foundation.registryServer.value};imageTag=@{value=$ImageTag};
  databaseSecretUrl=@{value=$foundation.databaseSecretUrl.value};storageUrl=@{value=$foundation.storageUrl.value};
  documentEndpoint=@{value=$foundation.documentEndpoint.value};openAiEndpoint=@{value=$foundation.openAiEndpoint.value};
  modelDeployment=@{value=$foundation.modelDeployment.value};searchEndpoint=@{value=$foundation.searchEndpoint.value};
  busNamespace=@{value=$foundation.busNamespace.value};entraTenantId=@{value=$EntraTenantId};entraAudience=@{value=$ApiAudience};
  pilotAllowedCidr=@{value=$PilotAllowedCidr}
}}
$appsParameterFile=Join-Path ([System.IO.Path]::GetTempPath()) ('vca-apps-'+[guid]::NewGuid()+'.json')
try {
  $applicationParameters|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $appsParameterFile -Encoding utf8
  az deployment group create --resource-group $ResourceGroup --name vca-apps --template-file (Join-Path $PSScriptRoot '02_applications.bicep') --parameters ('@'+$appsParameterFile) --query properties.outputs --output json
  Check-Az
}finally{if(Test-Path -LiteralPath $appsParameterFile){Remove-Item -LiteralPath $appsParameterFile}}
Write-Host 'Next: configure the SPA redirect URI, assign Entra roles, initialise Search from the worker console, and run the pilot acceptance suite. No application data has been fabricated.'
