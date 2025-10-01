# -*- coding: utf-8 -*-
{
    'name': 'Isep Update Cert Background',
    'version': '16.2',
    'summary': """ Actualizar imagen de fondo en certificados masivamente""",
    'author': 'Breithner Aquituari',
    'website': '',
    'category': '',
    'depends': ['website_slides','isep_survey'],
    "data": [
        "security/ir.model.access.csv",
        "wizards/update_survey_background_wizard.xml"
    ],
    
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
