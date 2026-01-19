# -*- coding: utf-8 -*-
{
    'name': 'ISEP Admission CSV Export',
    'version': '16.0.1.0.0',
    'summary': 'Exportar admisiones a CSV',
    'description': """
        Este módulo permite exportar las admisiones (op.admission) seleccionadas a un archivo CSV.
        Agrega una acción en el menú Acción de la vista de Admisiones.
    """,
    'author': 'ISEP',
    'category': 'Education',
    'depends': [
        'openeducat_core',
        'openeducat_admission',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/admission_csv_export_wizard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
