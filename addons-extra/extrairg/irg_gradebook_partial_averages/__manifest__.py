# -*- coding: utf-8 -*-
{
    'name': 'IRG Gradebook — Promedios Parciales',
    'version': '16.0.1.0.0',
    'summary': 'No pone a 0 los promedios de asignatura al cambiar de plantilla.',
    'description': """
        Sobrescribe compute_point_average en app.gradebook.subject para que
        los promedios de assignment y exam se calculen con los resultados
        realmente registrados, aunque su cantidad no coincida con la qty
        configurada en la plantilla de calificaciones (gradebook_id).

        Antes, al aplicar o cambiar una plantilla, si el nº de resultados no
        coincidía exactamente con la qty de la línea de plantilla, el
        promedio se forzaba a 0 y ese 0 quedaba persistido (campos store).
        Con este módulo, si hay al menos 1 resultado registrado se calcula
        el promedio aritmético parcial; si no hay resultados, sigue siendo 0.

        Las categorías interaction y foro mantienen su lógica original
        (exigen exactamente 1 resultado).
    """,
    'author': 'IRG',
    'category': 'Education',
    'depends': ['isep_gradebook'],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
