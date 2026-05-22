# irg_portal_student_fix

**Categoría:** Education
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `isep_student_filter`, `isep_gradebook`

---

## ¿Qué hace este módulo?

Este módulo corrige el error de control de acceso `403 Forbidden AccessError` que se produce cuando un usuario con rol de alumno/portal (por ejemplo, `saoyara@gmail.com`) inicia sesión e intenta acceder a su dashboard de portal. 

El problema original radicaba en los campos computados `total_completion_porc` (en el modelo `op.student`) y `completion_porc` (en el modelo `op.student.course`). Estos campos realizaban búsquedas y lecturas sobre modelos como `op.subject`, `app.gradebook.subject` y las propias relaciones de `op.student.course` utilizando el contexto de permisos del usuario de portal. Dado que estos usuarios carecen de permisos de lectura para dichos modelos de negocio, Odoo lanzaba un AccessError impidiendo el renderizado de la página.

## Funcionalidades principales

- **Acceso seguro a datos de progreso:** Sobreescribe los métodos de cómputo `_compute_total_completion` (en `op.student`) y `_compute_advance_search` (en `op.student.course`) heredando los modelos mediante el ORM de Odoo.
- **Uso de privilegios administrativos:** Ejecuta las consultas y búsquedas (`search`, `search_count`) sobre `op.student.course`, `op.subject` y `app.gradebook.subject` llamando a `.sudo()`, permitiendo que el progreso del alumno se calcule correctamente sin importar el contexto de permisos de seguridad de la sesión activa del portal.

## Estructura del módulo

- `models/op_student.py` — Sobreescrituras de `op.student` y `op.student.course` con la lógica optimizada y uso de `sudo()`.

## Instalación / Actualización

```bash
# Instalar en el contenedor local
docker exec odoo16irg_local odoo-bin -c /etc/odoo/odoo.conf -d test_irg_db -i irg_portal_student_fix --stop-after-init

# Actualizar en el contenedor local
docker exec odoo16irg_local odoo-bin -c /etc/odoo/odoo.conf -d test_irg_db -u irg_portal_student_fix --stop-after-init
```
