// One Static Web App, Free plan (spec 0008). Deployed from GitHub Actions with the deployment
// token read at run time, so no repository link here.

param name string

@description('Static Web Apps live in a few regions only; the CDN serves everywhere.')
param location string

@description('Custom host name to bind, or empty for none (pass 1).')
param customDomain string = ''

resource site 'Microsoft.Web/staticSites@2023-12-01' = {
  name: name
  location: location
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    allowConfigFileUpdates: true
    stagingEnvironmentPolicy: 'Disabled'
  }
}

// CNAME validation: the record must point at the default host name before pass 2
resource domain 'Microsoft.Web/staticSites/customDomains@2023-12-01' = if (!empty(customDomain)) {
  parent: site
  name: empty(customDomain) ? 'none' : customDomain
  properties: {
    validationMethod: 'cname-delegation'
  }
}

output name string = site.name
output defaultHostname string = site.properties.defaultHostname
