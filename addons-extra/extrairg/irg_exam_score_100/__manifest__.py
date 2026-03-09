{
    'name': 'iRG Exam Score 100',
    'summary': 'Normaliza examenes/certificaciones survey a escala 0-100',
    'version': '16.0.1.0.0',
    'category': 'Website/Survey',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'survey',
        'website_slides_survey',
        'isep_survey',
        'isep_gradebook',
    ],
    'data': [
        'views/survey_survey_views.xml',
    ],
    'installable': True,
    'application': False,
}
