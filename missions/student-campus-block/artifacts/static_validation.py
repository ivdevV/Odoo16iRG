import ast
from pathlib import Path

import xml.etree.ElementTree as etree


module = Path("addons-extra/extrairg/irg_student_campus_block")
manifest = ast.literal_eval((module / "__manifest__.py").read_text())
assert manifest["version"].startswith("16.0.")
assert manifest["depends"] == ["openeducat_core"]
assert manifest["license"] == "LGPL-3"

for path in module.rglob("*.py"):
    ast.parse(path.read_text(), filename=str(path))

view_path = module / "views/op_student_view.xml"
view = etree.parse(str(view_path))
assert view.findall(".//field[@name='inherit_id'][@ref='openeducat_core.view_op_student_form']")
for action in ("action_block_campus_access", "action_unblock_campus_access"):
    buttons = view.findall(".//button[@name='%s']" % action)
    assert len(buttons) == 1
    button = buttons[0]
    assert button.get("type") == "object"
    assert button.get("groups") == "openeducat_core.group_op_back_office_admin"
    assert "user_id" in button.get("attrs", "")
    assert "irg_campus_blocked" in button.get("attrs", "")
    assert "No afecta a Moodle" in button.get("confirm", "")
ribbons = view.findall(".//widget[@name='web_ribbon'][@bg_color='bg-danger']")
assert len(ribbons) == 1
assert "('active', '=', False)" in ribbons[0].get("attrs", "")

model_source = (module / "models/op_student.py").read_text().lower()
assert "moodle" not in model_source
assert model_source.count(".sudo()") == 1
assert ".sudo().write({\"active\": active})" in model_source

print("STATIC_OK manifest, Python AST, XML inheritance/actions/groups/ribbon")
print("SECURITY_OK exactly one sudo(), limited to res.users active write")
print("MOODLE_SCOPE_OK no Moodle dependency or model integration; UI explicitly says unaffected")
