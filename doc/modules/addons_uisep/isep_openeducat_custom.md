# isep_openeducat_custom

**Categoría:** addons_uisep
**Versión:** 16.0.1
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP
**Depende de:** `openeducat_core`, `openeducat_admission`, `openeducat_core_enterprise`, `openeducat_assignment_enterprise`

---

## ¿Qué hace este módulo?

Personalización base del paquete OpenEduCat para adaptarlo a las necesidades de ISEP. Añade campos, modifica comportamientos y establece reglas de negocio específicas del modelo educativo de ISEP sobre los modelos estándar de OpenEduCat.

## Funcionalidades principales

- Customizaciones de `op.student`, `op.admission`, `op.course`, `op.subject`.
- Adaptaciones del flujo de admisión al proceso de ISEP.
- Campos adicionales para el modelo educativo específico.
- Ajustes de reglas de acceso y visibilidad de datos.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `op.student` | Herencia | Campos adicionales ISEP |
| `op.admission` | Herencia | Flujo de admisión adaptado |
| `op.course` | Herencia | Configuraciones específicas ISEP |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i isep_openeducat_custom \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u isep_openeducat_custom \
    --stop-after-init --db_host=pgodoo_latest
```
