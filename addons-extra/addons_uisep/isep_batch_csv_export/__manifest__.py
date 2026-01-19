# -*- coding: utf-8 -*-
{
    'name': 'ISEP Batch CSV Export',
    'version': '16.0.1.0.0',
    'summary': 'Exportar estudiantes de un lote a CSV',
    'description': """
        Este módulo permite exportar los estudiantes de un lote (op.batch) a un archivo CSV.
        Agrega una acción en el menú Acción del formulario de Lotes.
    """,
    'author': 'ISEP',
    'category': 'Education',
    'depends': [
        'openeducat_core',
        'openeducat_admission',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/batch_csv_export_wizard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
