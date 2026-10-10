# 08. Submission Checklist and Judging Map

## Required (Rules section 4.4)
- [x] Newly built project
- [x] Public GitHub repository
- [x] Working link for judges (Azure Container Apps, free, no login)
- [x] Synthetic data only
- [ ] Pitch naming the Microsoft and Azure technologies used
- [ ] Demo video under 2 minutes with a public URL (YouTube, Vimeo, Facebook Video or Youku), showing the project running
- [ ] Video has no third-party trademarks or copyrighted music
- [ ] English materials
- [ ] Registered at https://aka.ms/insidethegame
- [ ] Submission completed on the Projects page before 27 Oct 2026, 11:59 pm Pacific

## What can honestly be claimed

| Claim | True? |
|---|---|
| Microsoft Agent Framework six-agent workflow | yes, at `/agent-run`. The live feed uses an equivalent plain pipeline |
| Microsoft Foundry model writes the commentary | yes, in analyst mode, from structured facts only |
| Deployed on Azure Container Apps with managed identity | yes |
| CI/CD with GitHub Actions | yes |
| Cosmos DB, Event Hubs, Application Insights | no, planned only |
| GitHub Copilot used to build it | only if you actually used it |

## Judging map (20% each)

| Criterion | Evidence |
|---|---|
| Technological Implementation | seeded synthetic data generator, typed contracts, 30 tests, docs, Foundry, Agent Framework, Azure |
| Agentic Design and Innovation | six specialised agents, supervisor with retry and fallback, facts-only AI |
| Real-World Impact | broadcast overlays, three languages, analyst and casual modes |
| User Experience and Presentation | live feed, momentum graph, agent panel, clear video |
| Adherence to Category | see below |

## Categories to target
- **Best Multi-Agent System**: strongest fit. Distinct roles, shared state through the job, handoffs, recovery from failures.
- **Best Use of Microsoft Foundry**: a real Foundry deployment is used. Be specific about what it does.
- **Best Azure Cloud Native Integration**: only Container Apps and managed identity are used, so this is a weaker fit.

## Pipeline coverage (section 4.1)
Ingest, interpret, explain, render and personalise are all covered. Player tags, pass quality, speed metrics, narratives, explainability, synthetic data and multi-language output are included. Auto-eventing from video is out of scope.