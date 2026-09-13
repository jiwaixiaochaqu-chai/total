from __future__ import annotations

import csv
import re
import unittest
from pathlib import Path

from qa_core.indexing.document_loaders import load_file
from qa_core.intent.classifier import infer_source
from qa_core.scenarios.registry import get_scenario_registry


BANNED_SAMPLE_WORDS = re.compile(r"虚构|脱敏|演示|仅用于\s*RAG\s*场景演示|Fictional|desensitized|demo", re.IGNORECASE)
REQUIRED_FORMATS = {".md", ".csv", ".xlsx", ".docx", ".pptx", ".pdf"}
SOURCE_DIRS = {
    "product_data": "product",
    "development_data": "development",
    "support_data": "support",
    "quality_data": "quality",
}


class SmartDeviceScenarioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = get_scenario_registry()
        self.scenario = self.registry.resolve("smart_device_knowledge")
        self.root = Path(self.scenario.data_root)

    def test_scenario_is_registered_without_changing_existing_contracts(self) -> None:
        scenario_ids = {scenario.scenario_id for scenario in self.registry.list_scenarios()}
        for existing_id in {
            "enterprise_knowledge",
            "saas_support",
            "equipment_ops",
            "compliance_qa",
            "cross_border_risk",
            "tender_contract_risk",
            "insurance_claims",
            "engineering_project_qa",
        }:
            self.assertIn(existing_id, scenario_ids)
        self.assertIn("smart_device_knowledge", scenario_ids)
        self.assertEqual(self.scenario.valid_sources, ["product", "development", "support", "quality"])
        self.assertEqual(self.scenario.faq_collection, "smart_device_faq_hybrid_v1")
        self.assertEqual(self.scenario.doc_collection, "smart_device_doc_hybrid_v1")
        self.assertEqual(
            self.scenario.source_options(),
            [
                {"value": "product", "label": "产品知识"},
                {"value": "development", "label": "技术知识"},
                {"value": "support", "label": "客服支持知识"},
                {"value": "quality", "label": "测试与缺陷知识"},
            ],
        )

    def test_source_patterns_route_domain_questions(self) -> None:
        cases = {
            "SW-H8 的产品功能和续航规格是什么？": "product",
            "同步协议返回 E103 的接口排查方式是什么？": "development",
            "用户绑定失败时客服应该怎么引导？": "support",
            "测试发现 E103 历史缺陷如何复现？": "quality",
        }
        for query, expected in cases.items():
            with self.subTest(query=query):
                self.assertEqual(infer_source(query, self.scenario), expected)

    def test_faq_uses_four_sources_and_business_style_content(self) -> None:
        faq_path = Path(self.scenario.faq_csv_path)
        with faq_path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual({row["source"] for row in rows}, set(self.scenario.valid_sources))
        self.assertGreaterEqual(len(rows), 8)
        for row in rows:
            with self.subTest(question=row["question"]):
                self.assertNotRegex(row["question"], BANNED_SAMPLE_WORDS)
                self.assertNotRegex(row["answer"], BANNED_SAMPLE_WORDS)
                self.assertGreaterEqual(len(row["answer"]), 30)

    def test_each_source_directory_contains_all_supported_sample_formats(self) -> None:
        for dirname in SOURCE_DIRS:
            with self.subTest(dirname=dirname):
                files = [path for path in (self.root / dirname).iterdir() if path.is_file()]
                suffixes = {path.suffix.lower() for path in files}
                self.assertTrue(REQUIRED_FORMATS.issubset(suffixes), suffixes)
                self.assertGreaterEqual(len(files), len(REQUIRED_FORMATS))

    def test_all_documents_use_business_style_content_and_are_readable(self) -> None:
        for path in sorted(self.root.rglob("*")):
            if not path.is_file():
                continue
            with self.subTest(path=path.relative_to(self.root)):
                docs = load_file(path)
                self.assertGreater(len(docs), 0)
                text = "\n".join(doc.page_content for doc in docs)
                self.assertTrue(text.strip())
                self.assertNotRegex(text, BANNED_SAMPLE_WORDS)
                non_empty_units = [line for line in re.split(r"\n+", text) if line.strip()]
                if path.suffix.lower() in {".csv", ".xlsx"}:
                    self.assertGreaterEqual(len(non_empty_units), 3)
                else:
                    self.assertGreaterEqual(len(non_empty_units), 3)


if __name__ == "__main__":
    unittest.main()
