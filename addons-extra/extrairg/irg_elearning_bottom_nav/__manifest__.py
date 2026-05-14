# -*- coding: utf-8 -*-
{
    'name': 'IRG eLearning - Navegación inferior de unidades',
    'version': '16.0.1.0.0',
    'summary': 'Duplica los botones Anterior/Siguiente al pie del contenido de cada unidad',
    'description': """
        Mejora de UX: añade una segunda barra de navegación (Anterior / Siguiente)
        al final del contenido de cada slide/unidad del campus virtual, de modo que
        el alumno no tenga que desplazarse hacia arriba para continuar con la
        siguiente lección una vez terminada la actual.
    """,
    'category': 'Website/eLearning',
    'author': 'iRG',
    'license': 'LGPL-3',
    'depends': [
        'website_slides',
    ],
    'data': [
        'views/bottom_nav_template.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
