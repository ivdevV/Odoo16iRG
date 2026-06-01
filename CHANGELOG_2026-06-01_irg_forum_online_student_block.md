# Changelog - irg_forum_online_student_block

Fecha: 2026-06-01

## Cambios

- Se crea el modulo `irg_forum_online_student_block` para bloquear alumnos online en foros de campus/curso.
- Se bloquea la visibilidad de foros y posts cuando el foro intersecta con lotes/cursos online del alumno.
- Se bloquea la publicacion de temas y respuestas en esos foros mediante `UserError` traducible.
- Se filtran notificaciones por email y a seguidores para excluir alumnos online bloqueados.
- Se preserva la logica de HomeClass y master HC (`HC`, por ejemplo `MIAHC2606`).
- Se excluyen explicitamente codigos `MONL`, incluidos `MIAMONL2601` y `MBIAMONL2601`.
- Se anaden tests para bloqueo online, preservacion HC/MONL, alumno mixto online + master HC y bypass administrativo.
- Se anade micro-spec y documentacion tecnica del modulo.

## Validacion

- Sintaxis Python validada con `python3 -m compileall addons-extra/extrairg/irg_forum_online_student_block`.
- XML validado con parser de `xml.etree.ElementTree`.
- Diagnosticos de editor sin errores para el modulo nuevo.
- No se ejecuto Odoo/Docker local por configuracion de este workspace; la prueba Odoo debe realizarse en servidor real.
