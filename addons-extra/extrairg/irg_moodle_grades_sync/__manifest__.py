{
    'name': 'iRG Moodle Grades Sync',
    'version': '16.0.1.0.0',
    'category': 'Website/eLearning',
    'summary': 'Sincroniza notas de Moodle hacia OpenEduCat en Odoo',
    'description': """
Sincronización de notas Moodle -> Odoo (OpenEduCat)
===================================================

Trae las notas finales por asignatura desde Moodle a un modelo ligero en Odoo.

Resuelve dos fricciones reales:
  * Los nombres de asignatura difieren entre Odoo y Moodle -> tabla de mapeo
    intermedia curso-Moodle <-> asignatura-Odoo (irg.moodle.subject.map).
  * Los correos difieren entre campus -> emparejamiento de alumno en cadena
    (md_id -> correo -> nombre normalizado) con cola de revisión manual.

Reutiliza la infraestructura del módulo odoo_moodle_connector (credenciales,
patrón de service class con requests, res.partner.md_id).
    """,
    'author': 'iRG',
    'depends': ['odoo_moodle_connector', 'openeducat_core'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/subject_map_views.xml',
        'views/student_map_views.xml',
        'views/grade_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
