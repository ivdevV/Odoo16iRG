{
    'name': 'IRG Diploma Graduación Estudiante',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Generación de diploma de graduación en PDF para estudiantes desde op.student',
    'description': """
        Este módulo permite generar un diploma de graduación en PDF para un estudiante
        desde su vista en OpenEduCat (op.student) a partir de una plantilla .docx.
    """,
    'author': 'ISEP / iRG',
    'depends': [
        'openeducat_core',
        'web',
    ],
    'external_dependencies': {
        'python': ['reportlab', 'qrcode'],
    },
    'data': [
        'security/ir.model.access.csv',
        'wizard/diploma_graduacion_wizard_views.xml',
        'views/op_student_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
