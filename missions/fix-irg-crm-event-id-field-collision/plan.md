# Plan de misión: colisión de `event_id`

- **Tier:** standard. Corrección de instalación localizada que protege un esquema de datos existente.
- **Causa raíz:** la columna `crm_lead.event_id` ya es una clave foránea entera, según el error `DatatypeMismatch` de PostgreSQL.
- **Cambio:** usar `irg_event_id` como nuevo campo Char y conservar su etiqueta de interfaz.
- **Riesgos:** ninguno sobre datos existentes, porque no hay conversión SQL ni migración.
- **Pruebas:** validación estática; Docker/Odoo quedan excluidos por instrucción del usuario.
