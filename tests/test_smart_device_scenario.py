from __future__ import annotations

import csv
import unittest
from pathlib import Path

from qa_core.indexing.document_loaders import load_file
from qa_core.scenarios.registry import get_scenario_registry
from qa_core.intent.classifier import infer_source


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

    def test_faq_uses_four_sources_and_desensitized_content(self) -> None:
        faq_path = Path(self.scenario.faq_csv_path)
        with faq_path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual({row["source"] for row in rows}, set(self.scenario.valid_sources))
        self.assertTrue(rows)
        self.assertTrue(all("虚构" in row["answer"] or "脱敏" in row["answer"] for row in rows))

    def test_sample_documents_cover_original_supported_formats(self) -> None:
        files = [path for path in self.root.rglob("*") if path.is_file()]
        suffixes = {path.suffix.lower() for path in files}
        self.assertTrue({".md", ".csv", ".xlsx", ".docx", ".pptx", ".pdf"}.issubset(suffixes))
        source_dirs = {path.parent.name for path in files}
        self.assertTrue({"product_data", "development_data", "support_data", "quality_data"}.issubset(source_dirs))

    def test_all_sample_formats_are_readable_by_existing_loader(self) -> None:
        for path in sorted(self.root.rglob("*")):
            if not path.is_file():
                continue
            with self.subTest(path=path.name):
                docs = load_file(path)
                self.assertGreater(len(docs), 0)
                text = "\n".join(doc.page_content for doc in docs)
                self.assertTrue(text.strip())
                self.assertRegex(text, r"虚构|脱敏|Fictional|desensitized")


if __name__ == "__main__":
    unittest.main()
