// One WeLinc environment (staging or production) in its own resource group (VRMS spec 0008).
// Apply with infra/scripts/apply.sh <staging|prod> [--domains]; never by hand, because the
// script passes the private secrets file and the images each app runs now.

@allowed(['staging', 'prod'])
param envName string

param location string = resourceGroup().location

@description('PostgreSQL B1ms is not offered to trial accounts in every region; may differ from location.')
param postgresLocation string = location

@description('Static Web Apps regions are limited; East Asia is the closest to the users.')
param swaLocation string = 'eastasia'

param domain string = 'welinc.app'

@description('Pass 2: bind the custom domains. Only once dns-records.sh records resolve.')
param bindDomains bool = false

@description('Set by apply.sh when the gateway managed certificate already exists, so a re-apply never unbinds it.')
param gatewayCertExists bool = false

param registryName string
param registryResourceGroup string = 'rg-welinc-shared'

@description('{app or job name, ending included: image} as each runs now (apply.sh reads them back, so an apply never rolls an app back).')
param images object = {}

@description('The one Container Apps environment both WeLinc environments run in (the trial allows one): staging makes it, production joins it (AC-23).')
param environmentName string = 'cae-welinc-staging'
param environmentResourceGroup string = 'rg-welinc-staging'

@description('Groups whose apps exist here: [] until their S11 move is ready, then vmms and bms.')
param enabledGroups array = []

@description('Per group app, non secret extras: {"vmms-backend": {"settings": {...}, "healthPath": "..."}}.')
param groupApps object = {}

@description('Staging is the demo (AC-24): keep every group app at 1 replica from the defense window until the shutdown copy (AC-16, task 19a). Back to false after task 22.')
param warmAll bool = false

@description('Staging only (suite spec 0009 AC-33): the team inbox for seed account mail, with {tag}, like team+{tag}@gmail.com. Blank leaves seed mail in the auth log.')
param seedMailRedirect string = ''

@description('Deploy login principal ids for this environment: {ours, vmms, bms}. Empty skips the role.')
param logins object = {}

@description('The Brevo SMTP login (not a secret; the key is).')
param smtpUser string = ''

@description('The private file for this environment (infra/private/<env>.json), see infra/private.example.json.')
@secure()
param secrets object

var prod = envName == 'prod'
var prefix = prod ? '' : 'staging-'
// AC-23: every app, job, environment storage and certificate ends in its environment, because
// both share one Container Apps environment and its internal domain. Never write a bare base name.
var nameSuffix = '-${envName}'
var placeholderImage = 'mcr.microsoft.com/k8se/quickstart:latest'
var registryServer = '${registryName}.azurecr.io'

// Contract 0001 section 1
var hosts = {
  api: '${prefix}api.${domain}'
  portal: '${prefix}portal.${domain}'
  vrms: '${prefix}vrms.${domain}'
  vmms: '${prefix}vmms.${domain}'
  bms: '${prefix}bms.${domain}'
}
var url = {
  api: 'https://${hosts.api}'
  portal: 'https://${hosts.portal}'
  vrms: 'https://${hosts.vrms}'
  vmms: 'https://${hosts.vmms}'
  bms: 'https://${hosts.bms}'
}
var issuer = '${url.api}/auth'
var webOrigins = '${url.portal},${url.vrms},${url.vmms},${url.bms}'

var databases = ['auth', 'vrms', 'vmms', 'bms_booking', 'bms_dispatch', 'bms_completion', 'bms_analytics']

func dbUrl(host string, db string, role string, password string) string =>
  'postgresql://${db}_${role}:${password}@${host}:5432/${db}?sslmode=require&uselibpqcompat=true'

// AC-16: production keeps every app warm; staging only the gateway and timed apps, or every app while warmAll is on
func minReplicas(prod bool, warm bool) int => prod || warm ? 1 : 0

// ---------------------------------------------------------------- foundation

module platform 'modules/platform.bicep' = {
  name: 'platform'
  params: {
    envName: envName
    location: location
    vrmsWebOrigin: url.vrms
    vmmsWebOrigin: url.vmms
    createEnvironment: !prod
    environmentName: environmentName
    environmentResourceGroup: environmentResourceGroup
  }
}

