---
name: lms
description: Use LMS MCP tools for live course data
always: true
---

# LMS data (MCP)

Use the `mcp_lms_*` tools for **live** LMS data from the backend. Do not guess lab lists or metrics from repo files when the user asks about the LMS, learners, or scores.

## Tools (when to use)

- **`mcp_lms_lms_health`** — Backend status and **item count**; use for “healthy?”, “status”, or before reporting aggregate data.
- **`mcp_lms_lms_labs`** — Authoritative list of labs; use for “what labs exist?”, or **before** any lab-specific query when the lab is unknown or ambiguous.
- **`mcp_lms_lms_learners`** — All learners.
- **`mcp_lms_lms_pass_rates`** — Per-task pass/average scores for one lab (`lab` required).
- **`mcp_lms_lms_timeline`** — Submission counts over time for one lab (`lab` required).
- **`mcp_lms_lms_groups`** — Group performance for one lab (`lab` required).
- **`mcp_lms_lms_top_learners`** — Top learners by score for one lab (`lab` required; optional `limit`).
- **`mcp_lms_lms_completion_rate`** — Pass ratio for one lab (`lab` required).
- **`mcp_lms_lms_sync_pipeline`** — Run when health is ok but **labs or items look empty**; then re-fetch with `mcp_lms_lms_labs` or `mcp_lms_lms_health`.

## Missing lab

If the user asks about **scores**, pass rates, completion, groups, timeline, or top learners **without naming a lab**:

1. Call **`mcp_lms_lms_labs`** first.
2. If more than one lab exists, **stop and ask which lab** they mean — list titles with identifiers (e.g. `lab-04`). Do **not** call `mcp_lms_lms_pass_rates` (or other lab-scoped tools) for every lab unless the user clearly asked for **all labs**, a **comparison across labs**, or an **overview of every lab**.
3. On channels that support it, the shared **`structured-ui`** skill may present the choice; otherwise use a short plain-text list.

## Numbers and style

- Format percentages and counts clearly (e.g. `72%`, `8 / 12 learners`).
- Keep answers concise; include only figures relevant to the question.

## Capabilities question

If the user asks **what you can do**, summarize: live LMS tools above, that data comes from the backend (not local docs), and that you have separate file/workspace tools for repository tasks — do not conflate the two.
