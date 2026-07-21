import ast
import csv
import pathlib
import unittest
import xml.etree.ElementTree as ET


ADDON = pathlib.Path(__file__).resolve().parents[1]


class TestSafeMergeStaticContract(unittest.TestCase):
    def test_required_addon_files_exist(self):
        required = {
            "__init__.py",
            "__manifest__.py",
            "models/__init__.py",
            "models/res_partner.py",
            "models/merge_audit.py",
            "wizard/__init__.py",
            "wizard/partner_safe_merge_wizard.py",
            "security/ir.model.access.csv",
            "views/res_partner_views.xml",
            "views/partner_safe_merge_wizard_views.xml",
            "views/merge_audit_views.xml",
        }
        missing = sorted(path for path in required if not (ADDON / path).is_file())
        self.assertFalse(missing, "Missing addon files: %s" % ", ".join(missing))

    def test_python_xml_and_csv_are_parseable(self):
        for source in ADDON.rglob("*.py"):
            ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for source in ADDON.rglob("*.xml"):
            ET.parse(source)
        for source in ADDON.rglob("*.csv"):
            with source.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.reader(stream))
            self.assertGreaterEqual(len(rows), 2, str(source))

    def test_dangerous_merge_primitives_are_absent(self):
        production = "\n".join(
            source.read_text(encoding="utf-8")
            for folder in ("models", "wizard")
            for source in (ADDON / folder).rglob("*.py")
        )
        self.assertNotIn("._merge(", production)
        self.assertNotIn("cr.commit(", production)
        self.assertNotIn("DELETE FROM", production.upper())

    def test_closed_allowlist_and_security_guards_are_declared(self):
        service = (ADDON / "wizard/partner_safe_merge_wizard.py").read_text(
            encoding="utf-8"
        )
        partner = (ADDON / "models/res_partner.py").read_text(encoding="utf-8")
        audit = (ADDON / "models/merge_audit.py").read_text(encoding="utf-8")
        for token in (
            "TRANSFER_ALLOWLIST",
            "RECALCULATE_ALLOWLIST",
            "CONSERVE_ALLOWLIST",
            "POLYMORPHIC_ALLOWLIST",
            "base.group_system",
            "FOR UPDATE",
            "preview_hash",
        ):
            self.assertIn(token, service)
        self.assertIn("irg_merged_into_partner_id", partner)
        self.assertIn("_irg_safe_merge_service", partner)
        self.assertIn("Only the safe-merge service", audit)

    def test_reviewed_plan_is_bound_and_closed_over_m2m(self):
        service = (ADDON / "wizard/partner_safe_merge_wizard.py").read_text(
            encoding="utf-8"
        )
        for token in (
            "APPROVED_M2M_ALLOWLIST",
            "_inventory_many2many",
            "_lock_approved_m2m",
            '"decisions": payload["decisions"]',
            '"student_user_links": payload["student_user_links"]',
            "_lock_generated_plan",
            "self.env.su",
            "_inventory_allowlisted_transients",
            "BUSINESS_COLLISION_POLICIES",
        ):
            self.assertIn(token, service)

    def test_audit_declares_usable_before_and_after_snapshots(self):
        audit = (ADDON / "models/merge_audit.py").read_text(encoding="utf-8")
        service = (ADDON / "wizard/partner_safe_merge_wizard.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("before_snapshot_json", audit)
        self.assertIn("after_snapshot_json", audit)
        self.assertIn('"before_snapshot_json"', service)
        self.assertIn('"after_snapshot_json"', service)

    def test_conflicts_are_editable_before_and_locked_after_final_preview(self):
        view = (ADDON / "views/partner_safe_merge_wizard_views.xml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "attrs=\"{'readonly': [('preview_ready', '=', True)]}\"", view
        )

    def test_third_review_requires_runtime_strength_tests(self):
        tests = (ADDON / "tests/test_partner_safe_merge.py").read_text(
            encoding="utf-8"
        )
        for token in (
            "base.user_admin",
            "self.assertFalse(admin_env.su)",
            "threading.Event",
            "threading.Thread",
            "registry.cursor()",
            "concurrent_same_confirmation",
            "concurrent_inverse_confirmation",
            'self.env["res.partner.bank"].create',
            "test_source_account_move_blocks_preview",
            'self.env["account.move"].create',
            'r"account\\.move\\.(commercial_partner_id|partner_id)"',
            "master_street_before",
            "source_follower_id",
        ):
            self.assertIn(token, tests)


if __name__ == "__main__":
    unittest.main()
