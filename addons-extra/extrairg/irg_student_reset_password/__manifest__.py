# -*- coding: utf-8 -*-
{
    'name': 'iRG Student Reset Password',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Permite a los administradores de Back Office restablecer la contraseña de un estudiante.',
    'description': """
Este módulo permite restablecer la contraseña de un estudiante directamente desde su ficha.
Genera una contraseña aleatoria utilizando el asistente de isep_update_pass_user_ext.
    """,
    'author': 'iRG',
    'website': 'https://www.raimongaja.com',
    'depends': [
        'openeducat_core',
        'isep_update_pass_user_ext',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/op_student_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
