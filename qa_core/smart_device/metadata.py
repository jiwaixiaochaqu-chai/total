"""Domain metadata helpers for the smart device knowledge scenario.

This module is intentionally scenario-local. It knows the field contract used by
``smart_device_knowledge`` documents, while the generic RAG indexing pipeline only
calls it as an optional enrichment hook.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from typing import Any

import tomllib

SCENARIO_ID = "smart_device_knowledge"

DOMAIN_METADATA_FIELDS = (
    "product_model",
    "product_line",
    "hardware_version",
    "firmware_version",
    "app_version",
    "mobile_os",
    "error_codes",
    "document_type",
    "effective_status",
)

_PRODUCT_LINES = {"smartwatch", "smart_scale", "health_accessory"}
_DOCUMENT_TYPES = {"manual", "protocol", "sop", "test_case", "known_issue", "release_note", "faq"}
_EFFECTIVE_STATUSES = {"draft", "active", "deprecated"}

_MODEL_RE = re.compile(r"^[A-Z][A-Z0-9]{1,15}(?:-[A-Z0-9]{1,16}){0,3}$")
_VERSION_RE = re.compile(r"^[vV]?(\d+(?:\.\d+){1,3}(?:-[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*)?(?:\+[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*)?)$")
_ERROR_RE = re.compile(r"^[A-Z]{1,8}[-_]?\d{2,6}$")
_OS_RE = re.compile(r"^(android|ios)(?:\s+\d+(?:\.\d+){0,2})?$", re.IGNORECASE)
_FRONTMATTER_RE = re.compile(r"\A\s*\+\+\+\s*\r?\n(.*?)\r?\n\+\+\+", re.DOTALL)


def _clean_text(value: Any, *, field: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return unicodedata.normalize("NFKC", value).strip()


def _normalize_enum(value: Any, *, field: str, allowed: set[str]) -> str:
    raw = _clean_text(value, field=field)
    if not raw:
        return ""
    normalized = re.sub(r"[\s-]+", "_", raw.lower())
    aliases = {"smart_watch": "smartwatch", "smart_watches": "smartwatch", "smart_scale": "smart_scale"}
    normalized = aliases.get(normalized, normalized)
    if normalized not in allowed:
        raise ValueError(f"{field} has unsupported value: {raw}")
    return normalized


def _normalize_model(value: Any) -> str:
    raw = _clean_text(value, field="product_model").upper()
    if not raw:
        return ""
    if not _MODEL_RE.fullmatch(raw) or not any(ch.isdigit() for ch in raw):
        raise ValueError(f"product_model has unsupported format: {raw}")
    return raw


def _normalize_version(value: Any, *, field: str, hardware: bool = False) -> str:
    raw = _clean_text(value, field=field)
    if not raw:
        return ""
    match = _VERSION_RE.fullmatch(raw)
    if not match:
        raise ValueError(f"{field} has unsupported version format: {raw}")
    version = match.group(1)
    return f"V{version}" if hardware else version


def _normalize_os(value: Any) -> str:
    raw = _clean_text(value, field="mobile_os")
    if not raw:
        return ""
    if not _OS_RE.fullmatch(raw):
        raise ValueError(f"mobile_os has unsupported format: {raw}")
    name, _, suffix = raw.partition(" ")
    prefix = "iOS" if name.lower() == "ios" else "Android"
    return f"{prefix} {suffix.strip()}" if suffix.strip() else prefix


def _split_error_codes(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, str):
        candidates = [item for item in re.split(r"[,，;；\s]+", value) if item]
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        candidates = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError("error_codes entries must be strings")
            candidates.append(item)
    else:
        raise ValueError("error_codes must be a string or a sequence of strings")

    normalized: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        code = unicodedata.normalize("NFKC", item).strip().upper().replace("_", "-")
        if not code:
            continue
        if not _ERROR_RE.fullmatch(code):
            raise ValueError(f"error_codes has unsupported code: {item}")
        if code not in seen:
            normalized.append(code)
            seen.add(code)
    return normalized


def normalize_metadata(raw: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Normalize the smart device metadata contract without inventing values."""

    payload = dict(raw or {})
    return {
        "product_model": _normalize_model(payload.get("product_model")),
        "product_line": _normalize_enum(payload.get("product_line"), field="product_line", allowed=_PRODUCT_LINES),
        "hardware_version": _normalize_version(payload.get("hardware_version"), field="hardware_version", hardware=True),
        "firmware_version": _normalize_version(payload.get("firmware_version"), field="firmware_version"),
        "app_version": _normalize_version(payload.get("app_version"), field="app_version"),
        "mobile_os": _normalize_os(payload.get("mobile_os")),
        "error_codes": _split_error_codes(payload.get("error_codes")),
        "document_type": _normalize_enum(payload.get("document_type"), field="document_type", allowed=_DOCUMENT_TYPES),
        "effective_status": _normalize_enum(payload.get("effective_status"), field="effective_status", allowed=_EFFECTIVE_STATUSES),
    }


def _frontmatter_payload(text: str) -> dict[str, Any]:
    match = _FRONTMATTER_RE.match(text or "")
    if not match:
        return {}
    parsed = tomllib.loads(match.group(1))
    if not isinstance(parsed, dict):
        return {}
    return {key: parsed[key] for key in DOMAIN_METADATA_FIELDS if key in parsed}


def metadata_for_document(scenario_id: str, text: str, existing_metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return smart-device domain metadata for one document chunk.

    Existing metadata wins over in-document front matter, which prevents document
    authors from overriding tenant, role, visibility, or version governance fields.
    """

    if scenario_id != SCENARIO_ID:
        return {}
    existing = dict(existing_metadata or {})
    raw = _frontmatter_payload(text)
    for key in DOMAIN_METADATA_FIELDS:
        if key in existing:
            raw[key] = existing[key]
    return normalize_metadata(raw)