// The auth file share on the shared environment, named per environment (AC-14, AC-23)
module envStorage 'modules/env-storage.bicep' = {
  name: 'env-storage${nameSuffix}'
  scope: resourceGroup(environmentResourceGroup)
  params: {
    environmentName: platform.outputs.environmentName
    storageName: 'auth-uploads${nameSuffix}'
    filesAccountName: platform.outputs.filesAccountName
    filesResourceGroup: resourceGroup().name
    shareName: platform.outputs.authShareName
    lock: prod
  }
}

module pullRole 'modules/acr-pull.bicep' = {
  name: 'acr-pull-${envName}'
  scope: resourceGroup(registryResourceGroup)
  params: {
    registryName: registryName
    principalId: platform.outputs.pullPrincipalId
  }
}

module postgres 'modules/postgres.bicep' = {
  name: 'postgres'
  params: {
    name: 'psql-welinc-${envName}'
    location: postgresLocation
    adminLogin: 'welincadmin'
    adminPassword: secrets.postgresAdminPassword
    databases: databases
  }
}

var dbHost = 'psql-welinc-${envName}.postgres.database.azure.com'
var internal = 'internal.${platform.outputs.defaultDomain}'

// Base names (contract 0001 section 2); the deployed names add nameSuffix
var coreApps = ['api-gateway', 'auth-service', 'vrms-backend']
var coreJobs = ['auth-migrate', 'auth-seed', 'vrms-migrate', 'vrms-seed']

// https://<app name with its ending>.internal.<environment domain> (spec 0008, Internal addresses)
func internalUrl(base string, nameSuffix string, internal string) string => 'https://${base}${nameSuffix}.${internal}'

var authInternal = internalUrl('auth-service', nameSuffix, internal)

// A group that isn't in enabledGroups gets a .invalid host (RFC 2606, never resolves). Every
// *.internal name resolves to the environment's shared ingress, which answers a missing app with
// its own 404 page; a failed lookup instead gives the gateway's 502 UPSTREAM_UNAVAILABLE (AC-19).
func groupUpstream(group string, base string, enabled array, nameSuffix string, internal string) string =>
  contains(enabled, group) ? internalUrl(base, nameSuffix, internal) : 'http://${base}.invalid'

// ---------------------------------------------------------------- shared services and VRMS

// VRMS spec 0025: DSNs are public values (they can only send events), so they are plain settings.
// Blank in the private file means Sentry off for that app (AC-14). SENTRY_TEST_ROUTES is never set
// here: staging is the demo (spec 0008 AC-24), so its test routes stay off.
var sentryDsn = secrets.?sentry.?dsn ?? {}
var sentryEnvironment = prod ? 'production' : 'staging'

var authSettings = {
  NODE_ENV: 'production'
  AUTH_ISSUER: issuer
  PORTAL_URL: url.portal
  CORS_ORIGINS: webOrigins
  SSO_COOKIE_SECURE: 'true'
  TRUST_PROXY_HOPS: '2'
  DB_POOL_MAX: '3'
  ADMIN_SIGN_IN_CODE: 'true'
  // API docs at /auth/docs on staging only, worked out here so no parameter can turn them on in prod (VRMS spec 0026)
  API_DOCS_ENABLED: prod ? 'false' : 'true'
  SMTP_HOST: 'smtp-relay.brevo.com'
  SMTP_PORT: '587'
  SMTP_USER: smtpUser
  SMTP_FROM: 'WeLinc <noreply@${domain}>'
  SENTRY_DSN: sentryDsn.?auth ?? ''
  SENTRY_ENVIRONMENT: sentryEnvironment
}
var authSecrets = {
  AUTH_SIGNING_KEYS: secrets.auth.signingKeys
  SMTP_PASS: secrets.auth.smtpPass
}

