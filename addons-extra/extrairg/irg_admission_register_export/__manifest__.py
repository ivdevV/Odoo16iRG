# -*- coding: utf-8 -*-
{
    'name': 'iRG Admission Register Export',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Exportar admisiones de un registro a CSV o XLSX desde el menú de acciones',
    'author': 'iRG',
    'depends': [
        'openeducat_admission',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/admission_export_wizard_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
