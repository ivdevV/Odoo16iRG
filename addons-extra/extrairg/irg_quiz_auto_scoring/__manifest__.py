# -*- coding: utf-8 -*-
###############################################################################
#
#    iRG Inc
#    Copyright (C) 2009-TODAY iRG Inc
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
###############################################################################

{
    'name': 'iRG Quiz Auto-Scoring',
    'version': '16.0.1.0',
    'category': 'Education',
    'sequence': 1,
    'summary': 'Auto-calcular puntajes de cuestionarios y sincronizar con calificaciones',
    'complexity': 'medium',
    'author': 'iRG Inc',
    'website': 'https://www.irg.com.ar',
    'license': 'LGPL-3',
    'depends': [
        'openeducat_quiz',
    ],
    'external_dependencies': {
        'python': [],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/quiz_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
