import ast
import csv
from pathlib import Path
from xml.etree import ElementTree


root = Path('addons-extra/extrairg/irg_forum_notice_global_seen')
manifest = ast.literal_eval((root / '__manifest__.py').read_text(encoding='utf-8'))
assert manifest['version'] == '16.0.1.0.0'
assert manifest['depends'] == ['irg_forum_notice_popup']
assert manifest['data'] == [
    'security/forum_notice_seen_rules.xml',
    'security/ir.model.access.csv',
]
assets = manifest['assets']['web.assets_frontend']
parent = ('remove', 'irg_forum_notice_popup/static/src/js/forum_notice_popup.js')
replacement = 'irg_forum_notice_global_seen/static/src/js/forum_notice_popup.js'
assert assets.count(parent) == 1
assert assets.count(replacement) == 1
assert assets.index(parent) < assets.index(replacement)

with (root / 'security/ir.model.access.csv').open(
    newline='', encoding='utf-8'
) as stream:
    rows = list(csv.DictReader(stream))
assert len(rows) == 1
assert rows[0]['group_id:id'] == 'base.group_system'
assert rows[0]['model_id:id'] == 'model_irg_forum_notice_global_seen'
assert [
    rows[0][field]
    for field in ('perm_read', 'perm_write', 'perm_create', 'perm_unlink')
] == ['1', '1', '1', '1']

records = ElementTree.parse(
    root / 'security/forum_notice_seen_rules.xml'
).findall('.//record')
assert {record.attrib['id'] for record in records} == {
    'irg_forum_notice_seen_rule_user_own',
    'irg_forum_notice_seen_rule_portal_own',
    'irg_forum_notice_seen_rule_system_all',
}

normalize = lambda value: ' '.join(value.split())
readme = normalize((root / 'README.md').read_text(encoding='utf-8'))
changelog = normalize(
    Path('missions/irg_forum_notice_global_seen/CHANGELOG.md').read_text(
        encoding='utf-8'
    )
)
knowledge = normalize(
    Path(
        '.agents/knowledge/odoo_development_modding/artifacts/'
        'forum_notice_global_seen.md'
    ).read_text(encoding='utf-8')
)
source = (root / 'static/src/js/forum_notice_popup.js').read_text(
    encoding='utf-8'
)
model_source = (root / 'models/forum_notice_seen.py').read_text(
    encoding='utf-8'
)
for value in (
    'irg_forum_notice_popup',
    '## Install',
    '## Update',
    '(user_id, post_id)',
    'does not migrate, modify, or delete legacy records',
    'system administrators',
    '_irg_is_seen',
    '_irg_mark_seen',
    'docker-compose.local.yml',
    'test_irg_forum_global_seen',
    'if that request fails',
    'full page reload',
    'batch exclusion prevents discovery and marking',
    'rendered as text',
    'same-origin HTTP(S) URLs',
):
    assert value in readme, value
for value in (
    '16.0.1.0.0',
    'No legacy records are migrated, modified, or deleted',
):
    assert value in changelog, value
for value in (
    'Course-independent identity',
    'Server boundary',
    'Frontend replacement gotcha',
):
    assert value in knowledge, value
for label, content in (
    ('README', readme),
    ('CHANGELOG', changelog),
    ('knowledge', knowledge),
):
    upper = content.upper()
    for marker in ('TODO', 'TBD', 'FIXME', 'XXX', 'PLACEHOLDER'):
        assert marker not in upper, (label, marker)
assert readme.count('<database>') == 1
assert readme.count('-i irg_forum_notice_global_seen') == 2
assert readme.count('-u irg_forum_notice_global_seen') == 1

render_popup = source[
    source.index('function renderPopup('):
    source.index('async function initForumNoticePopup(')
]
inner_html_start = render_popup.index('wrapper.innerHTML')
inner_html = render_popup[
    inner_html_start:render_popup.index(';', inner_html_start) + 1
]
assert '${' not in inner_html
for untrusted_field in ('notice.title', 'notice.forum_name', 'notice.preview'):
    assert untrusted_field not in inner_html
for safe_assignment in (
    'titleNode.textContent = notice.title ||',
    'metaNode.textContent = `Foro: ${notice.forum_name}`;',
    'previewNode.textContent = notice.preview;',
):
    assert safe_assignment in render_popup
for url_contract in (
    'new URL(value, window.location.origin)',
    "['http:', 'https:'].includes(url.protocol)",
    'url.origin !== window.location.origin',
    'openBtn.href = safeUrl;',
):
    assert url_contract in source
assert 'from psycopg2.errors import UniqueViolation' in model_source
assert 'except UniqueViolation:' in model_source
assert 'except IntegrityError:' not in model_source

scan_roots = [
    Path('.agents/knowledge/odoo_development_modding/artifacts/forum_notice_global_seen.md'),
    root,
    Path('missions/irg_forum_notice_global_seen'),
    Path('.superpowers/sdd/task-5-validator-report.md'),
]
issues = []
for scan_root in scan_roots:
    paths = [scan_root] if scan_root.is_file() else scan_root.rglob('*')
    for path in paths:
        if not path.is_file():
            continue
        try:
            lines = path.read_text(encoding='utf-8').splitlines()
        except UnicodeDecodeError:
            continue
        issues.extend(
            f'{path}:{line_number}'
            for line_number, line in enumerate(lines, 1)
            if line.rstrip() != line
        )
assert not issues, issues

print('manifest_asset_security_validation: PASS')
print('documentation_content_placeholder_validation: PASS')
print('frontend_xss_and_integrity_scope_validation: PASS')
print('allowed_tree_trailing_whitespace_validation: PASS')
