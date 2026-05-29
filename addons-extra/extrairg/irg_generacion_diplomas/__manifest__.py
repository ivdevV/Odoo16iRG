{
    'name': 'IRG Generación Diplomas',
    'version': '16.0.1.0.4',
    'category': 'Education',
    'summary': 'Generación de diplomas físicos y digitales para alumnos',
    'description': """
        Este módulo permite generar diplomas desde la ficha del estudiante.
        - Soporte para diplomas físicos y digitales.
        - Gestión de nombres de cursos en Catalán.
        - Generación automática de QR y número de registro.
        - Diseño ajustado para nombres de cursos largos.
    """,
    'author': 'ISEP / iRG',
    'depends': [
        'openeducat_core',
        'web',
        'website',
    ],
    'external_dependencies': {
        'python': ['qrcode', 'reportlab'],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/op_course_views.xml',
        'wizard/diploma_wizard_views.xml',
        'views/op_student_views.xml',
        'views/diploma_verify_templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
