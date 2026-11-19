// The gateway's Azure managed certificate (spec 0008, Custom domains in two passes). Created only
// after the host name is bound with bindingType Disabled; it renews on its own. Both WeLinc
// environments keep theirs on the one Container Apps environment: cert-api-staging, cert-api-prod.

param environmentName string
param location string
param hostName string

@description('cert-api plus the environment ending.')
param name string

resource cae 'Microsoft.App/managedEnvironments@2024-03-01' existing = {
  name: environmentName
}

resource cert 'Microsoft.App/managedEnvironments/managedCertificates@2024-03-01' = {
  parent: cae
  name: name
  location: location
  properties: {
    subjectName: hostName
    domainControlValidation: 'CNAME'
  }
}

output id string = cert.id
