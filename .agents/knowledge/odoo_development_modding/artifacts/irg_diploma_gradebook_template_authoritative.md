# Plantilla autoritativa y recálculo explícito en libretas Odoo

## Contexto

En `app.gradebook.student`, `total_final` y `avg_score` pueden calcularse desde
las notas finales de las asignaturas obligatorias aunque `gradebook_id` esté
vacío. Por tanto, ver un promedio antes de elegir una plantilla no significa
que exista otra plantilla activa: es el fallback heredado del modelo.

En beta, seis notas `10` y un presencial `8,44` producían la media simple
`9,78`. El selector se guardaba y la plantilla mostraba el modo correcto, pero
las barreras secundarias de clasificación y la cadena MRO podían conservar ese
fallback en vez del resultado funcional `9,22`.

## Aprendizaje reutilizable

Cuando una opción de negocio explícita debe gobernar un cálculo, no conviene
subordinarla a datos clasificatorios redundantes e inconsistentes. Si
`gradebook_id.final_calculation_mode == 'diploma_50_50'` es una selección
deliberada y exclusiva para Diplomados, ese modo puede ser la autoridad
funcional, manteniendo validaciones estructurales sobre las líneas que entran
en la fórmula.

También hay que distinguir dos problemas:

1. **Invalidación:** el campo selector debe aparecer en `@api.depends`.
2. **Precedencia MRO:** después de `super()`, el addon cargado al final debe
   reaplicar el valor especial para que otro compute heredado no lo sustituya.

En instalaciones con listas de dependencias históricamente reemplazadas por
otros addons, un `write()` acotado a `gradebook_id` puede invalidar y recalcular
explícitamente los campos almacenados. Debe protegerse con una clave de
contexto contra reentrada y no convertirse en una recomputación masiva.

## Patrón aplicado

- Crear un addon puente nuevo cargado después de toda la cadena en conflicto.
- Mantener `super()` en computes para preservar casos estándar.
- Tratar el modo explícito como autoridad sin consultar categoría, tipo o
  nombre del curso.
- Exigir exactamente un presencial obligatorio y al menos un ordinario
  obligatorio no exento.
- Reutilizar `irg_is_grade_exempt()` como fuente única de exención NLEX/EX.
- Reaplicar el cálculo tanto en `total_final` como en `avg_score`.
- Invalidar y recalcular ambos campos al escribir `gradebook_id`.
- Ante una topología ambigua, registrar una advertencia y conservar el fallback
  heredado.

## Regresión mínima

- Forzar el detector heredado a falso y comprobar que no se llama: seis notas
  `10` más presencial `8,44` deben producir `9,22`.
- Comenzar con template estándar en `9,78`, escribir el especial y comprobar
  inmediatamente `9,22` en ambos campos finales.
- Verificar que el template estándar sigue en `9,78`.
- Añadir un NLEX puntuado y confirmar que el especial sigue en `9,22`.
- Crear dos presenciales y confirmar el fallback seguro.

## Gotchas operativos

- Cambiar entre templates estándar puede no alterar el promedio global si la
  implementación base calcula la nota final de asignatura solo con exámenes.
  La configuración de evaluaciones por asignatura y la ponderación global del
  Diplomado son capas distintas.
- Instalar un addon no garantiza la escritura de `gradebook_id` en registros
  históricos que ya tenían el template especial. Para comprobar una libreta
  existente, cambiar a un template estándar, guardar y volver al especial.
- No usar este patrón para saltarse validaciones funcionales genéricas: aquí es
  válido porque el modo `diploma_50_50` es una opción creada específicamente
  para Diplomados y conserva validaciones estrictas sobre las asignaturas.

## Resultado validado

`irg_diploma_gradebook_template_authoritative` pasó cinco pruebas Odoo en una
base aislada mediante `docker-compose.local.yml`: 5 superadas, 0 fallos, 0
errores. La instalación terminó con código 0 y el cambio inmediato comprobado
fue `9,78 -> 9,22`.
