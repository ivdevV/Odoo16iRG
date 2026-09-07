# Patron: variantes del convenio específico en el mismo módulo

Fecha: 2026-09-07

Modulo: `irg_practice_agreement_specific`

## Decision reutilizable

Si una variante nueva de convenio específico comparte wizard, doble
firma, controlador e informe PDF con las que ya existen, **ampliar el
módulo `irg_practice_agreement_specific`**. No crear un addon hermano
solo para el clausulado.

Esto es una **excepción autorizada y acotada** a la regla de no editar
módulos existentes. No autoriza tocar `irg_practice_agreement_sign` ni
`irg_practice_agreement_types`. No sienta precedente para otras
features que sí caben en un módulo nuevo por herencia.

Al añadir el valor en `selection_add`, Python (`_is_especifico()` /
`ESPECIFICO_TYPES`) y QWeb (report, portal, `attrs`) deben usar el
mismo predicado el mismo día. Ver
`irg_selection_qweb_predicate_alignment.md`.

## Motivos

El específico nacional es otra plantilla del mismo flujo, no otro
producto. Un módulo nuevo solo para esa variante no aporta arquitectura
y duplica `print_report_name`, tokens y firmar.
