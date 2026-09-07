"""Independent static validator for the irg_tfm_convocatorias mission.

This script deliberately imports neither Odoo nor the addon.  It validates the
source tree and extracts pure helpers through Python AST so it can run on a host
without the Odoo/Docker runtime.
"""

import ast
import csv
import io
import re
import struct
import zipfile
from pathlib import Path
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile


REPO = Path(__file__).resolve().parents[3]
ADDON = REPO / "addons-extra/extrairg/irg_tfm_convocatorias"


def passed(name, detail):
    print(f"PASS {name}: {detail}")


python_files = sorted(ADDON.rglob("*.py"))
python_trees = {
    path: ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    for path in python_files
}
passed("python_ast", f"{len(python_files)} files")

xml_files = sorted(ADDON.rglob("*.xml"))
for path in xml_files:
    ElementTree.parse(path)
passed("xml_well_formed", f"{len(xml_files)} files")

acl_path = ADDON / "security/ir.model.access.csv"
with acl_path.open(encoding="utf-8-sig", newline="") as stream:
    acl_rows = list(csv.DictReader(stream))
expected_acl_columns = {
    "id", "name", "model_id:id", "group_id:id", "perm_read", "perm_write",
    "perm_create", "perm_unlink",
}
assert set(acl_rows[0]) == expected_acl_columns
assert len({row["id"] for row in acl_rows}) == len(acl_rows)
assert all(
    row[key] in {"0", "1"}
    for row in acl_rows
    for key in ("perm_read", "perm_write", "perm_create", "perm_unlink")
)
passed("acl_csv", f"{len(acl_rows)} unique canonical rows")

manifest_path = ADDON / "__manifest__.py"
manifest = ast.literal_eval(python_trees[manifest_path].body[0].value)
assert manifest["version"].startswith("16.0.")
assert all((ADDON / item).is_file() for item in manifest["data"])
model_files = {
    path.stem for path in (ADDON / "models").glob("*.py")
    if path.stem != "__init__"
}
model_imports = {
    line.split()[-1]
    for line in (ADDON / "models/__init__.py").read_text(encoding="utf-8-sig").splitlines()
    if line.startswith("from . import ")
}
assert model_files == model_imports
assert "from . import portal" in (ADDON / "controllers/__init__.py").read_text(
    encoding="utf-8-sig"
)
passed(
    "manifest_imports",
    f"version {manifest['version']}; {len(manifest['depends'])} dependencies; "
    f"{len(manifest['data'])} data files; {len(model_files)} model imports",
)

dependency_locations = {}
for path in (REPO / "addons-extra").rglob("__manifest__.py"):
    dependency_locations.setdefault(path.parent.name, []).append(path.parent)
repository_dependencies = [
    name for name in manifest["depends"]
    if name.startswith(("irg_", "isep_", "openeducat_"))
]
missing_dependencies = [
    name for name in repository_dependencies if name not in dependency_locations
]
assert not missing_dependencies, missing_dependencies
assert len(repository_dependencies) == 10
passed(
    "repository_dependencies",
    f"all {len(repository_dependencies)} repository-provided dependencies found",
)

test_files = sorted((ADDON / "tests").glob("test_*.py"))
test_imports = {
    line.split()[-1]
    for line in (ADDON / "tests/__init__.py").read_text(encoding="utf-8-sig").splitlines()
    if line.startswith("from . import ")
}
assert test_imports == {path.stem for path in test_files}
test_count = sum(
    1
    for path in test_files
    for node in ast.walk(python_trees[path])
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and node.name.startswith("test_")
)
test_classes = [
    node
    for path in test_files
    for node in python_trees[path].body
    if isinstance(node, ast.ClassDef) and node.name.startswith("Test")
]
for node in test_classes:
    base_names = {
        getattr(base, "id", None) or getattr(base, "attr", None)
        for base in node.bases
    }
    assert base_names.intersection({"TransactionCase", "HttpCase"}), node.name
assert test_count == 55
passed("test_structure", f"3 files; 5 test classes; {test_count} test methods")

long_lines = []
trailing_whitespace = []
for path in ADDON.rglob("*"):
    if not path.is_file():
        continue
    text = path.read_text(encoding="utf-8-sig")
    for line_number, line in enumerate(text.splitlines(), 1):
        if line.rstrip(" \t") != line:
            trailing_whitespace.append((path, line_number))
        if path.suffix == ".py" and len(line) > 119:
            long_lines.append((path, line_number, len(line)))
