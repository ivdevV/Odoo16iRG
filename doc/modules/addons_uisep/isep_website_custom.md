# isep_website_custom

**Categoría:** addons_uisep
**Versión:** 0.1
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP
**Depende de:** `base`, `website`, `website_slides`, `openeducat_admission`, `isep_openeducat_custom`, `openeducat_core_enterprise`

---

## ¿Qué hace este módulo?

Módulo base del campus virtual de ISEP. Implementa el perfil de usuario en el portal con las secciones del campus: acceso a cursos/asignaturas, sidebar de navegación, panel de dashboard del alumno y tarjetas de acceso rápido por curso. Es la piedra angular de la experiencia del alumno en el sitio web.

## Funcionalidades principales

- Perfil de usuario del campus con secciones de cursos y asignaturas.
- Sidebar de navegación del campus.
- Dashboard del alumno con resumen de progreso.
- Tarjetas de acceso por curso (eLearning).
- Lógica de permisos de acceso al campus.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `op.student` | Herencia | Campos de acceso web |
| `res.users` | Herencia | Vinculación con `op.student` |

## Vistas y UI

- `views/user_profile_templates.xml` — perfil del alumno en el portal.
- `views/campus_dashboard.xml` — dashboard del campus.
- `views/campus_sidebar.xml` — sidebar de navegación.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i isep_website_custom \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u isep_website_custom \
    --stop-after-init --db_host=pgodoo_latest
```
