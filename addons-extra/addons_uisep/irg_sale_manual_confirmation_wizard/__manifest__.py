# -*- coding: utf-8 -*-
{
    'name': 'IRG Sale Manual Confirmation Wizard',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'summary': 'Wizard pre-confirmacion para presupuestos manuales + routing email bienvenida por modalidad',
    'description': """
        Modulo para gestion segura de la confirmacion MANUAL de presupuestos.

        Funcionalidades:

        1) Wizard pre-confirmacion (boton "Confirmar (validar fechas)" en sale.order):
           - Permite revisar/ajustar admission_date antes de confirmar
           - Muestra modalidad detectada del producto
           - Muestra preview del codigo de lote que se generara
           - Avisa si admission_date no es del mes actual o si HC/PRS y dia > 7

        2) Routing email bienvenida post-confirm:
           - Si lote es ONL (codigo contiene 'ONL') -> plantilla online
           - Si HC / PRS / GE -> plantilla por defecto existente
           - Plantillas configurables en singleton auto.admission.required

        3) Config (auto.admission.required):
           - welcome_template_online_id (Many2one mail.template)
           - welcome_template_default_id (Many2one mail.template)
           - manual_wizard_enabled (Boolean) - on/off del routing personalizado
    """,
    'author': 'Instituto Raimon Gaja',
    'depends': [
        'sale',
        'isep_openeducat_sale',
        'irg_openeducat_sale_lote_custom',
        'irg_elearning_correo_bienvenida_selector',
        'isep_sale_order_admissions',
        'isep_admission_from_student_field',
        'irg_admission_class_start_date',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/manual_confirmation_wizard_views.xml',
        'views/sale_order_views.xml',
        'views/auto_admission_required_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
