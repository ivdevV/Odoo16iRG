{
    'name': 'IRG - Modalidades de Curso',
    'version': '16.0.1.0.0',
    'summary': 'Añade modalidades (Presencial, HomeClass, Online) al modelo op.course',
    'description': """
        Permite indicar en cada curso académico (op.course) las modalidades
        de impartición disponibles: Presencial, HomeClass y/u Online.
        Las modalidades se gestionan mediante un catálogo extensible
        (irg.course.modality) vinculado por Many2many.

        La modalidad Online se activa automáticamente en los lotes cuyo código
        contiene 'ONL' pero no 'MONL' (lógica delegada al módulo
        irg_online_subject_opening y futuro módulo de desbloqueo eLearning).
    """,
    'author': 'IRG',
    'category': 'Education',
    'license': 'LGPL-3',
    'depends': [
        'openeducat_core',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/irg_course_modality_data.xml',
        'views/irg_course_modality_views.xml',
        'views/op_course_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
