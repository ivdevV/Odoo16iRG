# Micro-spec: canal eLearning TFM Online

## Problema

Una matrícula Online como `MOPCONL2606` puede tener convocatoria TFM pero no
mostrar el acceso eLearning. Además, el espejo de secciones Online no permite
configurar las convocatorias de sus categorías.

## Diseño aprobado

El addon `irg_tfm_convocatorias` heredará la vista exacta de
`irg_course_convocatorias_v2` para ofrecer una superficie editable de categorías
Online con `Convocatorias TFM`. La resolución de la familia aceptará el puntero
directo HomeClass → Online y, si falta, recuperará un único clon que apunte al
HomeClass. Cualquier ambigüedad fallará cerrada. La matrícula exacta seguirá
determinando HomeClass u Online y el portal enlazará únicamente al canal efectivo.

## Fuera de alcance

- No modifica el contenido ni las membresías ajenas al flujo TFM.
- No cambia los cortes de activación ni las fechas de convocatoria.
- No implementa todavía el Esquema mediante encuesta; ese cambio mantiene su
  proceso de diseño independiente.
- No despliega, publica ni actualiza beta.

## Aceptación

Los criterios y gates están definidos en
`missions/irg-tfm-online-elearning-fix/plan.md`.
