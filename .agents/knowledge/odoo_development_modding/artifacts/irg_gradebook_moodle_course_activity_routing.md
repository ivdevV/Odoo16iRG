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

El flujo histórico de migración usaba tres fuentes separadas: una autorizaba
parejas HomeClass, otra inventariaba IDs Online y una tercera aportaba
curso/asignatura/Activity IDs. Ese contexto explica la separación original,
pero no es el contrato vigente del administrador: ahora se importan exactamente
dos CSV consolidados, uno de parejas de curso y otro de
curso/asignatura/Activity IDs.

Centralizar ambos adaptadores —wizard y `odoo shell`— en el mismo servicio:
deben compartir lectura, validación, plan y aplicación, no reinterpretar los
CSV por separado. Aceptar los alias legado y canónico de cabeceras de curso,
pero rechazar una fila si ambos aportan valores contradictorios. El parser debe
ser estricto: un CSV estructuralmente malformado bloquea el análisis completo;
los problemas semánticos de filas se contabilizan como omisiones o advertencias.

Separar explícitamente análisis y aplicación. El análisis construye un plan y
un `preview` de solo lectura con las mismas claves de búsqueda que el *upsert*,
incluidos registros inactivos; por tanto puede informar de creaciones y
actualizaciones sin modificar datos. En la confirmación se vuelven a analizar
los bytes persistidos y se revalidan las referencias Odoo antes de escribir,
para no aplicar un plan o resumen obsoleto o manipulado.

Antes de la primera escritura, hacer un *preflight* estructural de todo el
plan: tipos, IDs, claves únicas, padres coherentes y actividades no vacías. Solo
después ejecutar *upsert* por claves estables y por Activity ID: nunca limpiar
el One2many, desactivar o borrar los históricos. Los mapas antiguos sin padre
se preservan, pero no se enrutan.

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
métodos / 22 pruebas y subpruebas Odoo sin fallos. En la etapa histórica
anterior se validó además la importación reversible de tres fuentes CSV, el
rechazo sintético de marcadores malformados y checks estáticos. El flujo actual
del administrador se rige por los dos CSV consolidados descritos arriba. El
upgrade final no emitió errores ni warnings de docutils atribuibles al README y
`verification.json` quedó en estado `passed`. El smoke real confirmó parseo,
autorizaciones y rollback, pero `test_irg_db` no contenía los registros Odoo
fuente y por ello no creó mapas reales.