var vrmsSettings = {
  NODE_ENV: 'production'
  AUTH_CLIENT_ID: 'vrms'
  AUTH_INTERNAL_URL: authInternal
  // VRMS spec 0029: calls to VMMS and BMS go through the gateway. Its ingress is external, so
  // inside the environment it answers at its own name without the .internal part
  SUITE_GATEWAY_INTERNAL_URL: 'https://api-gateway${nameSuffix}.${platform.outputs.defaultDomain}'
  AUTH_JWKS_URL: '${authInternal}/auth/.well-known/jwks.json'
  AUTH_ISSUER: issuer
  AUTH_PUBLIC_URL: issuer
  API_PUBLIC_URL: url.api
  WEB_APP_URL: url.vrms
  PORTAL_URL: url.portal
  CORS_ORIGINS: url.vrms
  SESSION_COOKIE_SECURE: 'true'
  TRUST_PROXY_HOPS: '2'
  DB_POOL_MAX: '3'
  STORAGE_ACCOUNT_URL: platform.outputs.blobEndpoint
  STORAGE_PUBLIC_URL: platform.outputs.blobEndpoint
  STORAGE_CONTAINER: 'vrms-attachments'
  // API docs at /vrms/docs on staging only, as for auth above (VRMS spec 0026)
  API_DOCS_ENABLED: prod ? 'false' : 'true'
  SENTRY_DSN: sentryDsn.?vrmsBackend ?? ''
  SENTRY_ENVIRONMENT: sentryEnvironment
}
var vrmsSecrets = {
  AUTH_CLIENT_PRIVATE_KEY: secrets.vrms.clientPrivateKey
  GEMINI_API_KEY: secrets.vrms.?geminiApiKey ?? ''
}

var gatewaySettings = {
  AUTH_UPSTREAM: authInternal
  VRMS_UPSTREAM: internalUrl('vrms-backend', nameSuffix, internal)
  VMMS_UPSTREAM: groupUpstream('vmms', 'vmms-backend', enabledGroups, nameSuffix, internal)
  VMMS_ANALYTICS_UPSTREAM: groupUpstream('vmms', 'vmms-analytics', enabledGroups, nameSuffix, internal)
  BMS_UPSTREAM: groupUpstream('bms', 'bms-gateway', enabledGroups, nameSuffix, internal)
  ALLOWED_ORIGINS: webOrigins
  TRUST_EDGE_PROXY: '1'
  GATEWAY_HSTS: 'max-age=31536000'
  GATEWAY_RATE_PER_SECOND: '20'
  GATEWAY_RATE_BURST: '40'
  // The two browser tunnels (spec 0025, AC-4, AC-5): both or neither, the gateway refuses half
  SENTRY_DSN_VRMS_WEB: sentryDsn.?vrmsWeb ?? ''
  SENTRY_DSN_PORTAL: sentryDsn.?portal ?? ''
}

module auth 'modules/container-app.bicep' = {
  name: 'app-auth-service'
  dependsOn: [pullRole]
  params: {
    name: 'auth-service${nameSuffix}'
    location: location
    environmentId: platform.outputs.environmentId
    image: images[?'auth-service${nameSuffix}'] ?? placeholderImage
    placeholderImage: placeholderImage
    port: 3001
    healthPath: '/auth/health'
    // Timed (session sweeper, temporary grant sweep); at most 1 because sign in limits are in memory
    minReplicas: minReplicas(prod, true)
    maxReplicas: 1
    cpu: '0.5'
    memory: '1Gi'
    // Suite spec 0009 AC-32 and AC-33: on staging, mail to seed addresses goes to the team inbox, or
    // the log while the inbox is blank; never sent to welinc.com. The app only,
    // not authSettings (the jobs share those); welinc-auth refuses it with SENTRY_ENVIRONMENT=production.
    settings: union(
      authSettings,
      prod ? {} : { SEED_MAIL_TO_LOG: 'true' },
      prod || empty(seedMailRedirect) ? {} : { SEED_MAIL_REDIRECT: seedMailRedirect }
    )
    secretSettings: union(authSecrets, {
      DATABASE_URL: dbUrl(dbHost, 'auth', 'app', secrets.roles.auth.app)
    })
    registryServer: registryServer
    pullIdentityId: platform.outputs.pullIdentityId
    fileMount: {
      storageName: envStorage.outputs.name
      mountPath: '/app/uploads'
    }
  }
}

