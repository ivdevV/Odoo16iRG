# -*- coding: utf-8 -*-
{
    'name': 'IRG Timetable — Lote por Batch Fix',
    'version': '16.0.1.0.0',
    'summary': (
        'Corrige la resolución del lote en /student/timetable/?batch_id=X: '
        'cuando la URL incluye batch_id, usa ese batch directamente en vez del '
        'primer enrollment running (que puede ser el incorrecto para alumnos '
        'con múltiples programas).'
    ),
    'category': 'Education',
    'author': 'IRG',
    'license': 'LGPL-3',
    'depends': [
        'irg_timetable_irg_api',
    ],
    'data': [],
    'assets': {
        'web.assets_frontend': [
            'irg_timetable_lote_batch_fix/static/src/js/timetable_lote_batch_fix.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
