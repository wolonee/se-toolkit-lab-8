"""Tool schemas, handlers, and registry for observability MCP server."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass

from mcp.types import Tool
from pydantic import BaseModel, Field

from mcp_obs.observability import (
    LogSearchResult,
    LogsErrorCountResult,
    ObservabilityClient,
    TraceGetResult,
    TracesListResult,
)


class LogsSearchQuery(BaseModel):
    query: str = Field(description="LogsQL query string.")
    limit: int = Field(default=20, ge=1, le=200, description="Max records.")


class LogsErrorCountQuery(BaseModel):
    minutes: int = Field(
        default=60, ge=1, le=24 * 60, description="Time window in minutes."
    )
    service_name: str | None = Field(
        default="Learning Management Service",
        description="Optional service.name filter.",
    )
    limit: int = Field(default=200, ge=1, le=2000, description="Max records to scan.")


class TracesListQuery(BaseModel):
    service: str = Field(
        default="Learning Management Service",
        description="Service name for trace lookup.",
    )
    limit: int = Field(default=10, ge=1, le=100, description="Max traces.")


class TraceGetQuery(BaseModel):
    trace_id: str = Field(description="Trace ID to retrieve.")


ToolPayload = BaseModel | Sequence[BaseModel]
ToolHandler = Callable[[ObservabilityClient, BaseModel], Awaitable[ToolPayload]]


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    model: type[BaseModel]
    handler: ToolHandler

    def as_tool(self) -> Tool:
        schema = self.model.model_json_schema()
        schema.pop("$defs", None)
        schema.pop("title", None)
        return Tool(name=self.name, description=self.description, inputSchema=schema)


async def _logs_search(client: ObservabilityClient, args: BaseModel) -> LogSearchResult:
    query = _require_logs_search_query(args)
    return await client.logs_search(query=query.query, limit=query.limit)


async def _logs_error_count(
    client: ObservabilityClient, args: BaseModel
) -> LogsErrorCountResult:
    query = _require_logs_error_count_query(args)
    scoped = f'_time:{query.minutes}m severity:ERROR'
    if query.service_name:
        scoped += f' service.name:"{query.service_name}"'
    return await client.logs_error_count(query=scoped, limit=query.limit)


async def _traces_list(client: ObservabilityClient, args: BaseModel) -> TracesListResult:
    query = _require_traces_list_query(args)
    return await client.traces_list(service=query.service, limit=query.limit)


async def _traces_get(client: ObservabilityClient, args: BaseModel) -> TraceGetResult:
    query = _require_trace_get_query(args)
    return await client.traces_get(trace_id=query.trace_id)


def _require_logs_search_query(args: BaseModel) -> LogsSearchQuery:
    if not isinstance(args, LogsSearchQuery):
        raise TypeError(f"Expected {LogsSearchQuery.__name__}, got {type(args).__name__}")
    return args


def _require_logs_error_count_query(args: BaseModel) -> LogsErrorCountQuery:
    if not isinstance(args, LogsErrorCountQuery):
        raise TypeError(
            f"Expected {LogsErrorCountQuery.__name__}, got {type(args).__name__}"
        )
    return args


def _require_traces_list_query(args: BaseModel) -> TracesListQuery:
    if not isinstance(args, TracesListQuery):
        raise TypeError(f"Expected {TracesListQuery.__name__}, got {type(args).__name__}")
    return args


def _require_trace_get_query(args: BaseModel) -> TraceGetQuery:
    if not isinstance(args, TraceGetQuery):
        raise TypeError(f"Expected {TraceGetQuery.__name__}, got {type(args).__name__}")
    return args


TOOL_SPECS = (
    ToolSpec(
        "logs_search",
        "Search VictoriaLogs with LogsQL and return matching records.",
        LogsSearchQuery,
        _logs_search,
    ),
    ToolSpec(
        "logs_error_count",
        "Count error logs per service in a time window.",
        LogsErrorCountQuery,
        _logs_error_count,
    ),
    ToolSpec(
        "traces_list",
        "List recent trace IDs for a service from VictoriaTraces.",
        TracesListQuery,
        _traces_list,
    ),
    ToolSpec(
        "traces_get",
        "Fetch a full trace by ID from VictoriaTraces.",
        TraceGetQuery,
        _traces_get,
    ),
)
TOOLS_BY_NAME = {spec.name: spec for spec in TOOL_SPECS}
