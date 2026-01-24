# -*- coding: utf-8 -*-
{
    'name': 'ISEP Admission Register CSV Export',
    'version': '16.0.1.0.0',
    'summary': 'Exportar admisiones de un registro de admisión a CSV',
    'description': """
        Este módulo permite exportar las admisiones de un registro de admisión (op.admission.register) a un archivo CSV.
        Agrega una acción en el menú Acción del formulario de Registros de Admisión.
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
