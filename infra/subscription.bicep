// Subscription level: the budget that emails at $50, $100, $150 and $180 of spend (AC-12).
// Apply: infra/scripts/apply.sh budget

targetScope = 'subscription'

@description('Where the alerts go.')
param alertEmail string

@description('First day of the current month; budgets must start on one.')
param startDate string = utcNow('yyyy-MM-01')

param amount int = 200

resource budget 'Microsoft.Consumption/budgets@2023-05-01' = {
  name: 'welinc-credit'
  properties: {
    category: 'Cost'
    amount: amount
    timeGrain: 'Monthly'
    timePeriod: {
      startDate: startDate
    }
    notifications: {
      at50: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 25
        thresholdType: 'Actual'
        contactEmails: [alertEmail]
      }
      at100: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 50
        thresholdType: 'Actual'
        contactEmails: [alertEmail]
      }
      at150: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 75
        thresholdType: 'Actual'
        contactEmails: [alertEmail]
      }
      at180: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 90
        thresholdType: 'Actual'
        contactEmails: [alertEmail]
      }
    }
  }
}
