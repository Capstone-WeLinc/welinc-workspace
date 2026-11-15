// One Container App (VRMS spec 0008). Every service of every group, the gateway included, goes
// through this module so ports, probes, replicas and secrets follow one rule.

@description('App name, also its internal host name.')
param name string
param location string
param environmentId string

@description('Image to run. The placeholder image means "nothing deployed yet": it listens on 80 and gets no probes.')
param image string
param placeholderImage string

@description('The port the app reads from PORT; ingress targetPort equals it (spec 0008, Network).')
param port int

@description('Startup and readiness probe path, for example /auth/health.')
param healthPath string

@description('Only the gateway is public.')
param external bool = false

@description('False for a worker that serves no HTTP (it gets no ingress and no probes).')
param ingress bool = true

param minReplicas int
param maxReplicas int
param cpu string = '0.25'
param memory string = '0.5Gi'

@description('Plain settings as {NAME: value}.')
param settings object = {}

@description('Secret settings as {NAME: value}. Each becomes a Container Apps secret and an env var reading it.')
@secure()
param secretSettings object = {}

param registryServer string
param pullIdentityId string

@description('Give the app a system assigned identity (backend-vrms uses it for Blob Storage).')
param systemIdentity bool = false

@description('Mount an environment storage (Azure Files) at a path: {storageName, mountPath} or {}.')
param fileMount object = {}

@description('Custom domain binding for the gateway: {} for none, else {name, bindingType, certificateId}.')
param customDomain object = {}

var placeholder = image == placeholderImage
var targetPort = placeholder ? 80 : port

// Container Apps secret names: lowercase letters, digits and dashes
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

// Startup allows 24 x 10 s = 240 s for boot and warm up; readiness follows on the same route.
// No liveness probe, so a database outage never restart loops the app (spec 0008, Revisions).
var probes = placeholder || !ingress ? [] : [
  {
    type: 'Startup'
    httpGet: { path: healthPath, port: port }
    periodSeconds: 10
    timeoutSeconds: 3
    failureThreshold: 24
  }
  {
    type: 'Readiness'
    httpGet: { path: healthPath, port: port }
    periodSeconds: 10
    timeoutSeconds: 3
    failureThreshold: 3
  }
]

var mounted = !empty(fileMount)
var identityType = systemIdentity ? 'SystemAssigned,UserAssigned' : 'UserAssigned'

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  identity: {
    type: identityType
    userAssignedIdentities: {
      '${pullIdentityId}': {}
    }
  }
  properties: {
    environmentId: environmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: !ingress ? null : {
        external: external
        targetPort: targetPort
        transport: 'auto'
        allowInsecure: false
        customDomains: empty(customDomain) ? [] : [
          {
            name: customDomain.name
            bindingType: customDomain.bindingType
            certificateId: customDomain.bindingType == 'SniEnabled' ? customDomain.certificateId : null
          }
        ]
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
          env: concat(envPlain, envSecret, [{ name: 'PORT', value: string(port) }])
          probes: probes
          volumeMounts: mounted ? [
            {
              volumeName: 'files'
              mountPath: fileMount.mountPath
            }
          ] : []
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http'
            http: { metadata: { concurrentRequests: '50' } }
          }
        ]
      }
      volumes: mounted ? [
        {
          name: 'files'
          storageType: 'AzureFile'
          storageName: fileMount.storageName
          // The runner image runs as node (uid 1000); SMB mounts belong to root otherwise
          mountOptions: 'uid=1000,gid=1000,dir_mode=0750,file_mode=0640'
        }
      ] : []
    }
  }
}

output name string = app.name
output id string = app.id
output fqdn string = ingress ? app.properties.configuration.ingress.fqdn : ''
output principalId string = systemIdentity ? app.identity.principalId : ''
