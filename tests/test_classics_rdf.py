# -*- coding: utf-8 -*-
import json
import shutil
import unittest
from pathlib import Path

from tools.export_rdf import export

ROOT = Path(__file__).resolve().parent.parent


class ClassicsRdfTest(unittest.TestCase):
    def setUp(self):
        self.out = ROOT / "tests" / "_tmp_classics"

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)

    def test_export_one_classic(self):
        kb = ROOT / "workspaces" / "sunzi" / "data" / "kb.json"
        result = export(kb, self.out, "urn:mcai:classic:sunzi:", "sunzi",
                        ontology_label_zh="孙子兵法知识资产词表",
                        scheme_label_zh="孙子兵法标准词表")
        self.assertEqual(result["bad"], 0)
        self.assertGreater(result["triples"], 100)
        ttl = Path(result["ttl"]).read_text(encoding="utf-8")
        self.assertIn("urn:mcai:classic:sunzi:", ttl)
        self.assertIn("skos/core#prefLabel", ttl)

    def test_manifest_if_present(self):
        manifest = ROOT / "dist_pkg" / "classics-rdf" / "manifest.json"
        if not manifest.exists():
            self.skipTest("manifest not generated yet")
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertFalse(data["published"])
        self.assertGreaterEqual(len(data["works"]), 3)
        for work in data["works"]:
            self.assertEqual(work["bad_triples"], 0)
            self.assertTrue(work["verify_ok"])
            self.assertGreater(work["triples"], 100)


if __name__ == "__main__":
    unittest.main()
