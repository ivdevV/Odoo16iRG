{
    'name': 'iRG Survey TXT Import Feedback',
    'summary': 'Importa preguntas tipo test (4 opciones) desde TXT con feedback generico',
    'version': '16.0.1.0.0',
    'category': 'Website/Survey',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'survey',
        'website_slides_survey',
        'isep_survey',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/survey_views.xml',
        'views/survey_txt_import_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
}