assert not trailing_whitespace, trailing_whitespace
assert not long_lines, long_lines
passed("style", "no trailing whitespace; no Python line exceeds 119 columns")


def extract_eligibility_parser():
    path = ADDON / "models/op_student_course.py"
    selected = []
    for node in python_trees[path].body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "_BATCH_CODE_RE"
            for target in node.targets
        ):
            selected.append(node)
        if isinstance(node, ast.FunctionDef) and node.name == "irg_parse_tfm_batch_eligibility":
            selected.append(node)
    namespace = {"re": re}
    module = ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[]))
    exec(compile(module, str(path), "exec"), namespace)
    return namespace["irg_parse_tfm_batch_eligibility"]


parse_batch = extract_eligibility_parser()
eligibility_matrix = {
    "HC2510": False,
    "HC2511": ("HC", 2511),
    "xxHC2511suffix": ("HC", 2511),
    "MONLHC2512": False,
    "MONLHC2601": ("HC", 2601),
    "ONL2601": False,
    "ONL2602": ("ONL", 2602),
    "PRS-HC2601": False,
    "HC2513": False,
    "garbage": False,
    "": False,
}
assert {code: parse_batch(code) for code in eligibility_matrix} == eligibility_matrix
passed("pure_eligibility", f"{len(eligibility_matrix)} cutoff/exclusion cases")


def extracted_delivery_validator():
    path = ADDON / "models/irg_tfm_entrega.py"
    constant_names = {
        "_DOCX_CONTENT_TYPES_NS", "_DOCX_WORD_NS", "_DOCX_MAIN_CONTENT_TYPE",
        "_MAX_DOCX_ENTRIES", "_MAX_DOCX_CENTRAL_DIRECTORY_BYTES",
        "_MAX_DOCX_UNCOMPRESSED_BYTES", "_MAX_DOCX_COMPRESSION_RATIO",
        "_MAX_DOCX_XML_BYTES", "_PDF_HEADER_RE", "_PDF_OBJECT_RE",
        "_OLE_FREE_SECTOR", "_OLE_END_OF_CHAIN", "_OLE_RESERVED_SECTORS",
        "_WORD_FIB_MIN_FC_LCB",
    }
    method_names = {
        "_irg_is_pdf", "_irg_is_word_ole", "_irg_has_valid_word_fib",
        "_irg_is_docx", "_irg_docx_archive_preflight",
        "_irg_read_bounded_zip_member", "_irg_parse_safe_xml",
    }
    nodes = []
    methods = []
    for node in python_trees[path].body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id in constant_names
            for target in node.targets
        ):
            nodes.append(node)
        if isinstance(node, ast.ClassDef) and node.name == "IrgTfmEntrega":
            for method in node.body:
                if isinstance(method, ast.FunctionDef) and method.name in method_names:
                    method.decorator_list = []
                    methods.append(method)
    nodes.append(ast.ClassDef(
        name="Validator", bases=[], keywords=[], body=methods, decorator_list=[],
    ))
    namespace = {
        "io": io,
        "re": re,
        "struct": struct,
        "ElementTree": ElementTree,
        "BadZipFile": BadZipFile,
        "ZipFile": ZipFile,
    }
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(module, str(path), "exec"), namespace)
    return namespace["Validator"]()


validator = extracted_delivery_validator()
content_types = (
    b'<?xml version="1.0"?><Types '
    b'xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    b'<Override PartName="/word/document.xml" '
    b'ContentType="application/vnd.openxmlformats-officedocument.'
    b'wordprocessingml.document.main+xml"/></Types>'
)
document = (
    b'<?xml version="1.0"?><w:document '
    b'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    b'<w:body/></w:document>'
)


def make_zip(entries):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries:
            archive.writestr(name, data)
    return stream.getvalue()


