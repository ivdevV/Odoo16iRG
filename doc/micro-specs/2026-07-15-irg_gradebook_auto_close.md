# Micro-spec: `irg_gradebook_auto_close`

**Fecha:** 2026-07-15
**Módulo:** `irg_gradebook_auto_close`
**Ruta:** `addons-extra/extrairg/irg_gradebook_auto_close/`

## Justificación

La libreta del alumno (`app.gradebook.student`) ya dispone de una acción manual de
cierre, `state_to_done()`, y de acciones de reapertura. El flujo de introducción de
notas, tanto manual como procedente de Moodle, debe cerrar automáticamente una libreta
cuando todas sus asignaturas están calificadas, sin duplicar ni debilitar las
validaciones académicas que ya aplica el cierre manual.

La extensión se implementa en un módulo nuevo para conservar intacto
`isep_gradebook` y facilitar su instalación, prueba y reversión independientes.

## Objetivo

Cerrar una libreta en estado `in_progress` cuando tenga al menos una línea y todas
las líneas cumplan:

- `final_subject_note > 0`;
- `point_average_exam > 0` cuando `show_exam` sea verdadero;
- `point_average_assignment > 0` cuando `show_assignment` sea verdadero.

Una línea que no muestre exámenes o asignaciones no exige el promedio oculto
correspondiente. En particular, Prácticas o TFM sin AVG Asignaciones pueden cerrar.

## Alcance

- Crear `irg_gradebook_auto_close`, dependiente de `isep_gradebook`.
- Heredar `app.gradebook.student` para evaluar la condición y solicitar el cierre.
- Heredar `app.gradebook.result` para reevaluar las libretas afectadas después de
  `create`, `write` y `unlink`.
- Conservar las libretas anterior y nueva cuando un resultado cambia de línea.
- Soportar operaciones multi-registro y creación por lotes.
- Mantener operativas `state_to_in_progress()` y `action_draft()`.
- Cubrir con tests la condición de cierre, los cinco escenarios aprobados y las
  regresiones de hooks, lotes y multi-registro detectadas durante la implementación.

## Fuera de alcance

- Modificar `isep_gradebook`, sus vistas o sus botones.
- Escribir `state = "done"` directamente o cambiar las validaciones originales.
- Crear modelos, campos, ACL, cron o interfaz nueva.
- Reevaluar por cambios ajenos a `app.gradebook.result`.
- Cerrar de nuevo una libreta por el mero hecho de reabrirla.
- Migrar o corregir datos históricos.

## Diseño

### Condición de cierre

`app.gradebook.student._irg_is_ready_to_close()` devuelve `False` para recordsets
vacíos, exige singleton, estado `in_progress` y al menos una línea. Después evalúa
todas las líneas con las reglas positivas anteriores. La lectura de los campos
computed stored permite a Odoo resolver sus dependencias antes de decidir.

`_irg_try_auto_close()` procesa cada libreta elegible y llama a
`state_to_done()`.

### Decisión: `state_to_done()` y captura de `UserError`

Se reutiliza `state_to_done()` en lugar de asignar el estado directamente porque el
método base valida la cantidad de evaluaciones requerida por el template. Esa
validación sigue siendo la autoridad académica del cierre.

Si la libreta parece completa por promedios pero faltan evaluaciones del template,
`state_to_done()` puede lanzar `UserError`. El autocierre captura únicamente esa
excepción, registra un warning y deja la libreta en `in_progress`; guardar una nota
no debe fallar por un intento automático de cierre. Otras excepciones no se ocultan.

### Triggers de resultados

- `create`: ejecuta la lógica base, reúne las libretas de los registros creados y
  evalúa una vez al final del lote.
- `write`: conserva las libretas previas, ejecuta la lógica heredada registro a
  registro por compatibilidad con el override singleton del módulo base, reúne las
  libretas actuales y evalúa la unión de ambas.
- `unlink`: conserva las libretas antes del borrado, ejecuta `super()` y evalúa
  después solo las que aún existen.

El `create` base puede escribir internamente `scoring_total` cuando está activo el
redondeo. Para impedir un cierre sobre un lote todavía parcial, esas escrituras
anidadas llevan el contexto namespaced
`irg_gradebook_auto_close_skip_nested_write_auto_close`. El trigger se difiere hasta
el final del `create`; los registros se rebrowsean con el contexto normal para que la
marca interna no se filtre al recordset devuelto.

### Reapertura

Las acciones base de reapertura no se sobreescriben. Una libreta reabierta permanece
en `in_progress` hasta que un `create`, `write` o `unlink` posterior de un resultado
vuelva a ejecutar la evaluación.

## Criterios de aceptación

1. Escribir la última nota positiva de una libreta completa la deja en `done`.
2. Una línea con calificación final cero mantiene la libreta en `in_progress`.
3. Una línea con `show_assignment=False` puede cerrar sin promedio de asignaciones.
4. Reabrir no provoca autocierre; una escritura posterior de nota sí reevalúa.
5. Un `UserError` de `state_to_done()` no aborta el guardado y mantiene la libreta
   abierta.
6. La condición directa cubre línea completa, nota cero y asignaciones ocultas.
7. `create`, `write` multi-registro, `unlink` y cambio de línea reevalúan todas las
   libretas afectadas después de la operación base.
8. Un `create` por lotes con redondeo no cierra usando datos parciales ni devuelve
   un recordset contaminado con el contexto interno.
9. No se modifica ningún archivo de `isep_gradebook`.

## Compatibilidad, instalación y rollback

El módulo es compatible con Odoo 16, versión `16.0.1.0.0`, y depende únicamente de
`isep_gradebook`. No crea tablas, campos ni reglas de seguridad. Su instalación no
requiere migración; las libretas existentes se reevaluarán únicamente cuando cambie
un resultado.

El rollback funcional consiste en desinstalar `irg_gradebook_auto_close`. La
desinstalación detiene futuros autocierres, pero no reabre automáticamente libretas
que ya estén en `done`.

## Validación

La validación independiente se ejecutó mediante `docker-compose.local.yml` contra
`test_irg_db`: upgrade fresco, 13 tests post-install, 0 fallos y 0 errores. También
pasaron compilación de 7/7 archivos Python, parseo de manifest e imports, auditoría
de patrones prohibidos y comprobación de alcance sin cambios en `isep_gradebook`.
La evidencia trazable se conserva en `missions/gradebook-auto-close/`.
