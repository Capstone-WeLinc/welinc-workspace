// What every app in one environment stands on (spec 0008): the two storage accounts, the identity
// that pulls images, and the Container Apps environment with its logs. The trial allows one
// Container Apps environment in the subscription, so staging makes it and production only reads it
// (createEnvironment false). Its environment storage is env-storage.bicep, scoped to its group.

param envName string
param location string

@description('True on staging: make the Container Apps environment and its logs. False on production: use the existing one.')
param createEnvironment bool

@description('The one Container Apps environment both WeLinc environments run in.')
param environmentName string

@description('The resource group that holds it (rg-welinc-staging).')
param environmentResourceGroup string

@description('The VRMS web origin, allowed to GET blobs through signed links.')
param vrmsWebOrigin string

@description('The VMMS web origin, allowed to GET its own blobs through signed links.')
param vmmsWebOrigin string

var suffix = take(uniqueString(resourceGroup().id), 8)

// Logs: 30 days, and a daily cap near the free amount. Both environments' logs land here (logs
// are set per Container Apps environment), so the cap is twice one environment's 0.15 GB.
resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = if (createEnvironment) {
  name: 'log-welinc-${envName}'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
    workspaceCapping: { dailyQuotaGb: json('0.3') }
  }
}

// Files account: shared key on, because Container Apps mounts Azure Files only with a key
resource files 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: 'st${suffix}files'
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true
  }
}

resource fileService 'Microsoft.Storage/storageAccounts/fileServices@2023-05-01' = {
  parent: files
  name: 'default'
}

// Profile pictures, mounted by welinc-auth at /app/uploads (AC-14)
resource authShare 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-05-01' = {
  parent: fileService
  name: 'auth-uploads'
  properties: {
    shareQuota: 5
  }
}

// Blob account: shared key off; backend-vrms reaches it with its own identity (spec 0017)
resource blobs 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: 'st${suffix}blob'
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: blobs
  name: 'default'
  properties: {
    cors: {
      corsRules: [
        {
          allowedOrigins: [vrmsWebOrigin, vmmsWebOrigin]
          allowedMethods: ['GET']
          allowedHeaders: ['*']
          exposedHeaders: ['Content-Length', 'Content-Type']
          maxAgeInSeconds: 600
        }
      ]
    }
  }
}

// One private container per system. Each backend's identity is allowed into its own container
// only (env.bicep, access), so no system reads another system's files.
resource attachments 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = [for c in ['vrms-attachments', 'vmms-attachments']: {
  parent: blobService
  name: c
  properties: {
    publicAccess: 'None'
  }
}]

resource cae 'Microsoft.App/managedEnvironments@2024-03-01' = if (createEnvironment) {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs!.properties.customerId
        sharedKey: logs!.listKeys().primarySharedKey
      }
    }
  }
}

// Production's view of the same environment (it must not change it, AC-23)
resource sharedCae 'Microsoft.App/managedEnvironments@2024-03-01' existing = if (!createEnvironment) {
  name: environmentName
  scope: resourceGroup(environmentResourceGroup)
}

// Every app and job pulls images with this one identity (AcrPull on the shared registry)
resource pull 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-welinc-${envName}-pull'
  location: location
}

output environmentId string = createEnvironment ? cae.id : sharedCae.id
output environmentName string = environmentName
output defaultDomain string = createEnvironment ? cae!.properties.defaultDomain : sharedCae!.properties.defaultDomain
output staticIp string = createEnvironment ? cae!.properties.staticIp : sharedCae!.properties.staticIp
output customDomainVerificationId string = createEnvironment
  ? cae!.properties.customDomainConfiguration.customDomainVerificationId
  : sharedCae!.properties.customDomainConfiguration.customDomainVerificationId
output filesAccountName string = files.name
output authShareName string = authShare.name
output blobAccountName string = blobs.name
output blobEndpoint string = 'https://${blobs.name}.blob.${environment().suffixes.storage}'
output pullIdentityId string = pull.id
output pullIdentityName string = pull.name
output pullPrincipalId string = pull.properties.principalId
