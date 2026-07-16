# IRG Gradebook Auto Close

Extensión para Odoo 16 que cierra automáticamente una libreta de alumno cuando
todas sus líneas tienen las notas requeridas. Reutiliza el cierre estándar de
`isep_gradebook`, por lo que conserva sus validaciones académicas.

## Comportamiento funcional

Una libreta se considera candidata cuando está en `in_progress` y contiene al menos
una línea. Cada línea debe tener:

- calificación final mayor que cero;
- promedio de exámenes mayor que cero, si muestra exámenes;
- promedio de asignaciones mayor que cero, si muestra asignaciones.

Los promedios correspondientes a bloques no aplicables se omiten. Así, una línea de
Prácticas o TFM sin asignaciones puede cerrar si el resto de sus notas requeridas es
positivo.

El cierre llama a `state_to_done()`. Si las cantidades de evaluaciones no coinciden
con el template y el método lanza `UserError`, el guardado de la nota continúa, se
registra un warning y la libreta permanece en proceso.

## Uso

No añade botones ni configuración. Después de instalar el módulo:

1. Introduzca o sincronice resultados en la libreta.
2. Al crear, modificar, mover o eliminar un resultado, el módulo reevalúa las
   libretas afectadas.
3. Cuando todas las líneas cumplen la condición y las validaciones del template,
   la libreta pasa a `done` (`Finalizado`).

Los botones existentes `state_to_in_progress()` y `action_draft()` conservan su
comportamiento. Reabrir una libreta no la vuelve a cerrar de inmediato; se reevalúa
solo después de una operación posterior sobre `app.gradebook.result`.

## Arquitectura y triggers

El módulo no crea modelos ni permisos. Hereda:

- `app.gradebook.student`: `_irg_is_ready_to_close()` comprueba las líneas y
  `_irg_try_auto_close()` invoca el cierre estándar capturando solo `UserError`.
- `app.gradebook.result`: ejecuta la reevaluación después de `create`, `write` y
  `unlink`.

Detalles de los hooks:

- `create` acepta lotes, ejecuta el create base por elemento por compatibilidad y
  reevalúa una vez al terminar el lote completo.
- `write` conserva y reevalúa tanto la libreta anterior como la nueva si cambia
  `gradebook_subject_id`; los writes multi-registro se delegan por registro porque
  el override base usa relaciones singleton.
- `unlink` conserva la referencia antes del borrado y reevalúa después de `super()`.

El create de `isep_gradebook` puede escribir internamente `scoring_total` durante el
redondeo. Esos writes anidados se ejecutan con la clave de contexto interna y
namespaced `irg_gradebook_auto_close_skip_nested_write_auto_close`, que difiere solo
el autocierre. Al finalizar, los registros se rebrowsean en contexto normal y las
libretas se evalúan con el lote completo. La clave no forma parte de la API pública.

## Instalación y actualización local

Dependencia: `isep_gradebook`.

Las pruebas y operaciones locales del proyecto deben usar
`docker-compose.local.yml`. Para instalar o actualizar en la base de pruebas:

```bash
docker compose -f docker-compose.local.yml run --rm odoo_local odoo \
  -c /etc/odoo/odoo.conf -d test_irg_db -u irg_gradebook_auto_close \
  --stop-after-init
```

En una instalación inicial puede sustituirse `-u` por `-i`.

## Pruebas

La suite es `TransactionCase`, está etiquetada `post_install` y contiene 13 tests:

- cinco escenarios funcionales aprobados;
- tres pruebas directas de la condición;
- write multi-registro;
- create simple de la última nota;
- unlink después de `super()`;
- cambio de línea con libreta anterior y nueva;
- create por lotes con redondeo y write anidado.

Ejecución:

```bash
docker compose -f docker-compose.local.yml run --rm odoo_local odoo \
  -c /etc/odoo/odoo.conf -d test_irg_db -u irg_gradebook_auto_close \
  --test-enable --test-tags /irg_gradebook_auto_close \
  --stop-after-init --log-level=test
```

La validación independiente de 2026-07-15 obtuvo 13 tests, 0 fallos y 0 errores.

## Limitaciones y advertencias

- Solo se reevalúa por operaciones sobre `app.gradebook.result`; cambiar templates,
  flags o líneas por otra ruta no dispara el autocierre.
- Las notas y promedios deben ser estrictamente mayores que cero. El cero bloquea el
  cierre.
- Las validaciones de cantidades del template siguen prevaleciendo. Un fallo deja
  warning en logs y mantiene la libreta abierta.
- Desinstalar el módulo no reabre libretas cerradas anteriormente.
- No deben reutilizarse ni inyectarse externamente las claves de contexto internas.
- Los warnings preexistentes de otros módulos del entorno no pertenecen a este addon;
  consulte la evidencia de la misión para distinguirlos del resultado objetivo.
