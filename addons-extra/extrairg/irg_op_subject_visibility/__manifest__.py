{
    'name': 'iRG - Visibilidad de Asignaturas por Lote',
    'summary': 'Permite especificar para qué lotes es visible una asignatura en el portal eLearning',
    'description': """
        Extiende op.subject con:
        - Campo booleano "visible_all_course_batches" (default True) para indicar si la
          asignatura es visible para todos los lotes del curso.
        - Campo Many2many "batch_visibility_ids" para seleccionar lotes específicos cuando
          la visibilidad general está desactivada.
        - Campo computed "effective_batch_ids" que resuelve los lotes efectivos.
        - Restricción de acceso en el portal eLearning (slide.channel) basada en el lote
          activo del estudiante.
    """,
    'version': '16.0.1.0.0',
    'category': 'Education',
    'author': 'iRG Developer',
    'license': 'LGPL-3',
    'depends': [
        'openeducat_core',
        'irg_op_subject_multi_course',
        'isep_elearning_custom',
    ],
    'data': [
        'views/op_subject_views.xml',
        'templates/subject_visibility_tmpl.xml',
    ],
    'installable': True,
    'application': False,
}