module vrms 'modules/container-app.bicep' = {
  name: 'app-vrms-backend'
  dependsOn: [pullRole]
  params: {
    name: 'vrms-backend${nameSuffix}'
    location: location
    environmentId: platform.outputs.environmentId
    image: images[?'vrms-backend${nameSuffix}'] ?? placeholderImage
    placeholderImage: placeholderImage
    port: 3002
    healthPath: '/vrms/health'
    // Timed: the directory poll, the matrix sync, the attachment sweep
    minReplicas: minReplicas(prod, true)
    maxReplicas: 2
    cpu: '0.5'
    memory: '1Gi'
    settings: vrmsSettings
    secretSettings: union(vrmsSecrets, {
      DATABASE_URL: dbUrl(dbHost, 'vrms', 'app', secrets.roles.vrms.app)
    })
    registryServer: registryServer
    pullIdentityId: platform.outputs.pullIdentityId
    systemIdentity: true
  }
}

// The two step binding: a host name first goes on with bindingType Disabled, the managed
// certificate is issued, then it switches to SniEnabled. A re-apply with the certificate in
// place skips straight to SniEnabled, so the gateway never loses its certificate.
var certName = 'cert-api${nameSuffix}'
var certId = '${platform.outputs.environmentId}/managedCertificates/${certName}'

module gatewayBind 'modules/container-app.bicep' = if (bindDomains && !gatewayCertExists) {
  name: 'app-api-gateway-bind'
  dependsOn: [pullRole]
  params: {
    name: 'api-gateway${nameSuffix}'
    location: location
    environmentId: platform.outputs.environmentId
    image: images[?'api-gateway${nameSuffix}'] ?? placeholderImage
    placeholderImage: placeholderImage
    port: 3000
    healthPath: '/health'
    external: true
    minReplicas: 1
    maxReplicas: 2
    settings: gatewaySettings
    registryServer: registryServer
    pullIdentityId: platform.outputs.pullIdentityId
    customDomain: { name: hosts.api, bindingType: 'Disabled', certificateId: '' }
  }
}

// On the shared environment, so in its resource group; the deployment name carries the environment
module gatewayCert 'modules/managed-cert.bicep' = if (bindDomains && !gatewayCertExists) {
  name: certName
  scope: resourceGroup(environmentResourceGroup)
  dependsOn: [gatewayBind]
  params: {
    environmentName: platform.outputs.environmentName
    location: location
    hostName: hosts.api
    name: certName
  }
}

module gateway 'modules/container-app.bicep' = {
  name: 'app-api-gateway'
  dependsOn: [pullRole, gatewayCert]
  params: {
    name: 'api-gateway${nameSuffix}'
    location: location
    environmentId: platform.outputs.environmentId
    image: images[?'api-gateway${nameSuffix}'] ?? placeholderImage
    placeholderImage: placeholderImage
    port: 3000
    healthPath: '/health'
    external: true
    minReplicas: 1
    maxReplicas: 2
    settings: gatewaySettings
    registryServer: registryServer
    pullIdentityId: platform.outputs.pullIdentityId
    customDomain: bindDomains ? { name: hosts.api, bindingType: 'SniEnabled', certificateId: certId } : {}
  }
}

// Jobs run from the seed image of a commit, started by deploy.yml or by hand
var seedAllow = prod ? {} : { SEED_ALLOW: 'staging' }

module authMigrate 'modules/job.bicep' = {
  name: 'job-auth-migrate'
  dependsOn: [pullRole]
  params: {
    location: location
    environmentId: platform.outputs.environmentId
    registryServer: registryServer
    pullIdentityId: platform.outputs.pullIdentityId
    name: 'auth-migrate${nameSuffix}'
    image: images[?'auth-migrate${nameSuffix}'] ?? placeholderImage
    settings: authSettings
    secretSettings: union(authSecrets, {
      DATABASE_URL: dbUrl(dbHost, 'auth', 'owner', secrets.roles.auth.owner)
    })
  }
}

