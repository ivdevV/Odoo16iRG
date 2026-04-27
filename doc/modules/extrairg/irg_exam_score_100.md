# irg_exam_score_100

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG Inc
**Depende de:** `survey`

---

## ¿Qué hace este módulo?

Proporciona el campo de compatibilidad `x_exam_auto_scale_100` en el modelo `survey.survey` para vistas que lo referencian. Este campo indica si el examen debe escalarse automáticamente a 100 puntos, permitiendo normalizar la puntuación de exámenes con diferente número de preguntas.

## Funcionalidades principales

- Campo técnico `x_exam_auto_scale_100` en `survey.survey`.
- Compatible con vistas que necesitan este campo para funcionar correctamente.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `survey.survey` | Herencia | `x_exam_auto_scale_100` (Boolean) |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_exam_score_100 \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_exam_score_100 \
    --stop-after-init --db_host=pgodoo_latest
```
