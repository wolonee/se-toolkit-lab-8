# Lab 8 — Report

Paste your checkpoint evidence below. Add screenshots as image files in the repo and reference them with `![description](path)`.

## Task 1A — Bare agent

### "What is the agentic loop?" (`cli:task1a-loop`)

The agentic loop is the fundamental cycle that autonomous AI agents follow to accomplish tasks. It's the core reasoning and action pattern that enables agents to work independently toward goals.

**Perceive → Reason → Act → Observe → (repeat)**

1. **Perceive** — gather user input, environment state, context.
2. **Reason** — analyze goals, plan, decide next steps.
3. **Act** — call tools, modify environment, communicate.
4. **Observe** — check results, detect errors, decide whether to continue.

This loop enables autonomy: breaking tasks into steps, adapting on failures, and iterating until the goal is met or human input is needed. Example for “create a README”: read project files → plan content → write file → verify.

### "What labs are available in our LMS?" (`cli:task1a-labs`)

The agent did **not** use live LMS backend data. It used built-in file tools (`list_dir`, `read_file`) on the repo and answered from local documentation (README, `lab/tasks`, etc.). It described **Lab 8** and listed required/optional tasks from the workspace — not real `lab-XX` identifiers from the API. That matches the Part A expectation: no MCP LMS tools yet.

## Task 1B — Agent with LMS tools

### "What labs are available?" (`cli:task1b-labs`, before sync)

The agent called `mcp_lms_lms_labs` and `mcp_lms_lms_health`. It reported the backend as healthy with **no labs** (item count 0) and offered to run the sync pipeline.

After **`lms_sync_pipeline`** (`cli:task1b-sync`), a second listing returned **real backend labs**, e.g. Lab 01–07 titles plus **lab-08** (identifiers such as `lab-01` … `lab-08`).

### "Is the LMS backend healthy?" (`cli:task1b-health`)

The agent called `mcp_lms_lms_health` and answered: **yes**, the LMS backend is healthy, tracking **56 items**.

## Task 1C — Skill prompt

### "Show me the scores" without a lab (`cli:task1c-2`, with `workspace/skills/lms/SKILL.md`)

The agent called **`mcp_lms_lms_labs`** only, then responded with a **numbered list of all 8 labs** (titles + identifiers) and **asked which lab** to show scores for, with an option to request an overview of all labs. It did **not** call `mcp_lms_lms_pass_rates` until the user picks a scope — matching the checkpoint.

## Task 2A — Deployed agent

`docker compose ps` shows `nanobot` is **Up**.

Startup excerpt (`docker compose logs nanobot --tail 200`):

```text
nanobot-1  | Using config: /app/nanobot/config.resolved.json
nanobot-1  | 🐈 Starting nanobot gateway version 0.1.4.post5 on port 18790...
nanobot-1  | 2026-04-01 15:33:11.943 | INFO | nanobot.channels.manager:_init_channels:58 - WebChat channel enabled
nanobot-1  | ✓ Channels enabled: webchat
nanobot-1  | 2026-04-01 15:33:14.581 | INFO | ... MCP server 'lms': connected, 9 tools registered
nanobot-1  | 2026-04-01 15:33:15.703 | INFO | ... MCP server 'webchat': connected, 1 tools registered
nanobot-1  | 2026-04-01 15:33:15.703 | INFO | nanobot.agent.loop:run:280 - Agent loop started
```

## Task 2B — Web client

WebSocket endpoint check through Caddy (`/ws/chat`) with `NANOBOT_ACCESS_KEY`:

```json
{"type":"text","content":"Here are the available labs: ... lab-01 ... lab-08 ..."}
```

Conversation evidence over webchat transport:

- `What can you do in this system?` -> agent returned capabilities summary.
- `How is the backend doing?` -> `healthy`, item count `56` (real LMS tool data).
- `Show me the scores` -> structured UI payload:

```json
{"type":"choice","options":[{"label":"Lab 01 – Products, Architecture & Roles","value":"lab-01"}, ... ]}
```

Nanobot logs confirm end-to-end flow:

- `Processing message from webchat:...`
- `Tool call: mcp_lms_lms_health({})`
- `Tool call: mcp_lms_lms_labs({})`
- `Tool call: mcp_webchat_ui_message({...})`

TODO screenshot path: `![Task 2B web client chat](artifacts/task-2b-webchat.png)`

## Task 3A — Structured logging

### Happy path excerpt (`request_started` -> `request_completed`, status 200)

From `docker compose logs backend --tail 80`:

```text
2026-04-01 15:42:19,224 INFO ... trace_id=6c5f013245157b3f004e0817682a72da ... - request_started
2026-04-01 15:42:19,225 INFO ... trace_id=6c5f013245157b3f004e0817682a72da ... - auth_success
2026-04-01 15:42:19,226 INFO ... trace_id=6c5f013245157b3f004e0817682a72da ... - db_query
2026-04-01 15:42:19,275 INFO ... trace_id=6c5f013245157b3f004e0817682a72da ... - request_completed
INFO: ... "GET /items/ HTTP/1.1" 200 OK
```

### Error path excerpt (`db_query` with error)

