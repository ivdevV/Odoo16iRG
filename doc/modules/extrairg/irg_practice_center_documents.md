# irg_practice_center_documents

**Categoria:** extrairg
**Version:** 16.0.1.0.1
**Licencia:** LGPL-3
**Instalable:** Si
**Autor:** IRG
**Depende de:** `isep_practices_2`

---

## Que hace este modulo

Añade una seccion de documentacion en la ficha backend de `Practice Centers` para subir adjuntos del centro de practicas. La seccion aparece antes de `Practice Schedules`, de forma que el equipo pueda consultar o cargar documentos antes de revisar los horarios del centro.

## Funcionalidades principales

- Añade el campo `document_ids` al modelo `practice.center`.
- Permite asociar multiples registros `ir.attachment` a un centro de practicas.
- Inserta la seccion `Center Documentation` en la vista formulario de `practice.center`.
- Muestra los nombres de los documentos adjuntos en una lista de solo lectura bajo el control de subida.
- Mantiene el cambio fuera del portal del alumno.

## Diseno tecnico

El modulo hereda `practice.center` y añade un campo Many2many hacia `ir.attachment`:

```python
document_ids = fields.Many2many(
    comodel_name='ir.attachment',
    relation='irg_practice_center_attachment_rel',
    column1='practice_center_id',
    column2='attachment_id',
)
```

La vista se extiende mediante `inherit_id="isep_practices_2.view_practice_center_form"` y un `xpath` sobre el campo `schedule_description`, evitando modificar el XML original de `isep_practices_2`.

## Vistas y UI

- `views/practice_center_views.xml` — añade `Center Documentation` antes de `Practice Schedules`.
- El campo usa el widget `many2many_binary`, por lo que el usuario interno puede subir archivos directamente desde el formulario.
- La misma relacion se muestra debajo en modo lista de solo lectura con la columna `Document Name`, para que los nombres de los adjuntos sean visibles.

## Seguridad

No crea modelos nuevos ni endpoints. No añade reglas de acceso propias porque reutiliza `ir.attachment` y el acceso existente al modelo `practice.center`. Los documentos no se exponen en portal ni en controladores web.

## Instalacion / actualizacion

```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_practice_center_documents \
    --stop-after-init --db_host=pgodoo_local
```

```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_practice_center_documents \
    --stop-after-init --db_host=pgodoo_local
```

## Pruebas realizadas

```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf \
    -d test_irg_db -u irg_practice_center_documents \
    --stop-after-init --test-enable \
    --test-tags /irg_practice_center_documents \
    --db_host=pgodoo_local --http-port=18069 --gevent-port=18072
```

Resultado: `0 failed, 0 error(s) of 3 tests`.

## Limitaciones conocidas

- Los adjuntos quedan pensados para gestion interna desde backend.
- No hay metadatos documentales adicionales como tipo, fecha de vencimiento o estado de revision.
- Los permisos siguen el comportamiento estandar de `ir.attachment` y del acceso interno a `practice.center`.

## Changelog

- 2026-05-26: Creado el modulo `irg_practice_center_documents`.
- 2026-05-26: Añadida seccion `Center Documentation` antes de `Practice Schedules`.
- 2026-05-26: Añadidos tests para validar campo de adjuntos y posicion en vista.
- 2026-05-26: Añadida lista de solo lectura para mostrar el nombre de los documentos adjuntos.
