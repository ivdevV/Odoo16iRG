{
    'name': 'iRG Gradebook Moodle Wizard',
    'version': '16.0.1.0.0',
    'category': 'Website/eLearning',
    'summary': 'Botón en la libreta de calificaciones para traer notas de Moodle vía wizard',
    'description': """
Sincronización puntual Moodle -> libreta de calificaciones (isep_gradebook)
===========================================================================
Botón «Sincronizar con Moodle» en la libreta de un alumno. Abre un wizard
que muestra, por asignatura, las actividades evaluativas encontradas en
Moodle (mapeo a nivel de actividad, importado del flujo n8n) y la nota que
se escribirá. Al confirmar, hace upsert de líneas app.gradebook.result
tipadas (quiz -> exam, tarea -> assignment) marcadas con is_moodle.
    """,
    'author': 'iRG',
    'depends': ['isep_gradebook', 'irg_moodle_grades_sync'],
    'data': [
        'security/ir.model.access.csv',
        'views/moodle_map_views.xml',
        'views/moodle_sync_wizard_views.xml',
        'views/app_gradebook_student_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