module authSeed 'modules/job.bicep' = {
  name: 'job-auth-seed'
  dependsOn: [pullRole]
  params: {
    location: location
    environmentId: platform.outputs.environmentId
    registryServer: registryServer
    pullIdentityId: platform.outputs.pullIdentityId
    name: 'auth-seed${nameSuffix}'
    image: images[?'auth-seed${nameSuffix}'] ?? placeholderImage
    settings: union(authSettings, seedAllow, {
      API_PUBLIC_URL: url.api
      CLIENT_VRMS_WEB_ADDRESS: url.vrms
      CLIENT_VMMS_WEB_ADDRESS: url.vmms
      CLIENT_BMS_WEB_ADDRESS: url.bms
    })
    secretSettings: union(authSecrets, {
      DATABASE_URL: dbUrl(dbHost, 'auth', 'app', secrets.roles.auth.app)
      CLIENT_VRMS_JWKS: secrets.clients.?vrms ?? ''
      CLIENT_VMMS_JWKS: secrets.clients.?vmms ?? ''
      CLIENT_BMS_JWKS: secrets.clients.?bms ?? ''
      CLIENT_VMMS_ANALYTICS_JWKS: secrets.clients.?vmmsAnalytics ?? ''
      CLIENT_BMS_ANALYTICS_JWKS: secrets.clients.?bmsAnalytics ?? ''
    })
  }
}

module vrmsMigrate 'modules/job.bicep' = {
  name: 'job-vrms-migrate'
  dependsOn: [pullRole]
  params: {
    location: location
    environmentId: platform.outputs.environmentId
    registryServer: registryServer
    pullIdentityId: platform.outputs.pullIdentityId
    name: 'vrms-migrate${nameSuffix}'
    image: images[?'vrms-migrate${nameSuffix}'] ?? placeholderImage
    settings: vrmsSettings
    secretSettings: union(vrmsSecrets, {
      DATABASE_URL: dbUrl(dbHost, 'vrms', 'owner', secrets.roles.vrms.owner)
    })
  }
}

// Owner role: the full staging seed switches the audit_logs triggers off for its reset, which
// only the table owner may do. --reference on production writes no audit rows.
module vrmsSeed 'modules/job.bicep' = {
  name: 'job-vrms-seed'
  dependsOn: [pullRole]
  params: {
    location: location
    environmentId: platform.outputs.environmentId
    registryServer: registryServer
    pullIdentityId: platform.outputs.pullIdentityId
    name: 'vrms-seed${nameSuffix}'
    image: images[?'vrms-seed${nameSuffix}'] ?? placeholderImage
    settings: union(vrmsSettings, seedAllow)
    secretSettings: union(vrmsSecrets, {
      DATABASE_URL: dbUrl(dbHost, 'vrms', 'owner', secrets.roles.vrms.owner)
    })
  }
}

// ---------------------------------------------------------------- VMMS and BMS

