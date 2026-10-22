param location string = resourceGroup().location
param prefix string = 'vca'
param environmentId string
param runtimeIdentityId string
param runtimeClientId string
param registryServer string
param imageTag string
param databaseSecretUrl string
param storageUrl string
param documentEndpoint string
param openAiEndpoint string
param modelDeployment string
param searchEndpoint string
param busNamespace string
param entraTenantId string
param entraAudience string
@description('Optional allow-listed public IPv4 CIDR for the internal pilot web/API; empty permits authenticated internet access.')
param pilotAllowedCidr string = ''
var accessRules = empty(pilotAllowedCidr) ? [
] : [
  {
    name: 'pilot'
    ipAddressRange: pilotAllowedCidr
    action: 'Allow'
  }
]
resource scanner 'Microsoft.App/containerApps@2025-01-01' = {
  name: '${prefix}-scanner'
  location: location
  properties: {
    environmentId: environmentId
    configuration: {
      ingress: {
        external: false
        targetPort: 3310
        exposedPort: 3310
        transport: 'tcp'
      }
    }
    template: {
      containers: [
        {
          name: 'scanner'
          image: 'clamav/clamav:1.4'
          resources: {
            cpu: 2
            memory: '4Gi'
          }
          probes: [
            {
              type: 'Readiness'
              tcpSocket: {
                port: 3310
              }
              initialDelaySeconds: 60
              periodSeconds: 30
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}
var commonEnv = [
  {
    name: 'APP_MODE'
    value: 'azure'
  }
  {
    name: 'DEV_AUTH_ENABLED'
    value: 'false'
  }
  {
    name: 'DATABASE_URL'
    secretRef: 'database-url'
  }
  {
    name: 'AZURE_CLIENT_ID'
    value: runtimeClientId
  }
  {
    name: 'ENTRA_TENANT_ID'
    value: entraTenantId
  }
  {
    name: 'ENTRA_AUDIENCE'
    value: entraAudience
  }
  {
    name: 'AZURE_STORAGE_ACCOUNT_URL'
    value: storageUrl
  }
  {
    name: 'AZURE_DOCUMENT_ENDPOINT'
    value: documentEndpoint
  }
  {
    name: 'AZURE_OPENAI_ENDPOINT'
    value: openAiEndpoint
  }
  {
    name: 'AZURE_OPENAI_DEPLOYMENT'
    value: modelDeployment
  }
  {
    name: 'AZURE_SEARCH_ENDPOINT'
    value: searchEndpoint
  }
  {
    name: 'AZURE_SERVICEBUS_NAMESPACE'
    value: busNamespace
  }
  {
    name: 'SCANNER_MODE'
    value: 'clamav'
  }
  {
    name: 'CLAMAV_HOST'
    value: scanner.properties.configuration.ingress.fqdn
  }
]
resource api 'Microsoft.App/containerApps@2025-01-01' = {
  name: '${prefix}-api'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${runtimeIdentityId}': {
      }
    }
  }
  properties: {
    environmentId: environmentId
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: registryServer
          identity: runtimeIdentityId
        }
      ]
      secrets: [
        {
          name: 'database-url'
          keyVaultUrl: databaseSecretUrl
          identity: runtimeIdentityId
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: '${registryServer}/vca-api:${imageTag}'
          env: commonEnv
          resources: {
            cpu: 1
            memory: '2Gi'
          }
          probes: [
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 15
              periodSeconds: 10
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}
resource worker 'Microsoft.App/containerApps@2025-01-01' = {
  name: '${prefix}-worker'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${runtimeIdentityId}': {
      }
    }
  }
  properties: {
    environmentId: environmentId
    configuration: {
      registries: [
        {
          server: registryServer
          identity: runtimeIdentityId
        }
      ]
      secrets: [
        {
          name: 'database-url'
          keyVaultUrl: databaseSecretUrl
          identity: runtimeIdentityId
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'worker'
          image: '${registryServer}/vca-api:${imageTag}'
          command: [
            'python'
            '-m'
            'app.worker'
          ]
          env: commonEnv
          resources: {
            cpu: 1
            memory: '2Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}
resource web 'Microsoft.App/containerApps@2025-01-01' = {
  name: '${prefix}-web'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${runtimeIdentityId}': {
      }
    }
  }
  properties: {
    environmentId: environmentId
    configuration: {
      ingress: {
        external: true
        targetPort: 3000
        transport: 'auto'
        allowInsecure: false
        ipSecurityRestrictions: accessRules
      }
      registries: [
        {
          server: registryServer
          identity: runtimeIdentityId
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'web'
          image: '${registryServer}/vca-web:${imageTag}'
          resources: {
            cpu: 0.5
            memory: '1Gi'
          }
          env: [
            {
              name: 'API_INTERNAL_URL'
              value: 'https://${api.properties.configuration.ingress.fqdn}'
            }
            {
              name: 'NEXT_PUBLIC_AUTH_MODE'
              value: 'entra'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}
output webUrl string = 'https://${web.properties.configuration.ingress.fqdn}'
output apiUrl string = 'https://${api.properties.configuration.ingress.fqdn}'
