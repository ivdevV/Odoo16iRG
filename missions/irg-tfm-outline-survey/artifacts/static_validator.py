import ast
import csv
import json
from pathlib import Path
from xml.etree import ElementTree


HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
ADDON = REPO / 'addons-extra/extrairg/irg_tfm_convocatorias'


def text(relative):
    path = ADDON / relative
    assert path.is_file(), 'missing: %s' % relative
    return path.read_text(encoding='utf-8-sig')


manifest = ast.literal_eval(text('__manifest__.py'))
assert 'survey' in manifest['depends']
assert manifest['version'] == '16.0.1.1.0'

required = (
    'models/irg_tfm_esquema.py',
    'models/survey_question.py',
    'models/survey_survey.py',
    'models/survey_user_input.py',
    'models/res_config_settings.py',
    'data/tfm_outline_survey.xml',
    'security/irg_tfm_security.xml',
    'views/survey_tfm_views.xml',
    'views/res_config_settings_views.xml',
    'tests/test_tfm_outline_survey.py',
)
for relative in required:
    text(relative)

for path in ADDON.rglob('*.py'):
    ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
for path in ADDON.rglob('*.xml'):
    ElementTree.parse(path)

model_source = text('models/irg_tfm_esquema.py')
delivery_source = text('models/irg_tfm_entrega.py')
portal_source = text('controllers/portal.py')
portal_xml = text('views/tfm_portal_templates.xml')
portal_tree = ElementTree.fromstring(portal_xml)
security_xml = text('security/irg_tfm_security.xml')
data_xml = text('data/tfm_outline_survey.xml')
tests = text('tests/test_tfm_outline_survey.py')
survey_source = text('models/survey_survey.py')
survey_input_source = text('models/survey_user_input.py')

contracts = {
    'survey_template_only': (
        'survey.user_input' not in model_source
        and 'survey.user_input' not in portal_source
        and '/survey/' not in portal_source
    ),
    'native_survey_attempts_blocked': all((
        'irg_tfm_template_only' in survey_source,
        'def _create_answer(' in survey_source,
        'irg_tfm_template_only' in survey_input_source,
        "<field name=\"access_mode\">token</field>" in data_xml,
        "<field name=\"irg_tfm_template_only\" eval=\"True\"/>" in data_xml,
        'test_native_survey_url_cannot_create_an_attempt' in tests,
    )),
    'private_models': all(name in model_source for name in (
        "_name = 'irg.tfm.esquema'",
        "_name = 'irg.tfm.esquema.pregunta'",
        "_name = 'irg.tfm.esquema.opcion'",
    )),
    'optimistic_revision': all(term in model_source for term in (
        'revision', 'FOR UPDATE', 'otra pestaña',
    )),
    'lock_order': (
        '_irg_lock_submission_configuration' in model_source
        and delivery_source.index('SELECT id FROM irg_tfm_convocatoria')
        < delivery_source.index('SELECT id FROM op_course')
        < delivery_source.index('SELECT id FROM tesis_model')
    ),
    'limits': all(term in model_source for term in (
        '_MAX_CHAR_ANSWER = 500',
        '_MAX_TEXT_ANSWER = 20000',
        '_MAX_OPTIONS = 100',
        '_MAX_SELECTED_OPTIONS = 50',
        '_MAX_QUESTIONS = 100',
        '_MAX_TOTAL_TEXT = 100000',
    )),
    'three_steps': all(term in data_xml for term in (
        'proposal', 'approach', 'results',
    )),
    'editable_frozen_section_titles': all(term in portal_source for term in (
        '_frozen_outline_step_labels', 'question.section_title',
    )),
    'portal_posts_csrf': (
        portal_source.count("methods=['POST']") >= 3
        and portal_source.count('csrf=True') >= 3
    ),
    'portal_multifield_steps': all(term in portal_xml for term in (
        'Guardar borrador', 'Siguiente', 'Anterior',
        'Revisar y enviar Esquema',
    )),
    'escaped_student_output': 't-raw="question.answer_text"' not in portal_xml,
    'qweb_t_field_uses_html_nodes': not any(
        element.tag == 't' and 't-field' in element.attrib
        for element in portal_tree.iter()
    ),
    'reviewer_group': (
        'group_tfm_reviewer' in security_xml
        and "[('state', '=', 'done')]" in security_xml
    ),
    'no_notifying_chatter': all(term in model_source for term in (
        "self.env['mail.message']", "'partner_ids': False",
    )) and 'message_post(' not in model_source,
    'legacy_file_outline_read_only': (
        "if stage == 'outline':" in delivery_source
        and 'Los nuevos Esquemas se envían mediante el cuestionario TFM.' in delivery_source
        and 'Los nuevos Esquemas se registran mediante el cuestionario TFM.'
        in text('models/tesis_model.py')
    ),
    'immutability': all(term in model_source for term in (
        'def write(', 'def unlink(', 'def copy(', 'TFM outline history is immutable',
    )),
    'tdd_scope': len([
        line for line in tests.splitlines() if line.strip().startswith('def test_')
    ]) >= 9,
}
failed = [name for name, result in contracts.items() if not result]
assert not failed, failed

with (ADDON / 'security/ir.model.access.csv').open(encoding='utf-8-sig', newline='') as stream:
    rows = list(csv.DictReader(stream))
assert not any(row['group_id:id'] == 'base.group_portal' for row in rows)

print(json.dumps({'status': 'pass', 'contracts': len(contracts)}, indent=2))
