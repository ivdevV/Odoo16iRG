{
    'name': 'iRG eLearning Scheduled Content',
    'version': '16.0.1.0.0',
    'category': 'Website/eLearning',
    'summary': 'Restricción de acceso por fecha programada',
    'description': """
        Este módulo permite programar la fecha de disponibilidad del contenido.
        El alumno no podrá acceder al contenido hasta que llegue la fecha indicada.
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
