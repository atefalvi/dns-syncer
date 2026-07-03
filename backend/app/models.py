"""Typed models for API request/response bodies.

Storage stays as plain dicts (config.json is the source of truth); these models
validate the API surface only.
"""
from typing import Any, Literal, Optional

from pydantic import BaseModel


class RecordConfig(BaseModel):
    id: str
    enabled: bool = True
    zone_id: str = ""
    zone_name: str = ""
    record_id: str = ""
    hostname: str
    fqdn: str = ""
    type: Literal["A", "AAAA"] = "A"
    proxied: bool = True
    target_ip: str = ""
    cloudflare_value: str = ""
    status: str = "unknown"
    last_checked_at: Optional[str] = None
    last_updated_at: Optional[str] = None


class RecordCreate(BaseModel):
    zone_id: str = ""
    zone_name: str = ""
    hostname: str
    type: Literal["A", "AAAA"] = "A"
    proxied: bool = True
    enabled: bool = True


class RecordPatch(BaseModel):
    enabled: Optional[bool] = None
    proxied: Optional[bool] = None


class IntegrationConfig(BaseModel):
    id: str = ""
    enabled: bool = True
    name: str
    type: Literal["webhook", "discord", "slack", "teams"] = "webhook"
    trigger_events: list[str] = []
    method: str = "POST"
    url: str = ""  # write-only; stored encrypted, never returned
    headers: dict[str, str] = {}
    body_template: dict[str, Any] = {}


class IntegrationPatch(BaseModel):
    enabled: Optional[bool] = None
    name: Optional[str] = None
    trigger_events: Optional[list[str]] = None
    method: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[dict[str, str]] = None
    body_template: Optional[dict[str, Any]] = None


class AppSettings(BaseModel):
    sync_interval_minutes: Optional[int] = None
    ip_provider: Optional[str] = None
    ip_provider_url: Optional[str] = None
    log_retention_days: Optional[int] = None
    max_log_entries: Optional[int] = None
    run_on_startup: Optional[bool] = None
    cloudflare_zone_id: Optional[str] = None
    cloudflare_zone_name: Optional[str] = None
    ui_bind_host: Optional[str] = None
    ui_port: Optional[int] = None


class TokenBody(BaseModel):
    token: str
