"""Import one-off del mapeo n8n (hoja MAP_ASIGNATURAS) a
irg.gradebook.moodle.map.

Uso (dentro de odoo shell):
    docker exec -i odoo16irg_local odoo shell -d test_irg_db <<'EOF'
    exec(open('/mnt/extra-addons/extrairg/irg_gradebook_moodle_wizard/'
              'tools/import_map_csv.py').read())
    run_import(env, '/tmp/map_asignaturas.csv')
    env.cr.commit()
    EOF

Idempotente: upsert por (op_subject_id, moodle_course_id); las líneas de
actividad se regeneran en cada import.
"""
import csv


ODOO_INTEGER_ID_MIN = 1
ODOO_INTEGER_ID_MAX = 2147483647


def run_import(env, csv_path):
    map_model = env['irg.gradebook.moodle.map']
    subject_model = env['op.subject']
    created = updated = skipped = 0
    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            try:
                subject_value = float(row['Odoo Subject ID'])
                course_value = float(row['Moodle Course ID'])
                subject_id = int(subject_value)
                course_id = int(course_value)
            except (ValueError, TypeError, KeyError, OverflowError):
                skipped += 1
                continue
            if (
                    subject_value != subject_id
                    or course_value != course_id
                    or not ODOO_INTEGER_ID_MIN <= subject_id <= ODOO_INTEGER_ID_MAX
                    or not ODOO_INTEGER_ID_MIN <= course_id <= ODOO_INTEGER_ID_MAX):
                skipped += 1
                continue
            subject = subject_model.browse(subject_id).exists()
            if not subject:
                print(f"SKIP: op.subject {subject_id} no existe "
                      f"({row.get('Odoo Subject Name')})")
                skipped += 1
                continue
            ids_raw = (row.get('Moodle IDs List') or '').strip()
            if not ids_raw:
                skipped += 1
                continue
            act_tokens = [x.strip() for x in ids_raw.split(',')]
            if not act_tokens or any(
                    not x.isdecimal() for x in act_tokens):
                skipped += 1
                continue
            act_ids = [int(x) for x in act_tokens]
            if any(
                    not ODOO_INTEGER_ID_MIN <= act_id <= ODOO_INTEGER_ID_MAX
                    for act_id in act_ids):
                skipped += 1
                continue
            names_raw = (row.get('Moodle Names Found') or '').strip()
            names = [n.strip() for n in names_raw.split('|')]
            lines = []
            for i, act_id in enumerate(act_ids):
                lines.append((0, 0, {
                    'moodle_activity_id': act_id,
                    'name': names[i] if i < len(names) else '',
                    'activity_type': 'quiz',  # MAP_ASIGNATURAS: todo Quiz
                }))
            existing = map_model.with_context(active_test=False).search([
                ('op_subject_id', '=', subject_id),
                ('moodle_course_id', '=', course_id)], limit=1)
            vals = {
                'moodle_course_name': row.get('Curso Nombre') or '',
                'line_ids': [(5, 0, 0)] + lines,
            }
            if existing:
                existing.write(vals)
                updated += 1
            else:
                map_model.create(dict(
                    vals, op_subject_id=subject_id,
                    moodle_course_id=course_id))
                created += 1
    print(f'Import mapeo: {created} creados, {updated} actualizados, '
          f'{skipped} saltados.')
