# -*- coding: utf-8 -*-
{
    'name': 'IRG Website Theme',
    'version': '16.0.1.0.0',
    'summary': 'Tema visual centralizado para el website IRG/ISEP — variables Bootstrap, tipografía y overrides de layout',
    'description': """
        Módulo de tema global para el sitio web de Odoo 16 self-hosted (IRG).

        Centraliza la identidad visual de la instancia:
        - Paleta de colores corporativa mediante variables Bootstrap (prepend)
        - Tipografía corporativa (Inter via Google Fonts en <head>)
        - Overrides de navbar, footer y layout raíz vía xpath
        - Componentes: cards, botones, badges, inputs, tablas, breadcrumbs
        - Estilos del portal del alumno y campus

        Dependencias visuales:
        - Se carga ANTES que Bootstrap (prepend), garantizando propagación de
          $primary/$secondary a todos los módulos que ya usan variables Bootstrap:
          irg_elearning_styles_rework, irg_timetable_portal_modern_ui, etc.

        Ver: doc/micro-specs/2026-04-23-irg_website_theme.md
    """,
    'author': 'iRG',
    'website': 'https://institutoraimongaja.com',
    'category': 'Website/Theme',
    'license': 'LGPL-3',
    'depends': [
        'website',
        'isep_website_custom',
        'web',
    ],
    'data': [
        'views/layout_overrides.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # prepend = se compila ANTES que Bootstrap y el resto de estilos.
            # Esto garantiza que $primary, $secondary y demás variables estén
            # disponibles cuando cualquier otro módulo SCSS las consume.
            ('prepend', 'irg_website_theme/static/src/scss/irg_theme.scss'),
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
