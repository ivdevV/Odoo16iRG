# irg_identification_types

**Categoría:** extrairg
**Versión:** 16.0.2.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `l10n_latam_base`

---

## ¿Qué hace este módulo?

Restringe los tipos de identificación disponibles a los usados en España: DNI, Pasaporte y Documento Identificativo. Simplifica la interfaz al eliminar los tipos de identificación no relevantes para el mercado español, evitando errores de entrada de datos.

Usa un `post_migrate` hook para limpiar tipos de identificación inválidos.

## Funcionalidades principales

- Datos iniciales con los tres tipos de identificación permitidos.
- Hook `post_migrate` para eliminar tipos no permitidos.
- Restricción en el campo de tipo de identificación en formularios de contacto/alumno.

## Notas técnicas

- Depende de `l10n_latam_base` que provee el modelo `l10n_latam.identification.type`.
- `post_migrate` se ejecuta tras cada actualización para mantener el catálogo limpio.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_identification_types \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_identification_types \
    --stop-after-init --db_host=pgodoo_latest
```
