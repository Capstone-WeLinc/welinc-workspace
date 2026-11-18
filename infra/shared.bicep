// rg-welinc-shared: the one container registry every environment and group uses (spec 0008).
// Apply: infra/scripts/apply.sh shared

param location string = resourceGroup().location

@description('Principal ids of every deploy login (ours, VMMS, BMS; staging and production). Each gets AcrPush, which also covers reading tags.')
param pushPrincipalIds array = []

@description('Principal id of the weekly image cleanup login (.github/workflows/purge-images.yml in the workspace). It gets Reader on the registry (to list repositories and tags) and AcrDelete to remove old ones, nothing else.')
param purgePrincipalId string = ''

@description('ACR Tasks can be paused on free credit subscriptions; set false and .github/workflows/purge-images.yml runs infra/scripts/purge-images.sh weekly instead.')
param purgeTask bool = true

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: 'acrwelinc${uniqueString(resourceGroup().id)}'
  location: location
  sku: { name: 'Basic' }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
}

// Keeps the newest 15 tags of every image (rollback needs the old one to exist) and removes
// untagged layers. Weekly, Sunday 03:00 UTC.
var purgeYaml = '''
version: v1.1.0
steps:
  - cmd: acr purge --filter '.*:.*' --ago 0d --keep 15 --untagged
    disableWorkingDirectoryOverride: true
    timeout: 3600
'''

resource purge 'Microsoft.ContainerRegistry/registries/tasks@2019-06-01-preview' = if (purgeTask) {
  parent: registry
  name: 'weekly-purge'
  location: location
  properties: {
    platform: { os: 'Linux', architecture: 'amd64' }
    agentConfiguration: { cpu: 2 }
    timeout: 3600
    step: {
      type: 'EncodedTask'
      encodedTaskContent: base64(purgeYaml)
    }
    trigger: {
      timerTriggers: [
        {
          name: 'weekly'
          schedule: '0 3 * * 0'
          status: 'Enabled'
        }
      ]
      baseImageTrigger: {
        name: 'none'
        baseImageTriggerType: 'Runtime'
        status: 'Disabled'
      }
    }
  }
}

var acrPush = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8311e382-0749-4cb8-b61a-304f252e45ec')

resource push 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for id in pushPrincipalIds: {
  scope: registry
  name: guid(registry.id, id, acrPush)
  properties: {
    roleDefinitionId: acrPush
    principalId: id
    principalType: 'ServicePrincipal'
  }
}]

var reader = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'acdd72a7-3385-48ef-bd42-f606fba81ae7')
var acrDelete = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'c2f4ef07-c644-48eb-af81-4b1b4947fb11')

resource purgeRoles 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for role in (empty(purgePrincipalId) ? [] : [reader, acrDelete]): {
  scope: registry
  name: guid(registry.id, purgePrincipalId, role)
  properties: {
    roleDefinitionId: role
    principalId: purgePrincipalId
    principalType: 'ServicePrincipal'
  }
}]

output registryName string = registry.name
output loginServer string = registry.properties.loginServer
