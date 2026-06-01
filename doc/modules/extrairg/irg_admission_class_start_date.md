# irg_admission_class_start_date

**Categoria:** extrairg
**Version:** 16.0.1.0.2
**Licencia:** LGPL-3
**Instalable:** Si
**Autor:** IRG
**Depende de:** `openeducat_admission`

---

## Que hace este modulo

Anade el campo `Fecha de inicio de clases` al formulario de admisiones de OpenEduCat (`op.admission`) y sincroniza automaticamente la fecha de vencimiento con la fecha de fin del lote asignado. El campo permite registrar una fecha propia de inicio de clases por admision, separada de la fecha de admision, la fecha de solicitud, la fecha de vencimiento, la fecha de inicio de cuotas y el lote.

## Funcionalidades principales

- Campo fecha opcional en `op.admission`.
- Campo visible solo en el formulario de admision.
- Campo no copiable al duplicar una admision.
- Campo editable desde la admision, sin bloqueo especifico por estado.
- El campo `irg_class_start_date` es independiente del lote; no es related, computed ni sincronizado con `batch_id`.
- `due_date` se autocompleta con `batch_id.end_date` cuando se asigna o cambia lote.
- Sin cambios en listados, busquedas, agrupaciones ni permisos.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `op.admission` | Herencia | `irg_class_start_date`, autocompletado de `due_date` desde `batch_id.end_date` |

## Vistas y UI

- `views/op_admission_views.xml` hereda `openeducat_admission.view_op_admission_form`.
- El campo se inserta despues de `due_date` dentro de la pestana de detalle de admision.

## Instalacion / Actualizacion

Instalar o actualizar el modulo en la instancia Odoo 16 donde este disponible el addon path de `addons-extra/extrairg`.

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
	-d <dbname> -i irg_admission_class_start_date \
	--stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
	-d <dbname> -u irg_admission_class_start_date \
	--stop-after-init --db_host=pgodoo_latest
```

## Validacion funcional

1. Abrir una admision existente o crear una nueva.
2. Confirmar que aparece el campo `Fecha de inicio de clases` despues de `Due Date`.
3. Seleccionar una fecha y guardar.
4. Asignar o cambiar el lote y confirmar que `Due Date` toma automaticamente la `End Date` del lote.
5. Reabrir la admision y confirmar que la fecha guardada persiste.
6. Revisar una admision en estado `done` y confirmar que el campo sigue siendo editable si el usuario tiene permisos de escritura sobre admisiones.

## Limitaciones conocidas

- El campo `irg_class_start_date` es informativo; no alimenta calendarios, pagos ni aperturas de asignaturas.
- La sincronizacion automatica solo aplica a `due_date` en eventos de asignacion/cambio de lote.
- No se muestra en listados ni en filtros de busqueda por decision funcional inicial.

## Consideraciones de sincronizacion de vencimiento

- En formulario (`onchange` de `batch_id`), si el lote tiene `end_date`, `due_date` se sincroniza automaticamente con ese valor.
- En `create` y `write`, la sincronizacion automatica se aplica siempre que se asigne/cambie `batch_id`, incluso en flujos manuales.
- Si se informa `batch_id`, el valor final de `due_date` queda forzado a `batch_id.end_date`.

## Rollback

Desinstalar `irg_admission_class_start_date` desde Apps o revertir el commit que introduce el modulo y actualizar la instancia. El modulo no modifica datos nativos de OpenEduCat ni cambia flujos existentes.
