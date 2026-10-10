# 09. Troubleshooting

Problems met while building this project, and their fixes.

| Symptom | Cause | Fix |
|---|---|---|
| `pydantic-core`, `maturin`, `jiter` or `Rust not found` during `pip install` | The MSYS2 Python has no prebuilt packages | Use Python 3.12 from python.org in PowerShell: `py -3.12 -m venv .venv312` |
| `neither 'setup.py' nor 'pyproject.toml' found` | Wrong folder | `cd` into the folder that contains `pyproject.toml` |
| `az: command not found` | Azure CLI not visible from the MSYS2 window, or the window predates the install | Open a new PowerShell window |
| `Role 'Azure AI User' doesn't exist` | Role name not available | Use `Cognitive Services OpenAI User` |
| `401 PermissionDenied ... lacks the required data action` | The calling identity has no model role, or it has not propagated | Assign the role to your user id, wait a few minutes, `az logout` then `az login` |
| `Cannot find user ... in graph database` when assigning a role | Gmail-style accounts need the object id | Use `--assignee-object-id (az ad signed-in-user show --query id -o tsv)` |
| `No supported WebSocket library detected` and the stream returns 404 | `websockets` is not installed | `pip install websockets` (it is in `pyproject.toml`) |
| `ACR Tasks requests ... are not permitted` | Subscription cannot use ACR build tasks | Build with GitHub Actions and deploy from GHCR |
| `ConnectionResetError 10054` during an `az` command | Network dropped | Check the resource state, then rerun. Try without a VPN |
| `/agent-run` returns 500 | An uncopyable model client was passed through the framework | Fixed by keeping the client in a registry (see 03-AGENTS) |
| Tests fail or run for minutes when `.env` exists | `.env` made tests call the real model | `tests/conftest.py` disables the model for tests |
| Cards show only goals | Player focus is filled in | Clear the Player focus box |
| AI text missing | Casual mode, `USE_LLM` not true, or a Foundry error | Use Analyst mode and check the log for `Foundry call failed` |
| `$pid` assignment error in PowerShell | `$PID` is a reserved variable | Use another variable name such as `$principal` |
| New code not live after redeploy | Azure reused the old image | Add a new `--revision-suffix` when updating |