# -*- coding: utf-8 -*-
{
    'name': 'iRG - Visibilidad de Asignaturas Online en Portal',
    'summary': 'Aplica restricciones de visibilidad de asignaturas y vencimiento para cursos online',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'author': 'iRG Developer',
    'license': 'LGPL-3',
    'depends': [
        'isep_elearning_custom',
        'irg_op_subject_visibility',
        'irg_online_subject_opening',
    ],
    'data': [
        'templates/portal_online_visibility_tmpl.xml',
    ],
    'installable': True,
}
