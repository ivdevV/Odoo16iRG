# -*- coding: utf-8 -*-
{
    'name': 'iRG Batch Export (CSV & PDF)',
    'version': '16.0.1.1.0',
    'summary': 'Exportar estudiantes de un lote a CSV y PDF',
    'description': """
        Este módulo permite exportar los estudiantes de un lote (op.batch) a:
        - Archivo CSV
        - Reporte PDF con información detallada del grupo
        Agrega acciones en el menú Acción del formulario de Lotes.
    """,
    'author': 'iRG',
    'category': 'Education',
    'depends': [
        'openeducat_core',
        'openeducat_admission',
        'isep_sign_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/batch_csv_export_wizard_view.xml',
        'report/batch_students_report.xml',
        'report/batch_students_template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
