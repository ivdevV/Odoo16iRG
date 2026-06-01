# irg_admission_class_start_date

**Categoria:** extrairg
**Version:** 16.0.1.0.1
**Licencia:** LGPL-3
**Instalable:** Si
**Autor:** IRG
**Depende de:** `openeducat_admission`

---

## Que hace este modulo

Anade el campo `Fecha de inicio de clases` al formulario de admisiones de OpenEduCat (`op.admission`). El campo permite registrar una fecha propia de inicio de clases por admision, separada de la fecha de admision, la fecha de solicitud, la fecha de vencimiento, la fecha de inicio de cuotas y el lote.

## Funcionalidades principales

- Campo fecha opcional en `op.admission`.
- Campo visible solo en el formulario de admision.
- Campo no copiable al duplicar una admision.
- Campo editable desde la admision, sin bloqueo especifico por estado.
- Campo independiente del lote; no es related, computed ni sincronizado con `batch_id`.
- Sin cambios en listados, busquedas, agrupaciones, automatizaciones ni permisos.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `op.admission` | Herencia | `irg_class_start_date` |

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
4. Reabrir la admision y confirmar que la fecha persiste.
5. Revisar una admision en estado `done` y confirmar que el campo sigue siendo editable si el usuario tiene permisos de escritura sobre admisiones.

## Limitaciones conocidas

- El campo es informativo; no alimenta calendarios, pagos, aperturas de asignaturas ni automatizaciones.
- El campo no se calcula desde el lote ni actualiza datos del lote.
- No se muestra en listados ni en filtros de busqueda por decision funcional inicial.

## Rollback

Desinstalar `irg_admission_class_start_date` desde Apps o revertir el commit que introduce el modulo y actualizar la instancia. El modulo no modifica datos nativos de OpenEduCat ni cambia flujos existentes.