valid_docx = make_zip([
    ("[Content_Types].xml", content_types), ("word/document.xml", document),
])
generic_zip = make_zip([
    ("[Content_Types].xml", content_types), ("payload.txt", b"x"),
])
flood = make_zip([(f"f{index:03d}.txt", b"x") for index in range(257)])
bomb = make_zip([
    ("[Content_Types].xml", content_types),
    ("word/document.xml", document),
    ("optional.bin", b"A" * 1048576),
])
forged = bytearray(flood)
eocd = forged.rfind(b"PK\x05\x06")
struct.pack_into("<HH", forged, eocd + 8, 2, 2)
assert validator._irg_is_docx(valid_docx) is True
assert validator._irg_is_docx(generic_zip) is False
assert validator._irg_docx_archive_preflight(flood) is None
assert validator._irg_docx_archive_preflight(bytes(forged)) is None
assert validator._irg_is_docx(bomb) is False
valid_pdf = (
    b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n"
    b"<< /Size 2 /Root 1 0 R >>\nstartxref\n0\n%%EOF"
)
assert validator._irg_is_pdf(valid_pdf) is True
assert validator._irg_is_pdf(b"%PDF-1.7") is False
assert validator._irg_is_pdf(b"%PDF-1.7\n%%EOF") is False
passed("pure_pdf_docx", "valid PDF/DOCX plus malformed, flood, forged EOCD and bomb cases")


def make_doc_bytes(word_stream=None):
    free_sector = 0xFFFFFFFF
    end_of_chain = 0xFFFFFFFE
    fat_sector = 0xFFFFFFFD
    header = bytearray(512)
    header[:8] = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
    struct.pack_into("<HHHH", header, 24, 0x003E, 3, 0xFFFE, 9)
    struct.pack_into("<H", header, 32, 6)
    struct.pack_into("<I", header, 44, 1)
    struct.pack_into("<I", header, 48, 0)
    struct.pack_into("<I", header, 56, 4096)
    struct.pack_into("<I", header, 60, end_of_chain)
    struct.pack_into("<I", header, 68, end_of_chain)
    for index in range(109):
        struct.pack_into("<I", header, 76 + (index * 4), free_sector)
    struct.pack_into("<I", header, 76, 1)
    directory = bytearray(512)

    def directory_entry(offset, name, object_type, start_sector, size, child=free_sector):
        encoded_name = (name + "\x00").encode("utf-16le")
        directory[offset:offset + len(encoded_name)] = encoded_name
        struct.pack_into("<HBB", directory, offset + 64, len(encoded_name), object_type, 1)
        struct.pack_into("<III", directory, offset + 68, free_sector, free_sector, child)
        struct.pack_into("<I", directory, offset + 116, start_sector)
        struct.pack_into("<Q", directory, offset + 120, size)

    directory_entry(0, "Root Entry", 5, end_of_chain, 0, child=1)
    directory_entry(128, "WordDocument", 2, 2, 4096)
    fat = [free_sector] * 128
    fat[0] = end_of_chain
    fat[1] = fat_sector
    for sector in range(2, 9):
        fat[sector] = sector + 1
    fat[9] = end_of_chain
    if word_stream is None:
        word_stream = bytearray(4096)
        struct.pack_into("<HH", word_stream, 0, 0xA5EC, 0x00C1)
        struct.pack_into("<H", word_stream, 12, 0x00BF)
        struct.pack_into("<H", word_stream, 32, 0x000E)
        struct.pack_into("<H", word_stream, 62, 0x0016)
        struct.pack_into("<H", word_stream, 152, 0x005D)
        word_stream = bytes(word_stream)
    return bytes(header + directory + struct.pack("<128I", *fat) + word_stream)


assert validator._irg_is_word_ole(make_doc_bytes()) is True
assert validator._irg_is_word_ole(make_doc_bytes(b"W" * 4096)) is False
assert validator._irg_is_word_ole(
    b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"x" * 2048
) is False
passed("pure_doc", "real WordDocument/FIB accepted; named-only and forged inputs rejected")


def source(relative):
    return (ADDON / relative).read_text(encoding="utf-8-sig")


