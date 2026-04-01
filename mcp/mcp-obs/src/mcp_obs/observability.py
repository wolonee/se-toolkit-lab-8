"""HTTP clients and models for observability backends."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import BaseModel, Field


class LogRecord(BaseModel):
    timestamp: str = Field(alias="_time")
    service_name: str | None = Field(default=None, alias="service.name")
    severity: str | None = None
    event: str | None = None
    trace_id: str | None = None
    message: str | None = Field(default=None, alias="_msg")
    raw: dict[str, Any]


class LogSearchResult(BaseModel):
    query: str
    count: int
    records: list[LogRecord]


class ServiceErrorCount(BaseModel):
    service_name: str
    error_count: int


class LogsErrorCountResult(BaseModel):
    query: str
    total_errors: int
    per_service: list[ServiceErrorCount]


class TracesListResult(BaseModel):
    service: str
    count: int
    trace_ids: list[str]


class TraceGetResult(BaseModel):
    trace_id: str
    span_count: int
    process_count: int
    root_spans: list[str]
    raw: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ObservabilityClient:
    logs_base_url: str
    traces_base_url: str
    _http: httpx.AsyncClient

    @classmethod
    def create(
        cls, logs_base_url: str, traces_base_url: str, timeout_s: float = 20.0
    ) -> ObservabilityClient:
        return cls(
            logs_base_url=logs_base_url.rstrip("/"),
            traces_base_url=traces_base_url.rstrip("/"),
            _http=httpx.AsyncClient(timeout=timeout_s),
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def logs_search(self, query: str, limit: int) -> LogSearchResult:
        response = await self._http.get(
            f"{self.logs_base_url}/select/logsql/query",
            params={"query": query, "limit": str(limit)},
        )
        response.raise_for_status()
        records: list[LogRecord] = []
        text = response.text.strip()
        if text:
            for line in text.splitlines():
                payload = json.loads(line)
                # Keep canonical fields plus whole raw payload for flexibility.
                record = LogRecord.model_validate({**payload, "raw": payload})
                records.append(record)
        return LogSearchResult(query=query, count=len(records), records=records)

    async def logs_error_count(self, query: str, limit: int) -> LogsErrorCountResult:
        search = await self.logs_search(query=query, limit=limit)
        counts: Counter[str] = Counter()
        for record in search.records:
            service = record.service_name or "unknown"
            counts[service] += 1
        per_service = [
            ServiceErrorCount(service_name=service, error_count=count)
            for service, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        ]
        return LogsErrorCountResult(
            query=query,
            total_errors=search.count,
            per_service=per_service,
        )

    async def traces_list(self, service: str, limit: int) -> TracesListResult:
        response = await self._http.get(
            f"{self.traces_base_url}/select/jaeger/api/traces",
            params={"service": service, "limit": str(limit)},
        )
        response.raise_for_status()
        payload = response.json()
        traces = payload.get("data", [])
        trace_ids = [item.get("traceID", "") for item in traces if item.get("traceID")]
        return TracesListResult(service=service, count=len(trace_ids), trace_ids=trace_ids)

    async def traces_get(self, trace_id: str) -> TraceGetResult:
        response = await self._http.get(
            f"{self.traces_base_url}/select/jaeger/api/traces/{trace_id}"
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data", [])
        if not data:
            return TraceGetResult(
                trace_id=trace_id,
                span_count=0,
                process_count=0,
                root_spans=[],
                raw=payload,
            )
        first = data[0]
        spans = first.get("spans", [])
        span_ids = {span.get("spanID") for span in spans}
        child_ids = {
            ref.get("spanID")
            for span in spans
            for ref in span.get("references", [])
            if ref.get("spanID")
        }
        root_spans = [
            span.get("operationName", "unknown")
            for span in spans
            if span.get("spanID") in span_ids - child_ids
        ]
        return TraceGetResult(
            trace_id=trace_id,
            span_count=len(spans),
            process_count=len(first.get("processes", {})),
            root_spans=root_spans,
            raw=first,
        )
