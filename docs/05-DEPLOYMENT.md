# 05. Deployment

## Local
See the README quick start. Configuration comes from `.env` (never commit it).

| Variable | Purpose |
|---|---|
| `USE_LLM` | `true` enables Foundry commentary. Default `false` |
| `FOUNDRY_ENDPOINT` | Azure OpenAI endpoint, e.g. `https://<resource>.openai.azure.com/openai/v1` |
| `FOUNDRY_MODEL` | deployment name, e.g. `gpt-4.1-mini` |
| `EVENTHUB_NAMESPACE`, `COSMOS_ENDPOINT` | reserved, not used yet |

Locally the app signs in with your `az login`. The tests never read `.env` (see `tests/conftest.py`).

## What exists in Azure

| Resource | Name | Notes |
|---|---|---|
| Resource group | `matchlens-rg` | |
| Foundry resource | `matchlens-foundry` | East US 2, with a `gpt-4.1-mini` deployment |
| Container Apps environment | `matchlens-api-env` | |
| Container App | `matchlens-api` | external ingress, port 8000, 0.5 CPU, 1 GiB, **min 1 and max 1 replica** |

The Container App has a system-assigned managed identity with the **Cognitive Services OpenAI User** role on `matchlens-foundry`. No keys exist anywhere.

## Why one replica
Match state is in memory. With two replicas a request could reach a copy that does not know the match. A single replica avoids that until state moves to Cosmos DB.

## Build and release flow
1. Push to `main`.
2. GitHub Actions (`.github/workflows/publish.yml`) builds the Dockerfile and publishes `ghcr.io/bientechsavvy/matchlens:latest`. The package is set to public so Azure can pull it without credentials.
3. Tell Azure to start a new revision (see below).

`ci.yml` runs lint and tests on every push.

Azure Container Registry builds (`az containerapp up --source .`) were not permitted on this subscription (`TasksOperationsNotAllowed`), which is why the image is built on GitHub instead.

## First-time deployment (already done)

```powershell
az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights
az containerapp env create --name matchlens-api-env --resource-group matchlens-rg --location eastus2
az containerapp create --name matchlens-api --resource-group matchlens-rg --environment matchlens-api-env `
  --image ghcr.io/bientechsavvy/matchlens:latest --target-port 8000 --ingress external `
  --min-replicas 1 --max-replicas 1 --system-assigned `
  --env-vars USE_LLM=true FOUNDRY_ENDPOINT=https://matchlens-foundry.openai.azure.com/openai/v1 FOUNDRY_MODEL=gpt-4.1-mini

$principal = az containerapp show --name matchlens-api --resource-group matchlens-rg --query identity.principalId -o tsv
$scope = az cognitiveservices account show --name matchlens-foundry --resource-group matchlens-rg --query id -o tsv
az role assignment create --assignee-object-id $principal --assignee-principal-type ServicePrincipal `
  --role "Cognitive Services OpenAI User" --scope $scope
```

## Releasing a new version

```powershell
git push
# wait for the publish-image run to turn green on GitHub, then:
az containerapp update --name matchlens-api --resource-group matchlens-rg `
  --image ghcr.io/bientechsavvy/matchlens:latest --revision-suffix ("r" + (Get-Date -Format "HHmmss"))
```

The new revision suffix forces Azure to pull the image again.

## Viewing it
- **Address:** `az containerapp show --name matchlens-api --resource-group matchlens-rg --query properties.configuration.ingress.fqdn -o tsv`
- **Portal:** Resource groups, `matchlens-rg`, `matchlens-api`. The Overview page shows the Application Url and **Log stream** (under Monitoring) shows live logs.
- **Logs:** `az containerapp logs show --name matchlens-api --resource-group matchlens-rg --follow`. Look for `Foundry call failed` if AI text is missing.
- **Model usage:** open `matchlens-foundry`, then Monitoring, then Metrics.

## Cost
The model calls are short and cheap. Set a budget under Cost Management, since the public link can start matches that call the model.

## Judge access
The project must stay available, free and without login, until the judging period ends. Do not delete the resources before then. After judging ends and results are announced, you can remove everything with `az group delete --name matchlens-rg`, which also deletes the Foundry resource.

## Infra as code
`infra/main.bicep` is an unvalidated starter and was **not** used for the live deployment, which was created with the CLI commands above.