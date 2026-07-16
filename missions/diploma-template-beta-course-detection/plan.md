# Plan: deteccion robusta de Diplomados en libreta beta

## Objetivo

Corregir el caso de beta donde la plantilla
`Diplomado - Solo examen - Ponderacion 50/50` conserva la media simple 9,78
aunque el curso se identifica claramente como Diplomado y el resultado esperado
es 9,22.

## Evidencia y diagnostico

- La libreta AD003983 contiene seis modulos ordinarios con nota 10 y un modulo
  presencial con nota 8,44.
- Los cambios de `gradebook_id` quedan registrados en el chatter, por lo que no
  se trata de un fallo de guardado.
- El calculo especial devuelve al comportamiento estandar cuando
  `_is_diplomado_course()` es falso.
- La deteccion actual considera autoritativa cualquier categoria de producto
  configurada y no consulta el nombre del curso cuando esa categoria no es de
  Diplomado. En bases espejo con clasificacion heredada/inconsistente, un curso
  llamado `Diplomado ...` queda descartado y produce exactamente 9,78.

## Alcance

1. Crear un addon puente nuevo bajo `addons-extra/extrairg/`, sin modificar
   addons existentes.
2. Heredar `app.gradebook.student` y ampliar exclusivamente la deteccion de
   Diplomado: conservar los criterios estructurados heredados y aceptar tambien
   un nombre de curso con etiqueta inequivoca de Diplomado.
3. Mantener como segunda barrera la seleccion explicita del modo
   `diploma_50_50`, de modo que los templates normales no cambien.
4. Agregar pruebas de regresion para la clasificacion inconsistente de beta, el
   resultado 9,22, el cambio de template y un curso no Diplomado.

## Fuera de alcance

- Migraciones o escrituras masivas sobre datos historicos.
- Cambios a las calificaciones por asignatura o a `survey_type`.
- Modificar los addons de ponderacion/NLEX ya existentes.
- Commit o push sin una autorizacion explicita nueva del usuario.

## Complejidad y routing

- **Tier:** `standard`.
- **Justificacion:** logica acotada en un addon puente nuevo, con una extension
  de modelo y pruebas; no toca seguridad, migraciones, concurrencia ni secretos.
- **Implementacion:** subagente codificador de capacidad intermedia.
- **Validacion:** subagente testeador independiente, usando
  `docker-compose.local.yml` y emitiendo `verification.json`.
- **Documentacion:** subagente documentador despues de validacion `passed`.
- **Security Advisor:** no aplica.

## Validacion prevista

- Curso `Diplomado ...` con categoria de producto no Diplomado + template 50/50:
  seis notas 10 y presencial 8,44 producen 9,22.
- Cambiar desde un template estandar (9,78) al especial recalcula a 9,22.
- Un curso sin identificadores de Diplomado conserva el comportamiento normal.
- Instalacion y tests Odoo en el compose local.
- Sintaxis Python, manifest y `git diff --check`.

## Conocimiento aplicado

- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`:
  addons en `addons-extra/extrairg/`, prefijo `irg_` y extension por `_inherit`.
- `.agents/knowledge/odoo_development_modding/artifacts/irg_diploma_gradebook_template_nlex_compat.md`:
  preservar el addon puente que resuelve el orden MRO con NLEX.
