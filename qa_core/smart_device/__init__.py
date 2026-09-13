"""Smart device domain helpers for scenario-local metadata enrichment."""

from qa_core.smart_device.entity_parser import extract_entities
from qa_core.smart_device.metadata import SCENARIO_ID, metadata_for_document, normalize_metadata

__all__ = ["SCENARIO_ID", "extract_entities", "metadata_for_document", "normalize_metadata"]