// From contract 0001 sections 2 and 3. Each group confirms its own in docs/integration/hosting.md;
// groupApps overrides the health path and adds settings. edge: receives traffic through the suite
// gateway (TRUST_PROXY_HOPS=2). database: '' for none.
var groupDefs = {
  vmms: {
    web: 'vmms'
    apps: [
      // blob: its own container (vmms-attachments) with signed links; docIntel: fuel receipt scanning
      { group: 'vmms', name: 'vmms-backend', port: 3010, healthPath: '/vmms/health', database: 'vmms', timed: true, maxReplicas: 2, edge: true, ingress: true, blob: true, docIntel: true }
      { group: 'vmms', name: 'vmms-analytics', port: 3011, healthPath: '/vmms/analytics/health', database: 'vmms', timed: true, maxReplicas: 1, edge: true, ingress: true }
    ]
    jobs: [
      { group: 'vmms', name: 'vmms-migrate', app: 'vmms-backend', database: 'vmms' }
      // Analytics' own migration (the vector extension and the notify triggers): npm run migrate -- --skip-embeddings
      { group: 'vmms', name: 'vmms-analytics-migrate', app: 'vmms-analytics', database: 'vmms' }
    ]
  }
  bms: {
    web: 'bms'
    apps: [
      { group: 'bms', name: 'bms-gateway', port: 3020, healthPath: '/bms/health', database: '', timed: false, maxReplicas: 1, edge: true, ingress: true }
      // timed: booking flushes its approvals outbox every 5 s; dispatch syncs erased trucks from VMMS daily
      { group: 'bms', name: 'bms-booking', port: 3021, healthPath: '/health/ready', database: 'bms_booking', timed: true, maxReplicas: 1, edge: false, ingress: true }
      { group: 'bms', name: 'bms-dispatch', port: 3022, healthPath: '/health/ready', database: 'bms_dispatch', timed: true, maxReplicas: 1, edge: false, ingress: true }
      { group: 'bms', name: 'bms-completion', port: 3023, healthPath: '/health/ready', database: 'bms_completion', timed: false, maxReplicas: 1, edge: false, ingress: true }
      { group: 'bms', name: 'bms-analytics-projection', port: 3024, healthPath: '', database: 'bms_analytics', timed: true, maxReplicas: 1, edge: false, ingress: false }
      { group: 'bms', name: 'bms-analytics', port: 3025, healthPath: '/health/ready', database: 'bms_analytics', timed: false, maxReplicas: 1, edge: false, ingress: true }
    ]
    jobs: [
      { group: 'bms', name: 'bms-booking-migrate', app: 'bms-booking', database: 'bms_booking' }
      { group: 'bms', name: 'bms-dispatch-migrate', app: 'bms-dispatch', database: 'bms_dispatch' }
      { group: 'bms', name: 'bms-completion-migrate', app: 'bms-completion', database: 'bms_completion' }
      { group: 'bms', name: 'bms-analytics-migrate', app: 'bms-analytics', database: 'bms_analytics' }
    ]
  }
}

var groupAppList = flatten(map(enabledGroups, g => groupDefs[g].apps))
var groupJobList = flatten(map(enabledGroups, g => groupDefs[g].jobs))

// What every group service gets without asking (contract 0001 section 15)
func groupCommon(a object, url object, issuer string, authInternal string) object => union(
  {
    NODE_ENV: 'production'
    DB_POOL_MAX: '2'
    AUTH_ISSUER: issuer
    AUTH_INTERNAL_URL: authInternal
    AUTH_JWKS_URL: '${authInternal}/auth/.well-known/jwks.json'
    AUTH_PUBLIC_URL: issuer
    API_PUBLIC_URL: url.api
    PORTAL_URL: url.portal
    WEB_APP_URL: url[a.group]
    SESSION_COOKIE_SECURE: 'true'
  },
  a.edge ? { TRUST_PROXY_HOPS: '2' } : {}
)

module groupApp 'modules/container-app.bicep' = [for a in groupAppList: {
  name: 'app-${a.name}'
  dependsOn: [pullRole]
  params: {
    name: '${a.name}${nameSuffix}'
    location: location
    environmentId: platform.outputs.environmentId
    image: images[?'${a.name}${nameSuffix}'] ?? placeholderImage
    placeholderImage: placeholderImage
    port: a.port
    healthPath: groupApps[?a.name].?healthPath ?? a.healthPath
    ingress: a.ingress
    minReplicas: minReplicas(prod || warmAll, a.timed)
    maxReplicas: a.maxReplicas
    // Its own identity, for Blob Storage and Document Intelligence (no keys in settings)
    systemIdentity: (a.?blob ?? false) || (a.?docIntel ?? false)
    settings: union(
      groupCommon(a, url, issuer, authInternal),
      (a.?blob ?? false) ? {
        STORAGE_ACCOUNT_URL: platform.outputs.blobEndpoint
        STORAGE_PUBLIC_URL: platform.outputs.blobEndpoint
        STORAGE_CONTAINER: '${a.group}-attachments'
      } : {},
      // VMMS's own setting name; no key: the app signs in with its identity (Cognitive Services User)
      (a.?docIntel ?? false) ? { AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: docIntel.outputs.endpoint } : {},
      groupApps[?a.name].?settings ?? {}
    )
    secretSettings: union(
      empty(a.database) ? {} : { DATABASE_URL: dbUrl(dbHost, a.database, 'app', secrets.roles[a.database].app) },
      secrets.?groups[?a.name] ?? {}
    )
    registryServer: registryServer
    pullIdentityId: platform.outputs.pullIdentityId
  }
}]

