# 07. Roadmap

| Area | Status |
|---|---|
| Schema, simulator, analyst, explainer, narrator (EN/ES/FR), personalizer, overlays, API | done |
| Supervisor with retry, fallback and trace | done |
| Foundry commentary, verified live | done |
| Microsoft Agent Framework workflow (`/agent-run`) | done |
| WebSocket stream, event ingest | done |
| Frontend with momentum graph, stats and agent panel | done |
| GitHub repository and image publishing workflow | done |
| Azure Container Apps deployment with managed identity | done |
| 30 offline tests, lint clean | done |
| README and docs updated | done |
| Demo video (under 2 minutes) and pitch | to do |
| Submit on the hackathon site (deadline 27 Oct 2026, 11:59 pm Pacific) | to do |

## Optional improvements, in order of value
1. Run the narrator's model calls in parallel, so analyst mode takes about 1 to 2 seconds instead of several.
2. Store matches in Cosmos DB, which removes the single-replica limit and strengthens the Azure story.
3. Make `agent-run` honour favourite team and player focus.
4. Add Application Insights for monitoring.
5. Add Event Hubs for streaming ingest.

## Risks
- The public API has no authentication and each match can call the model. Keep a cost budget in place.
- State is lost on restart, so run through the demo shortly after any redeploy.