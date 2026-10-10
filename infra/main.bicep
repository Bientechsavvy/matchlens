// UNVALIDATED starter: Container App for the MatchLens API. Event Hubs, Cosmos DB and Foundry are still to add.
param location string = resourceGroup().location
param image string
param foundryEndpoint string = ''
param foundryModel string = ''

resource logs 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'matchlens-logs'
  location: location
  properties: { sku: { name: 'PerGB2018' } }
}

resource env 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'matchlens-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: { customerId: logs.properties.customerId, sharedKey: logs.listKeys().primarySharedKey }
    }
  }
}

resource app 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'matchlens-api'
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    managedEnvironmentId: env.id
    configuration: { ingress: { external: true, targetPort: 8000 } }
    template: {
      containers: [{
        name: 'api', image: image
        env: [
          { name: 'USE_LLM', value: empty(foundryEndpoint) ? 'false' : 'true' }
          { name: 'FOUNDRY_ENDPOINT', value: foundryEndpoint }
          { name: 'FOUNDRY_MODEL', value: foundryModel }
        ]
      }]
      scale: { minReplicas: 1, maxReplicas: 3 }
    }
  }
}

output url string = 'https://${app.properties.configuration.ingress.fqdn}'
