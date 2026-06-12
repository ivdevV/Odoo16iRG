# -*- coding: utf-8 -*-
{
    'name': 'IRG OpenEducat Sale Online Quarterly Batches',
    'version': '16.0.1.1.0',
    'category': 'Sales',
    'summary': 'Convocatorias trimestrales para lotes Online (A/B/C/D)',
    'description': """
        Sobrescribe get_lot_id() solo para modalidad Online (ONL):

        - mes 1-3   -> sufijo 'A'  -> lote ...ONL{YY}A
        - mes 4-6   -> sufijo 'B'  -> lote ...ONL{YY}B
        - mes 7-9   -> sufijo 'C'  -> lote ...ONL{YY}C
        - mes 10-12 -> sufijo 'D'  -> lote ...ONL{YY}D

        Lote ONL se crea con:
        - start_date = primer dia del trimestre
        - end_date   = ultimo dia del trimestre

        HC / PRS / GE no se ven afectados (siguen logica mensual de irg_openeducat_sale_lote_custom).

        Flag de configuracion: quarterly_online_enabled (auto.admission.required).
    """,
    'author': 'Instituto Raimon Gaja',
    'depends': [
        'irg_openeducat_sale_lote_custom',
        'isep_openeducat_sale',
    ],
    'data': [
        'views/auto_admission_required_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
