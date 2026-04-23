# irg_quiz_auto_scoring

**Categoría:** extrairg
**Versión:** 16.0.1.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG Inc
**Depende de:** `survey`

---

## ¿Qué hace este módulo?

Automatiza el cálculo de puntuaciones de surveys y cuestionarios, y sincroniza los resultados con el sistema de calificaciones. Los alumnos que completan un cuestionario tienen sus notas actualizadas automáticamente en la libreta de calificaciones sin intervención manual del docente.

## Funcionalidades principales

- Auto-cálculo de puntuaciones al finalizar un cuestionario.
- Sincronización automática de la nota del cuestionario con la libreta de calificaciones.
- Compatible con el flujo de surveys de eLearning (slides).

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `survey.user_input` | Herencia | Lógica de auto-scoring |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_quiz_auto_scoring \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_quiz_auto_scoring \
    --stop-after-init --db_host=pgodoo_latest
```
