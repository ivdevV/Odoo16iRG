# isep_elearning_custom

**Categoría:** addons_uisep
**Versión:** 16.0.2
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP
**Depende de:** `website_slides`, `isep_openeducat_custom`, `openeducat_core`, `openeducat_admission`, `openeducat_core_enterprise`, `openeducat_admission_enterprise`

---

## ¿Qué hace este módulo?

Personalizaciones del módulo de eLearning de Odoo para el sistema educativo de ISEP. Gestiona el enrollado de alumnos en cursos de eLearning, el envío de emails de bienvenida al curso, restricciones de acceso por perfil de alumno y crons de actualización de acceso a contenidos.

## Funcionalidades principales

- Cron de enrollado masivo de alumnos en canales de eLearning.
- Cron de actualización de estados de acceso al contenido.
- Plantillas de email de bienvenida al curso.
- Restricciones de acceso a contenidos según el estado del alumno.
- Integración con la admisión para enrollar en el canal del curso.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `slide.channel` | Herencia | Lógica de enrollado, restricciones de acceso |
| `op.admission` | Herencia | Enrollado en eLearning al confirmar |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i isep_elearning_custom \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u isep_elearning_custom \
    --stop-after-init --db_host=pgodoo_latest
```
