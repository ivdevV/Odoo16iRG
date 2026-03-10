{
    'name': 'iRG Survey Regrade Attempts',
    'summary': 'Permite recalificar intentos en survey.user_input y sincronizar libreta',
    'version': '16.0.1.0.0',
    'category': 'Website/Survey',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'survey',
        'isep_survey',
        'isep_gradebook',
    ],
    'data': [
        'views/survey_user_input_views.xml',
    ],
    'installable': True,
    'application': False,
}
