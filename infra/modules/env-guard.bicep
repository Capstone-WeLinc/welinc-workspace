// What production adds to the shared Container Apps environment (spec 0008, AC-11, AC-23), applied
// by production's apply.sh into rg-welinc-staging:
//   - the custom role "WeLinc environment joiner": place and update apps in the environment, read
//     its storages, never change or delete it; given on the environment to every production login
//   - CanNotDelete locks on the environment and on production's certificate, so nothing removes
//     what production runs on while it runs. A lock on the environment also covers everything
//     under it (every certificate and storage), so deleting one of staging's means lifting that
//     lock first (infra/README.md, Shared environment)

param environmentName string

@description('The production deploy logins (ours and every group that has one).')
param principalIds array

@description('cert-api-prod, or empty while production has no certificate yet (pass 1).')
param certName string = ''

resource cae 'Microsoft.App/managedEnvironments@2024-03-01' existing = {
  name: environmentName
}

resource joiner 'Microsoft.Authorization/roleDefinitions@2022-04-01' = {
  name: guid(resourceGroup().id, 'welinc-environment-joiner')
  properties: {
    roleName: 'WeLinc environment joiner'
    description: 'Places and updates apps and jobs in the shared Container Apps environment. Cannot change or delete it.'
    type: 'CustomRole'
    assignableScopes: [resourceGroup().id]
    permissions: [
      {
        actions: [
          'Microsoft.App/managedEnvironments/read'
          'Microsoft.App/managedEnvironments/join/action'
          'Microsoft.App/managedEnvironments/storages/read'
        ]
        notActions: []
      }
    ]
  }
}

resource onEnv 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for p in principalIds: {
  scope: cae
  name: guid(cae.id, p, joiner.id)
  properties: {
    roleDefinitionId: joiner.id
    principalId: p
    principalType: 'ServicePrincipal'
  }
}]

resource envLock 'Microsoft.Authorization/locks@2020-05-01' = {
  scope: cae
  name: 'keep-${environmentName}'
  properties: {
    level: 'CanNotDelete'
    notes: 'Production runs in this environment (spec 0008 AC-23). Never delete it, or rg-welinc-staging, while production runs.'
  }
}

resource cert 'Microsoft.App/managedEnvironments/managedCertificates@2024-03-01' existing = if (!empty(certName)) {
  parent: cae
  name: empty(certName) ? 'none' : certName
}

resource certLock 'Microsoft.Authorization/locks@2020-05-01' = if (!empty(certName)) {
  scope: cert
  name: 'keep-${certName}'
  properties: {
    level: 'CanNotDelete'
    notes: 'The production gateway certificate (spec 0008 AC-23).'
  }
}
