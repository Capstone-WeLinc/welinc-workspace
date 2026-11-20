// VRMS spec 0025, AC-13: platform alerts per environment, emailed to alertEmail. Sentry covers the
// apps' own errors; these cover the database and the containers.

param envName string
param alertEmail string
param postgresServerName string
@description('Deployed Container App names (with their -<env> ending) to watch for restart loops')
param appNames array

var tags = { system: 'welinc', env: envName }

resource email 'Microsoft.Insights/actionGroups@2023-01-01' = {
  name: 'ag-welinc-${envName}'
  location: 'global'
  tags: tags
  properties: {
    groupShortName: 'welinc-${take(envName, 4)}'
    enabled: true
    emailReceivers: [
      {
        name: 'alert-email'
        emailAddress: alertEmail
        useCommonAlertSchema: true
      }
    ]
  }
}

var server = resourceId('Microsoft.DBforPostgreSQL/flexibleServers', postgresServerName)

var databaseRules = [
  { key: 'db-storage', metric: 'storage_percent', threshold: 80, what: 'Database storage above 80%' }
  { key: 'db-cpu', metric: 'cpu_percent', threshold: 85, what: 'Database CPU above 85% for 15 minutes' }
]

resource database 'Microsoft.Insights/metricAlerts@2018-03-01' = [for r in databaseRules: {
  name: 'alert-${r.key}-${envName}'
  location: 'global'
  tags: tags
  properties: {
    description: r.what
    severity: 2
    enabled: true
    scopes: [server]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          criterionType: 'StaticThresholdCriterion'
          name: r.metric
          metricNamespace: 'Microsoft.DBforPostgreSQL/flexibleServers'
          metricName: r.metric
          operator: 'GreaterThan'
          threshold: r.threshold
          timeAggregation: 'Average'
        }
      ]
    }
    actions: [{ actionGroupId: email.id }]
  }
}]

// One rule per app: a restart loop is more than 3 restarts in 15 minutes, across its replicas
resource restarts 'Microsoft.Insights/metricAlerts@2018-03-01' = [for app in appNames: {
  name: 'alert-restarts-${app}'
  location: 'global'
  tags: tags
  properties: {
    description: '${app} restarted more than 3 times in 15 minutes'
    severity: 2
    enabled: true
    scopes: [resourceId('Microsoft.App/containerApps', app)]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          criterionType: 'StaticThresholdCriterion'
          name: 'RestartCount'
          metricNamespace: 'Microsoft.App/containerApps'
          metricName: 'RestartCount'
          operator: 'GreaterThan'
          threshold: 3
          timeAggregation: 'Total'
        }
      ]
    }
    actions: [{ actionGroupId: email.id }]
  }
}]
