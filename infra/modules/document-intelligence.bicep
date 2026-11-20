// Azure AI Document Intelligence for VMMS fuel receipt scanning (its prebuilt receipt model).
// The VMMS backend calls it with its own identity (Cognitive Services User, env.bicep, access).
// Keys stay on so a developer can test against it locally; a key lives in a local .env only.

param name string
param location string

@description('F0 is the free tier: one per subscription, so staging takes it and production uses S0.')
@allowed(['F0', 'S0'])
param sku string

resource docIntel 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: name
  location: location
  kind: 'FormRecognizer'
  sku: { name: sku }
  properties: {
    // A custom subdomain is required for Microsoft Entra (managed identity) calls
    customSubDomainName: name
    publicNetworkAccess: 'Enabled'
  }
}

output name string = docIntel.name
output id string = docIntel.id
output endpoint string = docIntel.properties.endpoint
