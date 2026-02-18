{
    'name': 'iRG Batch Slide Restrictions',
    'version': '16.0.1.0.0',
    'category': 'Website/eLearning',
    'summary': 'Restringe acceso a temas por lotes permitidos',
    'description': """
        Permite definir lotes permitidos por tema (slide.slide)
        y bloquea el acceso web cuando el alumno no pertenece
        a uno de los lotes configurados.
    """,
    'author': 'iRG',
    'depends': [
        'website_slides',
        'isep_elearning_custom',
        'irg_elearning_restrictions',
        'irg_elearning_scheduled',
    ],
    'data': [
        'views/slide_slide_view.xml',
        'views/templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
