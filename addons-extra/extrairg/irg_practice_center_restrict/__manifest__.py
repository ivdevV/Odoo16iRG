# -*- coding: utf-8 -*-
{
    'name': 'IRG Practice Center Restrict',
    'version': '16.0.1.0.0',
    'summary': 'Oculta los centros de prácticas a los alumnos (usuarios de portal)',
    'description': (
        "Restringe a los usuarios de tipo portal (alumnos) el acceso de lectura "
        "y selección de centros de prácticas en el portal web. Solo el staff "
        "interno puede ver y gestionar los centros en el backend y asignarlos "
        "a las solicitudes. El alumno sigue pudiendo enviar su solicitud de "
        "práctica; el coordinador le asigna el centro manualmente."
    ),
    'author': 'IRG',
    'category': 'Education',
    'depends': ['isep_practices_2'],
    'data': [
        'views/templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