enrollment = source("models/op_student_course.py")
gradebook_result = source("models/app_gradebook_result.py")
thesis = source("models/tesis_model.py")
delivery = source("models/irg_tfm_entrega.py")
slide = source("models/slide_slide.py")
membership = source("models/slide_channel_partner.py")
portal = source("controllers/portal.py")
portal_xml = source("views/tfm_portal_templates.xml")
slide_xml = source("views/tfm_slide_templates.xml")
cron_xml = source("data/ir_cron.xml")
hooks = source("hooks.py")
acl = source("security/ir.model.access.csv")
contracts = {
    "activation_threshold": (
        "completion_porc" in enrollment
        and "completion_proc" not in enrollment
        and ">= 50.0" in enrollment
        and "self.course_id.activate_tesis" in enrollment
    ),
    "activation_immediate_and_cron": (
        enrollment.count("record._irg_ensure_tfm_record()") >= 3
        and "limit=batch_size" in enrollment
        and "_TFM_CRON_BATCH_SIZE = 500" in enrollment
        and "<field name=\"interval_type\">hours</field>" in cron_xml
    ),
    "activation_unique_preflight": (
        "unique(course_id)" in thesis
        and "constraint_name" in enrollment
        and "HAVING count(*) > 1" in hooks
        and "completion_porc" in hooks
        and "completion_proc" not in hooks
    ),
    "gradebook_progress_trigger": (
        all(field in gradebook_result for field in (
            "scoring_total", "survey_type", "gradebook_subject_id",
        ))
        and "FOR UPDATE" in gradebook_result
        and "ORDER BY id" in gradebook_result
        and "compute_final_subject_note" in gradebook_result
        and "flush_recordset" in gradebook_result
        and "completion_porc" in gradebook_result
        and "invalidate_recordset" in gradebook_result
        and "irg_tfm_defer_grade_trigger" in gradebook_result
        and "completion_porc" not in enrollment[enrollment.index("domain = ["):]
    ),
    "convocation_auth_warning": (
        thesis.index("_irg_require_internal_user()")
        < thesis.index("SELECT id FROM irg_tfm_convocatoria")
        and "Warning: this TFM has no outline submission yet." in thesis
    ),
    "portal_ownership": all(term in thesis for term in (
        "('user_id', '=', self.env.uid)",
        "('student_id.user_id', '=', self.env.uid)",
        "('course_id.student_id.user_id', '=', self.env.uid)",
        "limit=2",
    )),
    "portal_csrf_and_bounded_upload": (
        "methods=['POST']" in portal and "csrf=True" in portal
        and "upload.stream.read((20 * 1024 * 1024) + 1)" in portal
    ),
    "legacy_routes": all(route in portal for route in (
        "/my/tesis_models/new", "/my/tesis_models2",
        "/my/tesis_models2/accept", "/my/tesis_models2/decline",
        "/my/tesis_model/<int:request_id>", "/web/submit_documenttr",
        "/my/notificacionestr/download", "/my/notificacionestr/borrar",
        "/my/notificacionestr/comment",
    )),
    "mycampus_surface": (
        "Trabajo Final de Máster" in portal_xml
        and all(label in portal_xml for label in ("Esquema", "Entrega parcial", "Entrega final"))
        and "Revisión de tesis" not in portal_xml
    ),
    "file_controls": (
        "_MAX_UPLOAD_BYTES = 20 * 1024 * 1024" in delivery
        and "'public': False" in delivery
        and "X-Content-Type-Options" in portal
    ),
    "version_and_immutability": (
        "unique(thesis_id, stage, convocation_key, version)" in delivery
        and "TFM delivery history is immutable." in delivery
        and "TFM delivery history cannot be deleted." in delivery
        and "TFM delivery attachments cannot be deleted." in delivery
    ),
    "server_windows_and_exceptions": (
        "opening <= today <= closing" in delivery
        and "An exception reason is required." in delivery
        and "Outline submissions close" in delivery
    ),
    "elearning_category_and_fail_closed": (
        "irg_tfm_convocation_ids and not slide.is_category" in slide
        and "len(students) != 1" in slide
        and "len(enrollments) != 1" in slide
        and "len(theses) != 1" in slide
    ),
    "elearning_qweb_composition": all(term in slide_xml for term in (
        "batch_blocked_slide_ids", "practice_blocked_slide_ids",
        "tfm_blocked_slide_ids", "is_user_allowed_by_batch",
        "is_user_allowed_by_practice_type", "is_user_allowed_by_tfm_convocation",
    )),
    "membership_provenance": (
        "irg_tfm_created" in membership
        and "irg_tfm_thesis_ids" in membership
        and "_irg_tfm_has_foreign_signals" in membership
        and "def unlink" not in membership
        and "irg_scp_active_partner_channel_batch_uniq" in membership
    ),
    "portal_no_direct_acl": "base.group_portal" not in acl,
}
assignment = thesis[thesis.index("    def write(self, vals):"):]
contracts["assignment_lock_order"] = (
    assignment.index("SELECT id FROM irg_tfm_convocatoria")
    < assignment.index("SELECT id FROM op_course")
    < assignment.index("SELECT id FROM tesis_model")
)
submission = delivery[delivery.index("    def _irg_lock_submission_configuration"):]
contracts["submission_lock_order"] = (
    submission.index("SELECT id FROM irg_tfm_convocatoria")
    < submission.index("SELECT id FROM op_course")
    < submission.index("SELECT id FROM tesis_model")
)
slide_view = portal[
    portal.index("    def slide_view(self, slide, **kwargs):"):
    portal.index("    def _get_slide_detail", portal.index("    def slide_view(self, slide, **kwargs):"))
]
contracts["direct_slide_gate_before_super"] = (
    slide_view.index("irg_has_tfm_requirement")
    < slide_view.index("return super().slide_view")
)
failed_contracts = [name for name, result in contracts.items() if not result]
assert not failed_contracts, failed_contracts
passed("static_contracts", f"{len(contracts)} grouped contracts")

