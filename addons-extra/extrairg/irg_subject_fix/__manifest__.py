# -*- coding: utf-8 -*-
{
    'name': 'IRG Subject Fix',
    'version': '16.0.1.0.0',
    'category': 'Education',
    'summary': 'Corrige filtrado de asignaturas en panel del alumno y auto-inscripción',
    'description': """
        Correcciones aplicadas:

        1. Panel del alumno (template):
           - Filtra asignaturas según el lote (batch) del estudiante en vez de mostrar todas las del curso.
           - Determina canales activos consultando slide.channel.partner con active=True,
             en vez de usar el Many2many que no respeta el campo active del modelo intermedio.
           - Añade verificación de precedencia (can_be_taken) para que asignaturas con
             prerrequisitos no completados aparezcan en gris e inaccesibles.

        2. Lógica backend (auto_enroll_student / cron):
           - auto_enroll_student() ahora verifica precedencia antes de inscribir.
           - cron_auto_enroll_student() filtra por modalidad (omite 'manual'),
             verifica precedencia, y filtra por batch_id al buscar duplicados.
    """,
    'author': 'iRG',
    'website': '',
    'depends': [
        'isep_website_custom_design',
        'isep_elearning_custom',
        'isep_subject_precedence',
        'website_slides',
    ],
    'data': [
        'views/user_profile_content_details.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
