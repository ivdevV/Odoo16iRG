# irg_vacation_30_day_cap

## Proposito

`irg_vacation_30_day_cap` limita el consumo anual de vacaciones a un maximo de 30 dias por empleado y por ano natural.

El limite se aplica exclusivamente al tipo de ausencia de vacaciones identificado por el external ID:

```text
nomina_cfdi_extras_ee.hr_holidays_status_vac
```

El modulo no modifica otros tipos de ausencia ni otras reglas de recursos humanos.

El modulo depende tecnicamente solo de `hr_holidays`. La integracion con `nomina_cfdi_extras_ee` es opcional en el manifest para evitar que la instalacion fuerce la carga de modulos de nomina mexicana. Si el external ID de vacaciones no existe en la base, la regla no se aplica hasta que exista.

## Alcance funcional

- Bloquea solicitudes, modificaciones o validaciones de vacaciones que superen 30 dias acumulados en el mismo ano natural para el mismo empleado.
- Cuenta vacaciones existentes en estado `validate` y `validate1`.
- Excluye el registro actual al recalcular el acumulado durante modificaciones o validaciones.
- No reescribe asignaciones existentes.
- No cambia el maximo mostrado en la interfaz de Odoo.
- No cambia la configuracion del tipo de ausencia; solo bloquea el consumo o validacion por encima del limite anual.
- No fuerza la instalacion de `nomina_cfdi_extras_ee` ni de `nomina_cfdi_ee`.

## Diseno tecnico

### Modelo extendido

El modulo hereda el modelo Odoo:

```text
hr.leave
```

La validacion se implementa sobre las operaciones de creacion, escritura y cambio de estado de ausencias.

### Constantes

El diseno usa constantes para centralizar:

- El external ID del tipo de ausencia de vacaciones: `nomina_cfdi_extras_ee.hr_holidays_status_vac`.
- El limite anual permitido: 30 dias.
- Los estados computables para el acumulado: `validate` y `validate1`.

La busqueda del tipo de vacaciones usa `env.ref(..., raise_if_not_found=False)`. Esto permite instalar el modulo aunque la nomina mexicana no este instalada o aunque una dependencia externa falle durante su carga.

### Ganchos de validacion

La regla se comprueba en los siguientes puntos del ciclo de vida de `hr.leave`:

- `create`: valida nuevas solicitudes de vacaciones, incluso antes de aprobacion.
- `write`: valida cambios que puedan alterar empleado, tipo de ausencia, fechas, duracion o estado, incluso antes de aprobacion.
- `action_approve`: valida antes de aprobar cuando la ausencia pasa por aprobacion intermedia.
- `action_validate`: valida antes de confirmar definitivamente la ausencia.

### Calculo del acumulado

Para cada solicitud afectada, el modulo calcula los dias de vacaciones ya existentes del empleado dentro del ano natural correspondiente.

El conteo se realiza por dias de calendario cubiertos por `request_date_from` y `request_date_to`, aplicando solo el tramo que solapa con el ano natural evaluado.

El acumulado considera:

- El mismo empleado.
- El tipo de ausencia de vacaciones definido por el external ID indicado.
- Estados `validate` y `validate1`.
- Fechas dentro del ano natural evaluado.

El calculo excluye el registro actual para evitar doble conteo cuando se edita o valida una ausencia ya existente.

## Instalacion y actualizacion

Ejecutar los comandos desde la raiz del repositorio.

El modulo no instala automaticamente `nomina_cfdi_extras_ee`. Para que la regla tenga efecto, la base debe tener disponible el external ID `nomina_cfdi_extras_ee.hr_holidays_status_vac`.

### Instalar el modulo en una base local

Ejemplo con `docker-compose.local.yml`:

```bash
docker compose -f docker-compose.local.yml run --rm odoo_local odoo \
  -d <base_datos> \
  -i irg_vacation_30_day_cap \
  --stop-after-init
```

### Actualizar el modulo en una base local

```bash
docker compose -f docker-compose.local.yml run --rm odoo_local odoo \
  -d <base_datos> \
  -u irg_vacation_30_day_cap \
  --stop-after-init
```

### Ejecutar pruebas del modulo

```bash
docker compose -f docker-compose.local.yml run --rm odoo_local odoo \
  -d <base_datos> \
  -i irg_vacation_30_day_cap \
  --test-enable \
  --test-tags /irg_vacation_30_day_cap \
  --stop-after-init
```

Sustituir `<base_datos>` por la base local de pruebas correspondiente.

## Comportamiento de uso

Cuando un usuario crea, modifica, aprueba o valida vacaciones del tipo `nomina_cfdi_extras_ee.hr_holidays_status_vac`, Odoo comprueba el total anual del empleado.

Si el total resultante supera 30 dias en el ano natural, la operacion se bloquea con un error en espanol. El mensaje esperado debe indicar que el empleado no puede superar 30 dias de vacaciones por ano natural.

La regla se aplica por empleado y por ano natural. Por ejemplo, una solicitud de vacaciones de 2026 no consume limite de 2027.

## Cobertura de pruebas

La cobertura automatizada del modulo esta incluida en:

```text
addons-extra/extrairg/irg_vacation_30_day_cap/tests/test_vacation_30_day_cap.py
```

Las pruebas cubren la regla de limite anual, bloqueos en validacion, creacion y escritura, el uso del tipo de ausencia de vacaciones esperado, que otros tipos de ausencia no se ven afectados, que otros empleados no se ven afectados y que anos naturales diferentes se computan por separado.

## Validacion realizada

- `python3 -m py_compile` paso correctamente para el codigo Python del modulo.
- Se intento ejecutar el comando de pruebas Odoo mediante `docker-compose.local.yml`.
- La ejecucion quedo bloqueada antes de llegar a las pruebas del modulo por una dependencia externa: `nomina_cfdi_ee` falla al cargar `data/res.bank.csv` por validacion invalida de BIC/SEPA.
- Se corrigio el manifest para que `irg_vacation_30_day_cap` no fuerce la instalacion de `nomina_cfdi_extras_ee` ni arrastre el fallo de carga de `nomina_cfdi_ee`.

Este bloqueo corresponde al entorno o a la dependencia `nomina_cfdi_ee`; no es un fallo de pruebas de `irg_vacation_30_day_cap`.

## Limitaciones

- No reescribe asignaciones de vacaciones existentes.
- No cambia el maximo mostrado en la interfaz de Odoo.
- Bloquea consumo, aprobacion o validacion por encima de 30 dias; no modifica saldos historicos.
- El periodo de control es el ano natural.
- La regla depende funcionalmente de que exista el external ID `nomina_cfdi_extras_ee.hr_holidays_status_vac`; si no existe, el modulo se instala pero no bloquea ausencias.
- Solo aplica al tipo de ausencia de vacaciones identificado por ese external ID.

## Changelog

### 2026-06-10

- Version inicial de la documentacion del modulo `irg_vacation_30_day_cap`.
- Documentado el limite anual de 30 dias de vacaciones por empleado y ano natural.
- Documentados diseno tecnico, comandos de instalacion/actualizacion, comportamiento de uso, validacion realizada, cobertura de pruebas y limitaciones conocidas.
- Corregida la dependencia dura de `nomina_cfdi_extras_ee` para evitar que la instalacion del modulo arrastre el fallo de `nomina_cfdi_ee/data/res.bank.csv`.
- Ajustado el bloqueo para aplicar tambien en solicitudes creadas o modificadas antes de aprobacion.
- Ajustado el calculo de dias para usar el solape de fechas solicitadas en lugar del valor dependiente de calendario `number_of_days`.
