# irg_auto_translate

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `website`, `openeducat_core`, `irg_language_nav`

---

## ¿Qué hace este módulo?

Automatiza la traducción de nombres de cursos y asignaturas usando DeepL o Google Translate. Las traducciones se generan mediante un cron programado para no bloquear la interfaz, y la lógica se ejecuta completamente dentro de `ir.cron` (sin hilos en background).

## Funcionalidades principales

- Traducción automática de nombres de `op.course` y `op.subject`.
- Soporte para DeepL y Google Translate como proveedores.
- `post_init_hook` que encola cursos y asignaturas existentes para traducción.
- Cron de procesamiento de cola de traducción.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `op.course` | Herencia | Cola de traducción |
| `op.subject` | Herencia | Cola de traducción |

## Notas técnicas

- Todas las llamadas a la API externa se ejecutan de forma síncrona dentro del cron.
- Las credenciales de la API se configuran en los parámetros del sistema.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_auto_translate \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_auto_translate \
    --stop-after-init --db_host=pgodoo_latest
```
