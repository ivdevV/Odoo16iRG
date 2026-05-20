# -*- coding: utf-8 -*-
{
    'name': 'Selector de Correo de Bienvenida',
    'version': '16.0.1.0.0',
    'category': 'OpenEduCat',
    'summary': 'Selecciona la plantilla de correo de bienvenida según la modalidad del lote',
    'author': 'iRG',
    'depends': ['isep_elearning_custom', 'isep_student_migration', 'isep_sale_order_admissions'],
    'data': [
        'data/mail_template_online.xml',
    ],
    'installable': True,
    'application': False,
}
