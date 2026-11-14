// What every app in one environment stands on (spec 0008): logs, the two storage accounts, the
// Container Apps environment with the auth file share, and the identity that pulls images.

param envName string
param location string

@description('The VRMS web origin, allowed to GET blobs through signed links.')
param vrmsWebOrigin string

var suffix = take(uniqueString(resourceGroup().id), 8)

// Logs: 30 days, and a daily cap that keeps ingestion inside the free amount
resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-welinc-${envName}'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
    workspaceCapping: { dailyQuotaGb: json('0.15') }
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
          allowedOrigins: [vrmsWebOrigin]
          allowedMethods: ['GET']
          allowedHeaders: ['*']
          exposedHeaders: ['Content-Length', 'Content-Type']
          maxAgeInSeconds: 600
        }
      ]
    }
  }
}

resource attachments 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: 'vrms-attachments'
  properties: {
    publicAccess: 'None'
  }
}

resource cae 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-welinc-${envName}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}

// The key is read here and never stored anywhere else (Value sourcing: auth file share)
resource authFiles 'Microsoft.App/managedEnvironments/storages@2024-03-01' = {
  parent: cae
  name: 'auth-uploads'
  properties: {
    azureFile: {
      accountName: files.name
      accountKey: files.listKeys().keys[0].value
      shareName: authShare.name
      accessMode: 'ReadWrite'
    }
  }
}

// Every app and job pulls images with this one identity (AcrPull on the shared registry)
resource pull 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-welinc-${envName}-pull'
  location: location
}

output environmentId string = cae.id
output environmentName string = cae.name
output defaultDomain string = cae.properties.defaultDomain
output staticIp string = cae.properties.staticIp
output customDomainVerificationId string = cae.properties.customDomainConfiguration.customDomainVerificationId
output authFilesStorageName string = authFiles.name
output blobAccountName string = blobs.name
output blobEndpoint string = 'https://${blobs.name}.blob.${environment().suffixes.storage}'
output pullIdentityId string = pull.id
output pullIdentityName string = pull.name
output pullPrincipalId string = pull.properties.principalId
