# -*- coding: utf-8 -*-
{
    'name': 'IRG - Ocultar Servicios Adicionales en Portal',
    'summary': 'Oculta la sección de Servicios Adicionales en el portal (/my/home) al instalar el módulo.',
    'version': '16.0.1.0.0',
    'category': 'Website',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': [
        'portal',
        'isep_openeducat_reports',
    ],
    'data': [
        'views/portal_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
}
