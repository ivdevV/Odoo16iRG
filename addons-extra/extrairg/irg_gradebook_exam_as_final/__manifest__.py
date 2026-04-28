# -*- coding: utf-8 -*-
{
    'name': 'IRG Gradebook — Nota del Examen como Nota Final de Asignatura',
    'version': '16.0.1.0.0',
    'summary': 'La nota final de una asignatura es la nota del examen registrado.',
    'description': """
        Sobrescribe el cálculo de final_subject_note en app.gradebook.subject
        para que la nota final de la asignatura sea únicamente la nota del examen
        (o el promedio aritmético de exámenes si hay varios, como fallback).
        Las categorías asignación, interacción y foro no influyen en la nota final.
    """,
    'author': 'IRG',
    'category': 'Education',
    'depends': ['isep_gradebook'],
    'data': [
        'data/gradebook_template_solo_examen.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
