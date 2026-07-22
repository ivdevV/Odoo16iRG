# Routing estricto de curso y actividades Moodle para libretas

## Problema reutilizable

Un mapa de asignatura con solo `moodle_course_id` es insuficiente cuando un
curso Odoo tiene ediciones HomeClass y Online, o varias ediciones Online. Elegir
por Activity ID o por el primer mapa disponible puede consultar un curso Moodle
equivocado y aplicar actividades de otra edición.

## Patrón aplicado

Usar una relación explícita de dos niveles:

```text
curso Odoo -> mapa de curso Moodle -> mapa de asignatura / Activity IDs
```

El mapa padre conserva curso Odoo, Moodle Course ID, nombre, modalidad y
edición; cada hijo exige por constraint el mismo Moodle Course ID y pertenencia
de su asignatura al curso del padre. La comprobación debe ser recíproca al
editar el padre, para no corromper hijos existentes. Antes de consultar Moodle,
el wizard resuelve exactamente un padre y filtra los hijos por contexto.

Para códigos de lote, exigir una sola señal autoritativa: `HC` selecciona un
único HomeClass activo; `ONL` prioriza la edición igual al año del lote y solo
acepta un fallback Online genérico inequívoco. Ausencia, doble modalidad o
múltiples candidatos son errores funcionales previos a la llamada externa.

La clasificación de nombres también debe ser estricta: solo `(ONLINE)` y
`(ONLINE AAAA)`, con cuatro dígitos, representan mapas Online seleccionables.
Si existe un token `(ONLINE` malformado, repetido o sin cierre exacto, devolver
modalidad falsa y descartarlo en el importador antes de tocar el ORM. No debe
convertirse en HomeClass ni en fallback Online genérico.

## Importación segura de datos históricos

Separar las fuentes autorizadoras de las relaciones completas: un CSV autoriza
parejas HomeClass, otro inventaría IDs Online y un tercero aporta
curso/asignatura/Activity IDs. Validar encabezados, codificación, IDs positivos
y pertenencia Odoo; resumir descartes por causa. Ejecutar *upsert* por claves
estables y por Activity ID: nunca limpiar el One2many, desactivar o borrar los
históricos. Los mapas antiguos sin padre se preservan, pero no se enrutan.

## Regresiones mínimas

- Selección HC, Online por año y fallback genérico.
- Rechazo de lote ambiguo, sin modalidad y candidatos múltiples.
- Rechazo pre-servicio y pre-ORM de marcadores Online malformados.
- Aislamiento de asignaturas entre cursos Moodle.
- Rechazo de incoherencia padre/hijo por ORM y defensa ante históricos
  corrompidos antes de contactar el servicio Moodle.
- Reejecución del importador sin borrar Activity IDs o metadatos existentes.

## Resultado validado

La última suite funcional del addon `irg_gradebook_moodle_routing` ejecutó 20
métodos / 22 pruebas y subpruebas Odoo sin fallos, más importación reversible
de las tres fuentes CSV, rechazo sintético de marcadores malformados y checks
estáticos. El upgrade final no emitió errores ni warnings de docutils
atribuibles al README y `verification.json` quedó en estado `passed`. El smoke
real confirmó parseo, autorizaciones y rollback, pero `test_irg_db` no contenía
los registros Odoo fuente y por ello no creó mapas reales.
