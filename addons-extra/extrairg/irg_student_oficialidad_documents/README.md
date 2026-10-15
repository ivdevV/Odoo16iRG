# irg_student_oficialidad_documents

Documentos de oficialidad del alumno (Unimarconi) en Odoo 16.

- Catalogo `irg.oficialidad.document.type` con 7 claves (nacional, internacional y `matricula-unimarconi` para ambos).
- Modelo `irg.oficialidad.document` con `UNIQUE(partner_id, document_type_id)`; el archivo se guarda como adjunto privado.
- En `res.partner` / `op.student`: tipo de alumno (`irg_oficialidad_student_type`), resumen `X/4`, checklist y aviso (solo informativo) si el VAT no encaja con el tipo.
- Pestaña **Detalle Oficialidad** del alumno: resumen, checklist y lista de documentos descargables. Se conserva el bloque `annex_9`.
- ACL: documentos con CRUD para usuarios internos (`base.group_user`); catalogo de solo lectura para internos y editable por administradores; nada para portal ni publico. Menu de documentos solo para administradores.

Los documentos llegan por el webhook del modulo `irg_student_oficialidad_webhook`; ver [documentacion](../../../doc/modules/extrairg/irg_student_oficialidad_webhook.md).

## Dependencias

`base`, `openeducat_core`, `isep_control_escolar`.

## Tests

```bash
odoo -d <dbname> -i irg_student_oficialidad_documents --test-enable \
    --test-tags=/irg_student_oficialidad_documents --stop-after-init
```

En una BD nueva hay que instalar antes `isep_gradebook` y `isep_control_escolar` (dependencia no declarada previa de `isep_control_escolar`).
