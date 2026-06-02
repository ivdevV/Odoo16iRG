# irg_practice_center_documents_consistency

**Categoria:** extrairg
**Version:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Si
**Autor:** IRG
**Depende de:** `irg_practice_center_documents`

---

## Que hace este modulo

Corrige la consistencia del guardado de documentos en centros de practicas (`practice.center`). El modulo evita mostrar el mismo campo `document_ids` dos veces en el formulario y normaliza los adjuntos nuevos para que queden vinculados al centro correcto.

## Funcionalidades principales

- Añade el campo readonly `document_display_ids` en `practice.center`.
- Reutiliza la misma tabla relacional `irg_practice_center_attachment_rel` que `document_ids` para no duplicar relaciones.
- Reemplaza la lista readonly duplicada de `document_ids` por `document_display_ids`.
- Mantiene un unico campo editable `document_ids` con widget `many2many_binary`.
- Normaliza adjuntos nuevos o sin vinculacion previa con `res_model='practice.center'` y `res_id` del centro.
- Evita reasignar adjuntos que ya pertenecen a otro recurso.

## Diseno tecnico

El modulo hereda `practice.center` y declara un segundo campo Many2many readonly sobre la misma tabla que usa `document_ids`:

```python
document_display_ids = fields.Many2many(
    comodel_name='ir.attachment',
    relation='irg_practice_center_attachment_rel',
    column1='practice_center_id',
    column2='attachment_id',
    readonly=True,
)
```

La normalizacion se ejecuta despues de `create()` y despues de `write()` cuando cambia `document_ids`. Solo actualiza adjuntos sin `res_id` y con `res_model` vacio o `practice.center`; no usa `sudo()`.

## Vistas y UI

- `views/practice_center_views.xml` hereda `irg_practice_center_documents.view_practice_center_form_documents`.
- El campo editable original `document_ids` se conserva con `widget="many2many_binary"`.
- La segunda aparicion readonly de `document_ids` se reemplaza por `document_display_ids`.
- La lista readonly sigue mostrando el nombre del archivo con la columna `Document Name`.

## Seguridad

No crea modelos nuevos, endpoints ni reglas de acceso. La escritura de metadatos en `ir.attachment` se realiza sin `sudo()`, por lo que respeta ACLs y reglas de registro existentes.

Los adjuntos ya vinculados a otro recurso no se reasignan automaticamente. Esto evita que un usuario con permisos sobre `practice.center` cambie la propiedad tecnica de documentos de otros modelos.

## Instalacion / actualizacion

```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_practice_center_documents_consistency \
    --stop-after-init --db_host=pgodoo_local
```

```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_practice_center_documents_consistency \
    --stop-after-init --db_host=pgodoo_local
```

## Pruebas realizadas

Sintaxis Python:

```bash
python3 -m compileall "addons-extra/extrairg/irg_practice_center_documents_consistency"
```

Tests Odoo locales:

```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf \
    -d test_irg_db -u irg_practice_center_documents_consistency \
    --stop-after-init --test-enable \
    --test-tags /irg_practice_center_documents_consistency \
    --db_host=pgodoo_local --http-port=18069 --gevent-port=18072
```

Resultado: `0 failed, 0 error(s) of 4 tests`.

Revision Security Advisor: aprobada con `[YES]` tras eliminar `sudo()` y cubrir con test que no se reasignan adjuntos ya vinculados a otro recurso.

## Limitaciones conocidas

- No crea un modelo documental con metadatos como tipo, caducidad o estado de revision.
- No expone documentos en portal.
- Si un usuario vincula manualmente un adjunto ya asociado a otro modelo, la relacion Many2many puede existir, pero el modulo no reasigna `res_model/res_id` para proteger la trazabilidad del adjunto.
- Si el usuario no tiene permiso para escribir sobre un adjunto nuevo, la normalizacion falla cerrado por las reglas estandar de Odoo.

## Changelog

- 2026-06-02: Creado el modulo `irg_practice_center_documents_consistency`.
- 2026-06-02: Separado el campo de carga `document_ids` del campo de visualizacion `document_display_ids`.
- 2026-06-02: Añadida normalizacion segura de adjuntos nuevos sin `sudo()`.
- 2026-06-02: Añadidos tests de vista, persistencia de adjuntos y proteccion contra reasignacion de adjuntos existentes.
