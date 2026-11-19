// One WeLinc environment's file storage on the shared Container Apps environment (spec 0008,
// AC-14, AC-23): auth-uploads-staging or auth-uploads-prod, each pointing at its own environment's
// files account. Deployed into the environment's resource group (rg-welinc-staging) from either
// environment, so the module deployment name carries the environment too.

param environmentName string

@description('auth-uploads plus the environment ending.')
param storageName string

@description('The files account and its share, in the resource group of this WeLinc environment.')
param filesAccountName string
param filesResourceGroup string
param shareName string

@description('Production: a CanNotDelete lock, so nothing removes the storage production mounts.')
param lock bool = false

resource cae 'Microsoft.App/managedEnvironments@2024-03-01' existing = {
  name: environmentName
}

resource files 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: filesAccountName
  scope: resourceGroup(filesResourceGroup)
}

// The key is read here and never stored anywhere else (Value sourcing: auth file share). Rotating
// it means running apply.sh for that environment again.
resource storage 'Microsoft.App/managedEnvironments/storages@2024-03-01' = {
  parent: cae
  name: storageName
  properties: {
    azureFile: {
      accountName: files.name
      accountKey: files.listKeys().keys[0].value
      shareName: shareName
      accessMode: 'ReadWrite'
    }
  }
}

resource storageLock 'Microsoft.Authorization/locks@2020-05-01' = if (lock) {
  scope: storage
  name: 'keep-${storageName}'
  properties: {
    level: 'CanNotDelete'
    notes: 'Production mounts this storage (spec 0008 AC-23). Remove only to retire production.'
  }
}

output name string = storage.name
