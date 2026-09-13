from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from langchain_core.documents import Document

from qa_core.indexing.document_normalizer import normalize_documents
from qa_core.smart_device.entity_parser import extract_entities
from qa_core.smart_device.metadata import metadata_for_document, normalize_metadata


class SmartDeviceMetadataTests(unittest.TestCase):
    def test_normalize_metadata_canonicalizes_domain_fields(self) -> None:
        metadata = normalize_metadata(
            {
                "product_model": " sw-h8 ",
                "product_line": "smart watch",
                "hardware_version": "2.0",
                "firmware_version": "v1.3.6",
                "app_version": "2.8.1-beta.1",
                "mobile_os": "android 14",
                "error_codes": "e103, E103;fw200",
                "document_type": "known issue",
                "effective_status": "ACTIVE",
            }
        )
        self.assertEqual(metadata["product_model"], "SW-H8")
        self.assertEqual(metadata["product_line"], "smartwatch")
        self.assertEqual(metadata["hardware_version"], "V2.0")
        self.assertEqual(metadata["firmware_version"], "1.3.6")
        self.assertEqual(metadata["app_version"], "2.8.1-beta.1")
        self.assertEqual(metadata["mobile_os"], "Android 14")
        self.assertEqual(metadata["error_codes"], ["E103", "FW200"])
        self.assertEqual(metadata["document_type"], "known_issue")
        self.assertEqual(metadata["effective_status"], "active")

    def test_normalize_metadata_rejects_unsupported_values(self) -> None:
        for raw in [
            {"product_model": "demo"},
            {"product_line": "medical_device"},
            {"hardware_version": "release"},
            {"mobile_os": "Windows 11"},
            {"error_codes": ["E103", 103]},
            {"document_type": "contract"},
            {"effective_status": "approved"},
        ]:
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    normalize_metadata(raw)

    def test_extract_entities_reads_only_explicit_domain_entities(self) -> None:
        text = "型号 SW-H8，硬件版本 V2.0，固件版本 1.3.6，App版本 2.8.1，Android 14，错误码 E103。IP 192.168.0.1 和日期 2026-09-13 不是错误码。"
        entities = extract_entities(text)
        self.assertEqual(entities["product_model"], ["SW-H8"])
        self.assertEqual(entities["hardware_version"], ["V2.0"])
        self.assertEqual(entities["firmware_version"], ["1.3.6"])
        self.assertEqual(entities["app_version"], ["2.8.1"])
        self.assertEqual(entities["mobile_os"], ["Android 14"])
        self.assertEqual(entities["error_codes"], ["E103"])

    def test_metadata_for_document_uses_toml_frontmatter_for_smart_device_only(self) -> None:
        text = """+++\nproduct_model = \"SW-H8\"\nproduct_line = \"smartwatch\"\nhardware_version = \"V2.0\"\nfirmware_version = \"1.3.6\"\napp_version = \"2.8.1\"\nmobile_os = \"Android 14\"\nerror_codes = [\"E103\"]\ndocument_type = \"known_issue\"\neffective_status = \"active\"\n+++\n正文。"""
        metadata = metadata_for_document("smart_device_knowledge", text, {})
        self.assertEqual(metadata["product_model"], "SW-H8")
        self.assertEqual(metadata["error_codes"], ["E103"])
        self.assertEqual(metadata_for_document("enterprise_knowledge", text, {}), {})

    def test_normalizer_adds_domain_metadata_without_overriding_scope(self) -> None:
        text = """+++\nproduct_model = \"SW-H8\"\nproduct_line = \"smartwatch\"\nhardware_version = \"V2.0\"\nfirmware_version = \"1.3.6\"\napp_version = \"2.8.1\"\nmobile_os = \"Android 14\"\nerror_codes = [\"E103\"]\ndocument_type = \"known_issue\"\neffective_status = \"active\"\n+++\n正文。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "issue.md"
            path.write_text(text, encoding="utf-8")
            docs = normalize_documents(
                [Document(page_content=text, metadata={"visibility": "private"})],
                path,
                "quality",
                "kb_test_v1",
                "smart_device_knowledge",
                1,
                allowed_roles=["qa"],
            )
        metadata = docs[0].metadata
        self.assertEqual(metadata["product_model"], "SW-H8")
        self.assertEqual(metadata["document_type"], "known_issue")
        self.assertEqual(metadata["visibility"], "public")
        self.assertEqual(metadata["allowed_roles"], ["qa"])
        self.assertEqual(metadata["source"], "quality")
        self.assertEqual(metadata["source_type"], "doc")


if __name__ == "__main__":
    unittest.main()
