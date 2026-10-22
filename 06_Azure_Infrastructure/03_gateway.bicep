@description('Optional gateway. Backend validates Entra JWT independently; API Management is not a substitute for API authorisation.')
param name string
param location string = resourceGroup().location
param publisherEmail string
param backendUrl string
param entraTenantId string
param entraAudience string
resource gateway 'Microsoft.ApiManagement/service@2024-05-01' = {
  name: name
  location: location
  sku: {
    name: 'Developer'
    capacity: 1
  }
  properties: {
    publisherEmail: publisherEmail
    publisherName: 'VCA Pilot'
  }
}
resource api 'Microsoft.ApiManagement/service/apis@2024-05-01' = {
  parent: gateway
  name: 'vca'
  properties: {
    displayName: 'VCA LOS API'
    path: 'vca'
    protocols: [
      'https'
    ]
    serviceUrl: backendUrl
    subscriptionRequired: false
    apiRevision: '1'
  }
}
resource getOperation 'Microsoft.ApiManagement/service/apis/operations@2024-05-01' = {
  parent: api
  name: 'get'
  properties: {
    displayName: 'GET'
    method: 'GET'
    urlTemplate: '/*'
  }
}
resource postOperation 'Microsoft.ApiManagement/service/apis/operations@2024-05-01' = {
  parent: api
  name: 'post'
  properties: {
    displayName: 'POST'
    method: 'POST'
    urlTemplate: '/*'
  }
}
resource policy 'Microsoft.ApiManagement/service/apis/policies@2024-05-01' = {
  parent: api
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: '''
<policies><inbound><base /><validate-jwt header-name="Authorization" failed-validation-httpcode="401" require-scheme="Bearer"><openid-config url="https://login.microsoftonline.com/${entraTenantId}/v2.0/.well-known/openid-configuration" /><audiences><audience>${entraAudience}</audience></audiences></validate-jwt><rate-limit-by-key calls="120" renewal-period="60" counter-key="@(context.Request.IpAddress)" /></inbound><backend><base /></backend><outbound><base /></outbound><on-error><base /></on-error></policies>
'''
  }
}
output gatewayUrl string = '${gateway.properties.gatewayUrl}/vca'
