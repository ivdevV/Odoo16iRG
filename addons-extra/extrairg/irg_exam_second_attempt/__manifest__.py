{
    'name': 'iRG Exam Second Attempt',
    'summary': (
        'Habilita el segundo intento y corrige la nota mostrada en slides '
        'tipo examen'
    ),
    'version': '16.0.1.0.0',
    'category': 'Website/eLearning',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'isep_survey',
        'isep_gradebook',
    ],
    'data': [
        'data/fix_exam_attempt_limits.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