From VictoriaLogs HTTP query:

Query:

```text
_time:15m service.name:"Learning Management Service" severity:ERROR
```

Excerpt:

```json
{"_msg":"db_query","event":"db_query","operation":"select","severity":"ERROR","error":"[Errno -2] Name or service not known","trace_id":"08596dd6b185ea3aa8bfe8891815bb4c","service.name":"Learning Management Service"}
{"_msg":"unhandled_exception","event":"unhandled_exception","severity":"ERROR","path":"/pipeline/sync","exception.type":"gaierror","trace_id":"df19f08598d70519b569da8c60bb23a2","service.name":"Learning Management Service"}
```

VictoriaLogs screenshot placeholder:

`![Task 3A VictoriaLogs query](artifacts/task-3a-victorialogs.png)`

## Task 3B — Traces

Healthy trace (trace id `6c5f013245157b3f004e0817682a72da`):

- Span count: `9`
- Processes: `2` (`Learning Management Service`, `mcp-lms`)
- Operations include: `GET /items/`, `SELECT db-lab-8`, `BEGIN;`, `ROLLBACK;`

Error trace (trace id `08596dd6b185ea3aa8bfe8891815bb4c`):

- Span count: `6`
- Processes: `2`
- Failure aligns with DB connectivity loss during `/items/` flow (no successful SQL spans like the healthy trace)

Trace screenshot placeholders:

`![Task 3B healthy trace](artifacts/task-3b-trace-healthy.png)`

`![Task 3B error trace](artifacts/task-3b-trace-error.png)`

## Task 3C — Observability MCP tools

### Normal condition (scoped to avoid stale historical errors)

Prompt: `Any LMS backend errors in the last 1 minute?`

Response:

```text
No LMS backend errors detected in the last 1 minute. The Learning Management Service appears to be running cleanly during that window.
```

### Failure condition (PostgreSQL stopped, then LMS-backed requests triggered)

Prompt: `Any LMS backend errors in the last 10 minutes?`

Response:

```text
Yes, there are 9 errors in the last 10 minutes.
Root cause: Database connectivity failure - DNS resolution error (socket.gaierror: [Errno -2] Name or service not known)
Affected service: Learning Management Service
Failing operation: PostgreSQL database connections via asyncpg
```

Validation from nanobot logs shows obs MCP tools were registered and called:

- `mcp_obs_logs_search`
- `mcp_obs_logs_error_count`
- `mcp_obs_traces_list`
- `mcp_obs_traces_get` (registered)

## Task 4A — Multi-step investigation

With PostgreSQL stopped, prompt: `What went wrong?`

Agent response (log + trace evidence in one investigation):

```text
What went wrong: The Learning Management Service cannot connect to PostgreSQL.

Log evidence:
- 14 errors in the last 10 minutes from Learning Management Service
- Error at 2026-04-01T15:53:18Z: socket.gaierror: [Errno -2] Name or service not known

Trace evidence:
- trace_id: e3507eab3e829aff96cceadd9d1f4f96
- failing span/operation: connect to postgres:5432
- failing request path: mcp-lms -> Learning Management Service (GET /items/) -> connect (postgres:5432) -> FAILED
```

## Task 4B — Proactive health check

In the same chat, I asked:

`Create a health check for this chat that runs every 2 minutes using your cron tool...`

Then `List scheduled jobs.` showed:

```text
ID: 5e853ce2
Job: LMS Health Check
Interval: Every 2 minutes
```

Proactive scheduled report transcript while failure was present:

```text
## LMS Health Check Summary
Status: Unhealthy
Findings (last 2 minutes):
- Backend health: HTTP 503
- Root cause (trace analysis): socket.gaierror [Errno -2], cannot resolve postgres:5432
- Affected operation: GET /items/
```

## Task 4C — Bug fix and recovery

1. **Root cause**

The planted bug was in `backend/src/lms_backend/routers/items.py` in `get_items()`: a broad `except Exception` converted all failures (including real DB outages) into misleading **`404 Items not found`**.

2. **Fix**

Changed the exception path to preserve failure semantics:

```diff
- logger.warning("items_list_failed_as_not_found", extra={"event": "items_list_failed_as_not_found"})
- raise HTTPException(status_code=404, detail="Items not found")
+ logger.exception("items_list_failed_internal", extra={"event": "items_list_failed_internal"})
+ raise HTTPException(status_code=503, detail="Items service unavailable")
```

3. **Post-fix failure check** (`What went wrong?` after redeploy, with PostgreSQL down)

```text
Error Count: 19 errors in last 10 minutes
HTTP Status: 503 Service Unavailable
Failing Endpoint: GET /items/
Root Cause: socket.gaierror [Errno -2] Name or service not known
Trace evidence: trace_id 7d644f520bf999efe6991f3c044632b7, failing connect span to postgres:5432
```

This shows the real DB failure path instead of the old misleading 404 handler.

4. **Healthy follow-up** (after PostgreSQL restart and new short cron check)

```text
Health Check Summary:
No errors detected in Learning Management Service during last 2 minutes.
Backend Status: Healthy (56 items)
All systems operating normally.
```
