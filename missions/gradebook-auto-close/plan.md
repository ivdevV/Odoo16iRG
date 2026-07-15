# Misión: gradebook-auto-close

## Fuente aprobada

El alcance aprobado por el usuario es `missions/gradebook-auto-close/00-plan.md`, copia
de `/Users/ivrogo/Downloads/00-plan.md`. La orden «Implementa el plan estrictamente»
constituye la aprobación de esta micro-especificación. Se mantiene la decisión indicada
en ella: el autocierre reutiliza `state_to_done()` y captura `UserError`; no se asigna
`state = "done"` directamente.

## Alcance

- Crear el módulo `addons-extra/extrairg/irg_gradebook_auto_close`.
- Extender por `_inherit` los modelos `app.gradebook.student` y
  `app.gradebook.result`; no modificar `isep_gradebook`.
- Implementar `_irg_is_ready_to_close()` y `_irg_try_auto_close()`.
- Disparar la reevaluación tras `create`, `write` y `unlink` de resultados,
  conservando también las libretas afectadas antes de un cambio de relación o borrado.
- Añadir `tests/test_auto_close.py` con los cinco escenarios funcionales exigidos y
  cobertura directa de la condición de cierre.
- Validar exclusivamente mediante `docker-compose.local.yml` contra `test_irg_db`.
- Documentar estructura, uso, pruebas, limitaciones, changelog y aprendizaje reusable.

## Fuera de alcance

- Cambiar la lógica original de `state_to_done()`.
- Alterar vistas, botones de reapertura o módulos existentes.
- Cerrar libretas desde escrituras que no sean cambios de `app.gradebook.result`.
- Hacer commit, pull, push o modificar la rama remota. Cualquier push a `Dev_iRG`
  requiere un OK explícito posterior del usuario.

## Clasificación y routing

Tier: `standard`.

Justificación objetiva: se prevé un módulo nuevo de aproximadamente 7 archivos, pero
la lógica está acotada a dos modelos y un archivo de tests, con contexto y aceptación
cerrados. No afecta autenticación, concurrencia, migraciones, secretos, despliegue ni
borrado histórico; no se activa Security Advisor. El número de archivos supera cinco
por el esqueleto obligatorio del módulo, no por complejidad cross-module.

- Plan/orquestación: agente principal, modelo de razonamiento alto.
- Implementación: subagente codificador, tier `standard`, especialista Odoo 16 y TDD.
- Validación: subagente testeador nuevo, tier `standard`.
- Anti-patrones: subagente revisor nuevo, tier `standard`.
- Calidad: subagente revisor nuevo, tier `standard`.
- Documentación: subagente documentador nuevo, modelo ligero/intermedio disponible.

Si `verification.json` queda en `failed`, se reencolará la corrección en tier
`complex` y el intento se registrará en `execution.log`.

## Fases y criterios de paso

### 1. Implementación TDD

1. Crear el esqueleto instalable con dependencia exclusiva funcional de
   `isep_gradebook` y sin ACL vacía, ya que no se crean modelos nuevos.
2. Escribir primero los tests de los cinco escenarios y de la condición indicada.
3. Ejecutar los tests antes de producción y registrar un fallo RED atribuible a la
   ausencia de la feature.
4. Implementar la mínima extensión para pasar los tests:
   - singleton-safe `_irg_is_ready_to_close()`;
   - `_irg_try_auto_close()` que captura solo `UserError` y registra warning;
   - `create`, `write` y `unlink` que reúnen libretas afectadas tras `super()`,
     preservando las referencias previas necesarias para `write`/`unlink`.
5. Ejecutar GREEN y refactorizar solo con pruebas verdes.
6. Mantener `execution.log` y producir `diff.patch`.

Paso de fase: el codificador entrega archivos cambiados, comandos, salida RED/GREEN y
riesgos observados. El orquestador comprueba el diff antes de delegar validación.

### 2. Validación independiente

Ejecutar, cuando apliquen:

- instalación/actualización del módulo y tests etiquetados en `test_irg_db` mediante
  `docker-compose.local.yml`;
- test suite objetivo completa (5/5 escenarios);
- comprobación de carga Python/XML/manifest del módulo;
- lint o verificaciones estáticas disponibles;
- comprobación automatizada de reapertura y del fallo capturado de template;
- flujo manual o integración equivalente reproducible: última nota ⇒ `done`.

Guardar salidas en `artifacts/` y emitir `verification.json` conforme al contrato.
Solo `status: passed` permite continuar.

### 3. Revisiones independientes

- Anti-patrones: verificar que no se modificó `isep_gradebook`, no hay cierre directo,
  `except Exception`, ACL innecesaria, APIs inventadas ni autocierre desde reapertura.
- Calidad: revisar compatibilidad Odoo 16, semántica multi-record, recomputación,
  colección de relaciones antigua/nueva en `write`, logging y correspondencia exacta
  con cada criterio de aceptación.

Los hallazgos Critical/Important vuelven a implementación y obligan a repetir la
validación completa.

### 4. Documentación

- Crear la micro-spec versionada en `doc/micro-specs/` a partir del plan aprobado.
- Documentar README técnico/funcional del módulo si las convenciones vecinas lo usan.
- Completar changelog de la misión y registrar el patrón reusable en
  `.agents/knowledge/`.
- Actualizar `execution.log`, regenerar `diff.patch` y conservar
  `verification.json` pasado.

## Riesgos controlados

- `write` puede cambiar `gradebook_subject_id`: se revisarán tanto la libreta anterior
  como la posterior.
- `unlink` elimina la relación: se capturan las libretas antes de `super()` y se llama
  al trigger después.
- `create` de `isep_gradebook` reescribe `scoring_total`: el autocierre debe ejecutarse
  al final de toda la lógica heredada mediante el `super()` del módulo nuevo.
- La validación original puede fallar por cantidades de template: se captura únicamente
  `UserError`, dejando la transacción y la libreta en `in_progress`.
- El checkout contiene cambios locales ajenos y está detrás del remoto: no se tocarán
  esos archivos ni se sincronizará la rama durante esta misión.

## Definición de terminado

La misión solo termina si `verification.json` tiene `status: passed`, las revisiones no
tienen hallazgos Critical/Important pendientes, la documentación está persistida y el
diff se limita al módulo/artefactos/documentación de esta misión. El resultado se
presentará al usuario para revisión sin push remoto.
