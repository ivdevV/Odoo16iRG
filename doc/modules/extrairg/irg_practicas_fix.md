# irg_practicas_fix

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `isep_practices_2`

---

## ¿Qué hace este módulo?

Corrige el campo `user_id` en el módulo de prácticas para que esté relacionado (`related`) al campo `user_id` del alumno (`op_student_id.user_id`). Este fix permite que la asignación de usuario en las prácticas sea coherente con el usuario del sistema vinculado al alumno.

## Funcionalidades principales

- Redefine `user_id` en el modelo de prácticas como campo relacionado al alumno.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| Modelo de prácticas (herencia de `isep_practices_2`) | Herencia | `user_id` como `related` |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_practicas_fix \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_practicas_fix \
    --stop-after-init --db_host=pgodoo_latest
```
