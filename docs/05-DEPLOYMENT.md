# 05. Deployment

## Environment variables (`.env.example`)

| Var | Purpose |
|-----|---------|
| `FOUNDRY_ENDPOINT` | Microsoft Foundry project endpoint |
| `FOUNDRY_MODEL` | deployed model name |
| `USE_LLM` | `true` to enable LLM narration; default `false` (templates) |
| `EVENTHUB_NAMESPACE` | Phase 2 streaming |
| `COSMOS_ENDPOINT` | Phase 2 state store |

Authentication uses **managed identity / DefaultAzureCredential**. No keys in code.

## Targets
1. **Local**: `uvicorn` (Phase 1).
2. **Azure Container Apps**: containerised API (Dockerfile in Phase 2).
3. **Azure Functions**: Event Hub triggered stream processors.

## CI/CD (GitHub Actions)
`lint (ruff) -> test (pytest) -> build image -> deploy to Container Apps`. Infra is defined in `infra/` (Bicep, Phase 2).

## Judge access (Rules §4.8)
Provide a public URL, free, with no login. The seeded demo match must load without configuration.