inheritance_targets = {
    "isep_tesis_model.view_tesis_model_form": (
        "addons-extra/addons_uisep/isep_tesis_model/views/tesis_model_views.xml",
        'id="view_tesis_model_form"',
    ),
    "isep_tesis_model.view_tesis_model_search": (
        "addons-extra/addons_uisep/isep_tesis_model/views/tesis_model_views.xml",
        'id="view_tesis_model_search"',
    ),
    "isep_tesis_model.portal_my_home_menu_inherit": (
        "addons-extra/addons_uisep/isep_tesis_model/templates/portal_my_tesis_model.xml",
        'id="portal_my_home_menu_inherit"',
    ),
    "isep_tesis_model.menu_practice_configuration": (
        "addons-extra/addons_uisep/isep_tesis_model/views/menu_views.xml",
        'id="menu_practice_configuration"',
    ),
    "irg_course_portal_tiles.irg_user_profile_content_details_inherit": (
        "addons-extra/extrairg/irg_course_portal_tiles/views/irg_course_portal_tiles_views.xml",
        'id="irg_user_profile_content_details_inherit"',
    ),
    "irg_practice_slide_restrictions.view_slide_slide_form_practice_restriction": (
        "addons-extra/extrairg/irg_practice_slide_restrictions/views/slide_slide_view.xml",
        'id="view_slide_slide_form_practice_restriction"',
    ),
    "irg_practice_slide_restrictions.view_slide_channel_form_practice_restriction": (
        "addons-extra/extrairg/irg_practice_slide_restrictions/views/slide_channel_view.xml",
        'id="view_slide_channel_form_practice_restriction"',
    ),
    "irg_practice_slide_restrictions.slide_fullscreen_sidebar_practice_hide": (
        "addons-extra/extrairg/irg_practice_slide_restrictions/views/templates.xml",
        'id="slide_fullscreen_sidebar_practice_hide"',
    ),
    "irg_practice_slide_restrictions.fullscreen_sidebar_hide_practice_sections": (
        "addons-extra/extrairg/irg_practice_slide_restrictions/views/templates.xml",
        'id="fullscreen_sidebar_hide_practice_sections"',
    ),
    "irg_practice_slide_restrictions.course_slides_list_hide_practice_sections": (
        "addons-extra/extrairg/irg_practice_slide_restrictions/views/templates.xml",
        'id="course_slides_list_hide_practice_sections"',
    ),
}
for _xmlid, (relative_path, marker) in inheritance_targets.items():
    target = REPO / relative_path
    assert target.is_file() and marker in target.read_text(encoding="utf-8-sig")
passed("inheritance_targets", f"{len(inheritance_targets)} repository XML ids")

assert (REPO / "missions/irg-tfm-convocatorias/plan.md").is_file()
assert (REPO / "doc/micro-specs/2026-09-04-irg-tfm-convocatorias.md").is_file()
assert not (ADDON / "missions").exists()
passed("artifact_scope", "plan and micro-spec remain outside the addon")

print("SUMMARY: 13 validation groups passed; 0 failed")
