# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


def _load_cif():
    path = Path(__file__).resolve().parents[1] / "cif.py"
    spec = importlib.util.spec_from_file_location("irg_practice_center_cif_cif", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestResolveCenterCif(unittest.TestCase):

    def test_center_cif_wins_over_partner_vat(self):
        resolve = _load_cif().resolve_center_cif
        self.assertEqual(resolve("B12345678", "A00000000"), "B12345678")

    def test_blank_cif_falls_back_to_partner_vat(self):
        resolve = _load_cif().resolve_center_cif
        self.assertEqual(resolve(False, "B12345678"), "B12345678")
        self.assertEqual(resolve("", "B12345678"), "B12345678")
        self.assertEqual(resolve("   ", "B12345678"), "B12345678")

    def test_cif_is_stripped(self):
        resolve = _load_cif().resolve_center_cif
        self.assertEqual(resolve("  B12345678  ", False), "B12345678")

    def test_missing_values_return_false(self):
        resolve = _load_cif().resolve_center_cif
        self.assertFalse(resolve(False, False))
        self.assertFalse(resolve(None, None))
        self.assertFalse(resolve("  ", ""))


if __name__ == "__main__":
    unittest.main()
