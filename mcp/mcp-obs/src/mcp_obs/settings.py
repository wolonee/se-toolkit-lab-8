"""Runtime settings for the observability MCP server."""

from __future__ import annotations

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    victorialogs_url: str = Field(
        validation_alias=AliasChoices("NANOBOT_VICTORIALOGS_URL"),
    )
    victoriatraces_url: str = Field(
        validation_alias=AliasChoices("NANOBOT_VICTORIATRACES_URL"),
    )


def resolve_settings() -> Settings:
    return Settings.model_validate({})
