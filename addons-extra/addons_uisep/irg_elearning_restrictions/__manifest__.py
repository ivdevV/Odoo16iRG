{
    'name': 'iRG eLearning Restrictions',
    'version': '16.0.1.0.5',
    'category': 'Website/eLearning',
    'summary': 'Restricciones de acceso a diapositivas',
    'description': """
        Este módulo permite establecer diapositivas como prerrequisito para acceder a otras.
        Creado para probar visibilidad de campos.
    """,
    'author': 'iRG',
    'depends': ['website_slides'],
    'data': [
        'views/slide_slide_view.xml',
        'views/templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
