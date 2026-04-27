# -*- coding: utf-8 -*-
{
    'name': 'IRG HTML Embed Slide',
    'version': '16.0.1.0.0',
    'summary': 'Permite embeber HTML personalizado en diapositivas de tipo artículo del eLearning.',
    'description': """
        Añade la pestaña "Contenido Interactivo" al formulario de slide.slide.
        Si se activa el campo "Usar HTML embebido", el HTML almacenado en
        "Código HTML embebido" se renderiza dentro de un iframe seguro en el
        reproductor de cursos (tanto vista normal como pantalla completa).
    """,
    'author': 'IRG',
    'category': 'eLearning',
    'depends': ['website_slides', 'isep_content_interactive'],
    'data': [
        'views/slide_slide_views.xml',
        'views/website_slides_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'irg_html_embed_slide/static/src/js/embed_widget.js',
            'irg_html_embed_slide/static/src/js/embed_fullscreen.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