module groupJob 'modules/job.bicep' = [for j in groupJobList: {
  name: 'job-${j.name}'
  dependsOn: [pullRole]
  params: {
    location: location
    environmentId: platform.outputs.environmentId
    registryServer: registryServer
    pullIdentityId: platform.outputs.pullIdentityId
    name: '${j.name}${nameSuffix}'
    image: images[?'${j.name}${nameSuffix}'] ?? placeholderImage
    // The same settings as the app it migrates, plus the staging seed switch: the lead starts this
    // job once with the group's seed command to seed staging (spec 0008, Seed and bootstrap jobs)
    settings: union(
      groupCommon(filter(groupAppList, a => a.name == j.app)[0], url, issuer, authInternal),
      groupApps[?j.app].?settings ?? {},
      seedAllow
    )
    secretSettings: union(
      { DATABASE_URL: dbUrl(dbHost, j.database, 'owner', secrets.roles[j.database].owner) },
      secrets.?groups[?j.app] ?? {}
    )
  }
}]

// ---------------------------------------------------------------- web apps

var webs = ['portal', 'vrms', 'vmms', 'bms']

module web 'modules/static-web-app.bicep' = [for w in webs: {
  name: 'web-${w}'
  params: {
    name: 'swa-welinc-${envName}-${w}'
    location: swaLocation
    customDomain: bindDomains ? hosts[w] : ''
  }
}]

// ---------------------------------------------------------------- access

var suffix = take(uniqueString(resourceGroup().id), 8)

resource blobAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: 'st${suffix}blob'
}

var blobContributor = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
// Only lets an identity ask for a user delegation key (to sign links); Azure accepts it at the
// account level only, so it carries no access to any blob by itself
var blobDelegator = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'db58b8e5-c6ad-4a2a-8342-4190687cbf4a')
var cognitiveUser = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908')

// Each system's backend reads and writes its own container only, and signs links for it
// (spec 0017). Narrowed from the whole account on 2026-11-21, when VMMS got a container too.
resource vrmsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' existing = {
  name: '${blobAccount.name}/default/vrms-attachments'
}

resource vrmsBlob 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: vrmsContainer
  // Keyed on the suffixed app: a recreated app has a new identity, and an assignment's principal can't change
  name: guid(vrmsContainer.id, 'vrms-backend${nameSuffix}', blobContributor)
  properties: {
    roleDefinitionId: blobContributor
    principalId: vrms.outputs.principalId
    principalType: 'ServicePrincipal'
  }
}

resource vrmsDelegator 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: blobAccount
  name: guid(blobAccount.id, 'vrms-backend${nameSuffix}', blobDelegator)
  properties: {
    roleDefinitionId: blobDelegator
    principalId: vrms.outputs.principalId
    principalType: 'ServicePrincipal'
  }
}

// Document Intelligence (VMMS fuel receipt scanning). Made even before VMMS is enabled, so its
// developers can test against it locally; its role assignment waits for the VMMS app below.
module docIntel 'modules/document-intelligence.bicep' = {
  name: 'document-intelligence${nameSuffix}'
  params: {
    name: 'di-welinc-${envName}-${suffix}'
    location: location
    sku: prod ? 'S0' : 'F0'
  }
}

resource docIntelAccount 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: 'di-welinc-${envName}-${suffix}'
}

// The same access for an enabled group's app that asks for it (groupDefs: blob, docIntel)
resource groupContainers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' existing = [for a in groupAppList: {
  name: '${blobAccount.name}/default/${a.group}-attachments'
}]

resource groupBlob 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (a, i) in groupAppList: if (a.?blob ?? false) {
  scope: groupContainers[i]
  name: guid(groupContainers[i].id, '${a.name}${nameSuffix}', blobContributor)
  properties: {
    roleDefinitionId: blobContributor
    principalId: groupApp[i].outputs.principalId
    principalType: 'ServicePrincipal'
  }
}]

