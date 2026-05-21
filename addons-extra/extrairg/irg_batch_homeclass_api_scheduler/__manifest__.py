{
    'name': 'IRG Batch HomeClass API Scheduler',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Synchronize subject dates for HomeClass batches using external Calendar API',
    'description': """
        This module connects to the external CRM Calendar API to automatically schedule
        subject start dates for HomeClass batches. It matches Odoo subjects using their
        code (bloque) or name (bloqueAsignaturas) and sets their date_from to the earliest
        class date in the calendar, updating the overall batch start class date.
    """,
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'openeducat_core',
        'isep_elearning_custom',
        'isep_student_migration',
    ],
    'data': [
        'views/op_batch_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
