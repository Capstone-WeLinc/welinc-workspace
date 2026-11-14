// One PostgreSQL Flexible Server per environment with its seven databases (spec 0008, Database).
// Roles, ownership and grants are not ARM resources: infra/db/init.sql makes them after this.

param name string
param location string
param adminLogin string

@secure()
param adminPassword string

param databases array

resource server 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: name
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '16'
    administratorLogin: adminLogin
    administratorLoginPassword: adminPassword
    storage: {
      storageSizeGB: 32
      autoGrow: 'Disabled'
    }
    backup: {
      backupRetentionDays: 14
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    network: {
      publicNetworkAccess: 'Enabled'
    }
    authConfig: {
      activeDirectoryAuth: 'Disabled'
      passwordAuth: 'Enabled'
    }
  }
}

// "Allow Azure services" only (spec 0008, Network). Laptop work adds a temporary rule.
resource azureServices 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2024-08-01' = {
  parent: server
  name: 'AllowAllAzureServicesAndResourcesWithinAzureIps'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// One at a time: the server refuses parallel configuration changes.
// VECTOR for the VRMS embeddings (spec 0013), PG_TRGM for the VRMS baseline migration.
resource extensions 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2024-08-01' = {
  parent: server
  name: 'azure.extensions'
  properties: {
    value: 'VECTOR,PG_TRGM'
    source: 'user-override'
  }
  dependsOn: [azureServices]
}

// A transaction left open holds back the directory feed for every system (suite spec 0005)
resource idleTimeout 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2024-08-01' = {
  parent: server
  name: 'idle_in_transaction_session_timeout'
  properties: {
    value: '60000'
    source: 'user-override'
  }
  dependsOn: [extensions]
}

@batchSize(1)
resource dbs 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = [for db in databases: {
  parent: server
  name: db
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
  dependsOn: [idleTimeout]
}]

output name string = server.name
output fqdn string = server.properties.fullyQualifiedDomainName
