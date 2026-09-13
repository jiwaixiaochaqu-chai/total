"""Lightweight entity recognizers for smart device product and issue text."""

from __future__ import annotations

import re
from collections.abc import Iterable

from qa_core.smart_device.metadata import normalize_metadata

_MODEL_LABEL_RE = re.compile(r"(?:产品型号|设备型号|型号|model)\s*[:：]?\s*([A-Za-z][A-Za-z0-9]{1,15}(?:-[A-Za-z0-9]{1,16}){0,3})", re.IGNORECASE)
_HW_LABEL_RE = re.compile(r"(?:硬件版本|硬件|hardware)\s*[:：]?\s*([vV]?\d+(?:\.\d+){1,3})", re.IGNORECASE)
_FW_LABEL_RE = re.compile(r"(?:固件版本|固件|firmware)\s*[:：]?\s*([vV]?\d+(?:\.\d+){1,3}(?:-[A-Za-z0-9.]+)?)", re.IGNORECASE)
_APP_LABEL_RE = re.compile(r"(?:App版本|应用版本|app)\s*[:：]?\s*([vV]?\d+(?:\.\d+){1,3}(?:-[A-Za-z0-9.]+)?)", re.IGNORECASE)
_ERROR_RE = re.compile(r"\b([A-Z]{1,8}[-_]?\d{2,6})\b")
_OS_RE = re.compile(r"\b(Android\s+\d+(?:\.\d+){0,2}|iOS\s+\d+(?:\.\d+){0,2})\b", re.IGNORECASE)


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.upper()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def _normalized_values(field: str, values: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for value in _unique(values):
        try:
            item = normalize_metadata({field: value})[field]
        except ValueError:
            continue
        if item:
            normalized.append(item)
    return normalized


def extract_entities(text: str) -> dict[str, list[str]]:
    """Extract explicit product, version, OS, and error-code entities from text."""

    value = text or ""
    return {
        "product_model": _normalized_values("product_model", _MODEL_LABEL_RE.findall(value)),
        "hardware_version": _normalized_values("hardware_version", _HW_LABEL_RE.findall(value)),
        "firmware_version": _normalized_values("firmware_version", _FW_LABEL_RE.findall(value)),
        "app_version": _normalized_values("app_version", _APP_LABEL_RE.findall(value)),
        "mobile_os": _normalized_values("mobile_os", _OS_RE.findall(value)),
        "error_codes": normalize_metadata({"error_codes": _ERROR_RE.findall(value)})["error_codes"],
    }
