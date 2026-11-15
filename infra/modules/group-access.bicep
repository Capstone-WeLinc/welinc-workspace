// A VMMS or BMS deploy login (AC-11): Reader on the resource group, and a custom role on its own
// apps, jobs and Static Web Apps only, plus the environment and the pull identity it must use.
// It never gets rights on another group's apps, on the shared services or on VRMS.

param group string
param envName string
param principalId string
param appNames array
param jobNames array
param webNames array
param environmentName string
param pullIdentityName string

var reader = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'acdd72a7-3385-48ef-bd42-f606fba81ae7')

resource deployer 'Microsoft.Authorization/roleDefinitions@2022-04-01' = {
  name: guid(resourceGroup().id, 'welinc-deployer', group)
  properties: {
    roleName: 'WeLinc ${group} deployer (${envName})'
    description: 'Updates and starts the ${group} apps and jobs in ${envName}, nothing else.'
    type: 'CustomRole'
    assignableScopes: [resourceGroup().id]
    permissions: [
      {
        actions: [
          'Microsoft.App/containerApps/read'
          'Microsoft.App/containerApps/write'
          'Microsoft.App/containerApps/listSecrets/action'
          'Microsoft.App/containerApps/*/read'
          'Microsoft.App/containerApps/revisions/restart/action'
          'Microsoft.App/jobs/read'
          'Microsoft.App/jobs/write'
          'Microsoft.App/jobs/start/action'
          'Microsoft.App/jobs/stop/action'
          'Microsoft.App/jobs/listSecrets/action'
          'Microsoft.App/jobs/*/read'
          'Microsoft.App/managedEnvironments/read'
          'Microsoft.App/managedEnvironments/join/action'
          'Microsoft.ManagedIdentity/userAssignedIdentities/read'
          'Microsoft.ManagedIdentity/userAssignedIdentities/assign/action'
          'Microsoft.Web/staticSites/read'
          'Microsoft.Web/staticSites/listSecrets/action'
        ]
        notActions: []
      }
    ]
  }
}

resource readRg 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, principalId, reader)
  properties: {
    roleDefinitionId: reader
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

resource apps 'Microsoft.App/containerApps@2024-03-01' existing = [for n in appNames: {
  name: n
}]

resource jobs 'Microsoft.App/jobs@2024-03-01' existing = [for n in jobNames: {
  name: n
}]

resource webs 'Microsoft.Web/staticSites@2023-12-01' existing = [for n in webNames: {
  name: n
}]

resource env 'Microsoft.App/managedEnvironments@2024-03-01' existing = {
  name: environmentName
}

resource pullIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: pullIdentityName
}

resource onApps 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (n, i) in appNames: {
  scope: apps[i]
  name: guid(apps[i].id, principalId, deployer.id)
  properties: {
    roleDefinitionId: deployer.id
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}]

resource onJobs 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (n, i) in jobNames: {
  scope: jobs[i]
  name: guid(jobs[i].id, principalId, deployer.id)
  properties: {
    roleDefinitionId: deployer.id
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}]

resource onWebs 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (n, i) in webNames: {
  scope: webs[i]
  name: guid(webs[i].id, principalId, deployer.id)
  properties: {
    roleDefinitionId: deployer.id
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}]

resource onEnv 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: env
  name: guid(env.id, principalId, deployer.id)
  properties: {
    roleDefinitionId: deployer.id
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

resource onPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: pullIdentity
  name: guid(pullIdentity.id, principalId, deployer.id)
  properties: {
    roleDefinitionId: deployer.id
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}
