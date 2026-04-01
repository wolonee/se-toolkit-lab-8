---
name: observability
description: Investigate LMS failures with logs and traces
always: true
---

# Observability strategy

Use `mcp_obs_*` tools when the user asks about errors, failures, incidents, or performance.
Treat **"What went wrong?"** and **"Check system health"** as explicit investigation requests.

## Tool order

1. Start with `mcp_obs_logs_error_count` using a narrow fresh window (2-10 minutes for live incidents, otherwise 10-60 minutes) and `service_name: Learning Management Service` unless the user asks broader scope.
2. If errors exist, call `mcp_obs_logs_search` with a scoped LogsQL query and extract recent `trace_id` values.
3. If a useful trace ID is found, call `mcp_obs_traces_get` for request-path details and failing operation evidence.
4. Use `mcp_obs_traces_list` when no trace ID is present in sampled logs but you still need recent traces.

## Response style

- Summarize findings concisely: error count, affected service, likely failing step, and one concrete next action.
- For "What went wrong?" always cite both:
  - one log fact (error/event + timestamp or trace id),
  - one trace fact (failing span/operation path).
- Do not dump raw JSON unless the user explicitly asks for raw output.
- If no errors are found, state that clearly and include the checked time window.

## Scope discipline

- Prefer LMS-focused wording (`Learning Management Service`) for LMS questions.
- Use short time windows for fresh incidents to avoid stale unrelated errors.
- When asked to schedule recurring checks in chat, use the built-in `cron` tool (add/list/remove) rather than heartbeat files.
