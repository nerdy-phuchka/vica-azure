targetScope = 'resourceGroup'
@description('Choose only a region permitted for borrower data and supporting all selected services.')
param location string = resourceGroup().location
param prefix string = 'vca'
@secure()
@minLength(20)
param databasePassword string
@description('Approved model name and version; capacity/availability must be preflighted.')
param modelName string
param modelVersion string
param modelSku string = 'Standard'
param modelCapacity int = 10
var suffix = uniqueString(resourceGroup().id)
var base = '${prefix}${suffix}'
resource vnet 'Microsoft.Network/virtualNetworks@2023-11-01' = {
  name: '${prefix}-vnet'
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: [
        '10.42.0.0/16'
      ]
    }
    subnets: [
      {
        name: 'apps'
        properties: {
          addressPrefix: '10.42.0.0/23'
          delegations: [
            {
              name: 'aca'
              properties: {
                serviceName: 'Microsoft.App/environments'
              }
            }
          ]
        }
      }
      {
        name: 'postgres'
        properties: {
          addressPrefix: '10.42.2.0/24'
          delegations: [
            {
              name: 'pg'
              properties: {
                serviceName: 'Microsoft.DBforPostgreSQL/flexibleServers'
              }
            }
          ]
        }
      }
      {
        name: 'endpoints'
        properties: {
          addressPrefix: '10.42.3.0/24'
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
    ]
  }
}
resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${prefix}-runtime'
  location: location
}
resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${prefix}-logs'
  location: location
  properties: {
    retentionInDays: 30
    sku: {
      name: 'PerGB2018'
    }
  }
}
resource insights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${prefix}-insights'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logs.id
  }
}
resource environment 'Microsoft.App/managedEnvironments@2025-01-01' = {
  name: '${prefix}-environment'
  location: location
  properties: {
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
    vnetConfiguration: {
      infrastructureSubnetId: '${vnet.id}/subnets/apps'
      internal: false
    }
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}
resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: '${base}acr'
  location: location
  sku: {
    name: 'Standard'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
}
resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: '${base}docs'
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    publicNetworkAccess: 'Disabled'
  }
}
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    isVersioningEnabled: true
  }
}
resource documents 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: 'documents'
  properties: {
    publicAccess: 'None'
  }
}
resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${base}kv'
  location: location
  properties: {
    tenantId: tenant().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enablePurgeProtection: true
    publicNetworkAccess: 'Disabled'
  }
}
resource pgZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: '${prefix}.private.postgres.database.azure.com'
  location: 'global'
}
resource pgLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: pgZone
  name: '${prefix}-pg-link'
  location: 'global'
  properties: {
    virtualNetwork: {
      id: vnet.id
    }
    registrationEnabled: false
  }
}
resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: '${base}-pg'
  location: location
  sku: {
    name: 'Standard_B2ms'
    tier: 'Burstable'
  }
  properties: {
    version: '16'
    administratorLogin: 'vcaadmin'
    administratorLoginPassword: databasePassword
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    network: {
      delegatedSubnetResourceId: '${vnet.id}/subnets/postgres'
      privateDnsZoneArmResourceId: pgZone.id
      publicNetworkAccess: 'Disabled'
    }
  }
  dependsOn: [
    pgLink
  ]
}
resource database 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = {
  parent: postgres
  name: 'vca'
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}
resource databaseSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: vault
  name: 'database-url'
  properties: {
    value: 'postgresql+psycopg://vcaadmin:${uriComponent(databasePassword)}@${postgres.properties.fullyQualifiedDomainName}:5432/vca?sslmode=require'
  }
}
resource docAi 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: '${base}-documents'
  location: location
  kind: 'FormRecognizer'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: '${base}-documents'
    publicNetworkAccess: 'Disabled'
    disableLocalAuth: true
  }
}
resource openAi 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: '${base}-openai'
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: '${base}-openai'
    publicNetworkAccess: 'Disabled'
    disableLocalAuth: true
  }
}
resource model 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openAi
  name: 'vca-analysis'
  sku: {
    name: modelSku
    capacity: modelCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
    versionUpgradeOption: 'NoAutoUpgrade'
  }
}
resource search 'Microsoft.Search/searchServices@2023-11-01' = {
  name: '${base}-search'
  location: location
  sku: {
    name: 'basic'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    publicNetworkAccess: 'disabled'
    disableLocalAuth: true
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
}
resource serviceBus 'Microsoft.ServiceBus/namespaces@2024-01-01' = {
  name: '${base}-bus'
  location: location
  sku: {
    name: 'Premium'
    tier: 'Premium'
    capacity: 1
  }
  properties: {
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Disabled'
    disableLocalAuth: true
  }
}
resource queue 'Microsoft.ServiceBus/namespaces/queues@2024-01-01' = {
  parent: serviceBus
  name: 'document-jobs'
  properties: {
    lockDuration: 'PT1M'
    maxDeliveryCount: 5
    defaultMessageTimeToLive: 'P1D'
    requiresDuplicateDetection: true
  }
}
var privateServices = [
  {
    name: 'blob'
    id: storage.id
    group: 'blob'
    zone: 'privatelink.blob.core.windows.net'
  }
  {
    name: 'vault'
    id: vault.id
    group: 'vault'
    zone: 'privatelink.vaultcore.azure.net'
  }
  {
    name: 'documents'
    id: docAi.id
    group: 'account'
    zone: 'privatelink.cognitiveservices.azure.com'
  }
  {
    name: 'openai'
    id: openAi.id
    group: 'account'
    zone: 'privatelink.openai.azure.com'
  }
  {
    name: 'search'
    id: search.id
    group: 'searchService'
    zone: 'privatelink.search.windows.net'
  }
  {
    name: 'bus'
    id: serviceBus.id
    group: 'namespace'
    zone: 'privatelink.servicebus.windows.net'
  }
]
module privateEndpoints 'modules/private-endpoint.bicep' = [for service in privateServices: {
    name: '${prefix}-${service.name}-private'
    params: {
      name: '${prefix}-${service.name}-pe'
      location: location
      resourceId: service.id
      groupId: service.group
      zoneName: service.zone
      subnetId: '${vnet.id}/subnets/endpoints'
      vnetId: vnet.id
    }
  }
]
output runtimeIdentityId string = identity.id
output runtimeClientId string = identity.properties.clientId
output runtimePrincipalId string = identity.properties.principalId
output registryName string = registry.name
output registryId string = registry.id
output registryServer string = registry.properties.loginServer
output environmentId string = environment.id
output storageId string = storage.id
output storageUrl string = storage.properties.primaryEndpoints.blob
output vaultId string = vault.id
output databaseSecretUrl string = '${vault.properties.vaultUri}secrets/database-url'
output documentId string = docAi.id
output documentEndpoint string = docAi.properties.endpoint
output openAiId string = openAi.id
output openAiEndpoint string = openAi.properties.endpoint
output modelDeployment string = model.name
output searchId string = search.id
output searchEndpoint string = 'https://${search.name}.search.windows.net'
output busId string = serviceBus.id
output busNamespace string = '${serviceBus.name}.servicebus.windows.net'
output insightsConnection string = insights.properties.ConnectionString
