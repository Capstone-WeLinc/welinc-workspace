// A manually started Container Apps job (spec 0008, Seed and bootstrap jobs). The command and the
// image are given at start (`az containerapp job start --image --command --args`); the template
// here carries the settings and secrets the job needs.

param name string
param location string
param environmentId string
param image string
param settings object = {}

@secure()
param secretSettings object = {}

param registryServer string
param pullIdentityId string
param cpu string = '0.5'
param memory string = '1Gi'

// An empty value is skipped: Container Apps refuses an empty secret, and the app treats a
// missing optional setting (GEMINI_API_KEY, a client key not sent yet) as off
var secretItems = filter(items(secretSettings), s => !empty(s.value))
var secretList = [for s in secretItems: {
  name: toLower(replace(s.key, '_', '-'))
  value: s.value
}]
var envPlain = [for s in items(settings): {
  name: s.key
  value: string(s.value)
}]
var envSecret = [for s in secretItems: {
  name: s.key
  secretRef: toLower(replace(s.key, '_', '-'))
}]

resource job 'Microsoft.App/jobs@2024-03-01' = {
  name: name
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${pullIdentityId}': {}
    }
  }
  properties: {
    environmentId: environmentId
    configuration: {
      triggerType: 'Manual'
      replicaTimeout: 600
      replicaRetryLimit: 0
      manualTriggerConfig: {
        parallelism: 1
        replicaCompletionCount: 1
      }
      registries: [
        {
          server: registryServer
          identity: pullIdentityId
        }
      ]
      secrets: secretList
    }
    template: {
      containers: [
        {
          name: name
          image: image
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: concat(envPlain, envSecret)
        }
      ]
    }
  }
}

output name string = job.name
output id string = job.id
