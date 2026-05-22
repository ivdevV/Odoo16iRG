# -*- coding: utf-8 -*-
{
    'name': 'IRG Portal Student Fix',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Corrige el error de acceso 403 al iniciar sesión en el portal del alumno',
    'description': """
        Evita errores de control de acceso (403 Forbidden AccessError) sobre op.subject,
        op.student.course y app.gradebook.subject al renderizar el menú del portal y el dashboard.
        Sobreescribe los métodos de cómputo del progreso total y de curso para ejecutarse con sudo().
    """,
    'author': 'iRG',
    'website': '',
    'depends': [
        'isep_student_filter',
        'isep_gradebook',
    ],
    'data': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