resource groupDelegator 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (a, i) in groupAppList: if (a.?blob ?? false) {
  scope: blobAccount
  name: guid(blobAccount.id, '${a.name}${nameSuffix}', blobDelegator)
  properties: {
    roleDefinitionId: blobDelegator
    principalId: groupApp[i].outputs.principalId
    principalType: 'ServicePrincipal'
  }
}]

resource groupDocIntel 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (a, i) in groupAppList: if (a.?docIntel ?? false) {
  scope: docIntelAccount
  name: guid(docIntelAccount.id, '${a.name}${nameSuffix}', cognitiveUser)
  properties: {
    roleDefinitionId: cognitiveUser
    principalId: groupApp[i].outputs.principalId
    principalType: 'ServicePrincipal'
  }
}]

var contributor = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b24988ac-6180-42a0-ab88-20f7382dd24c')

// Our deploy login: Contributor on this environment's resource group only (AcrPush is in shared)
resource oursRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(logins.?ours ?? '')) {
  name: guid(resourceGroup().id, logins.?ours ?? 'none', contributor)
  properties: {
    roleDefinitionId: contributor
    principalId: logins.?ours ?? ''
    principalType: 'ServicePrincipal'
  }
}

var groupsWithLogin = filter(enabledGroups, g => !empty(logins[?g] ?? ''))

module groupAccess 'modules/group-access.bicep' = [for g in groupsWithLogin: {
  name: 'access-${g}'
  dependsOn: [groupApp, groupJob, web]
  params: {
    group: g
    envName: envName
    principalId: logins[g]
    appNames: map(groupDefs[g].apps, a => '${a.name}${nameSuffix}')
    jobNames: map(groupDefs[g].jobs, j => '${j.name}${nameSuffix}')
    webNames: ['swa-welinc-${envName}-${groupDefs[g].web}']
    environmentName: platform.outputs.environmentName
    pullIdentityName: platform.outputs.pullIdentityName
    joinEnvironment: !prod
  }
}]

// Production on the shared environment: the joiner role for every production login, and the
// delete locks (AC-11, AC-23). The certificate lock waits until the certificate exists (pass 2).
module envGuard 'modules/env-guard.bicep' = if (prod) {
  name: 'env-guard${nameSuffix}'
  scope: resourceGroup(environmentResourceGroup)
  dependsOn: [gateway, envStorage]
  params: {
    environmentName: platform.outputs.environmentName
    principalIds: filter(map(['ours', 'vmms', 'bms'], w => logins[?w] ?? ''), p => !empty(p))
    certName: bindDomains ? certName : ''
  }
}

// VRMS spec 0025, AC-13: database storage and CPU, and a restart loop on any app, emailed to the
// private file's alertEmail. Skipped when the file has no alertEmail.
module alerts 'modules/alerts.bicep' = if (!empty(secrets.?alertEmail ?? '')) {
  name: 'alerts${nameSuffix}'
  dependsOn: [auth, vrms, gateway, groupApp]
  params: {
    envName: envName
    alertEmail: secrets.?alertEmail ?? ''
    postgresServerName: postgres.outputs.name
    appNames: map(concat(coreApps, map(groupAppList, a => a.name)), n => '${n}${nameSuffix}')
  }
}

// ---------------------------------------------------------------- outputs (read by the scripts)

output hosts object = hosts
output environmentDefaultDomain string = platform.outputs.defaultDomain
output customDomainVerificationId string = platform.outputs.customDomainVerificationId
output gatewayFqdn string = gateway.outputs.fqdn
output postgresFqdn string = postgres.outputs.fqdn
output webDefaultHostnames array = [for (w, i) in webs: {
  web: w
  defaultHostname: web[i].outputs.defaultHostname
}]
output webNames object = toObject(webs, w => w, w => 'swa-welinc-${envName}-${w}')
output nameSuffix string = nameSuffix
output appNames array = map(concat(coreApps, map(groupAppList, a => a.name)), n => '${n}${nameSuffix}')
output jobNames array = map(concat(coreJobs, map(groupJobList, j => j.name)), n => '${n}${nameSuffix}')
output resourceGroup string = resourceGroup().name
