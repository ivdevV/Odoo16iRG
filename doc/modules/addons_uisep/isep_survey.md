# isep_survey

**Categoría:** addons_uisep
**Versión:** 16.0
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP
**Depende de:** `survey`, `mail`, `isep_survey_attachment`, `website_slides_survey`, `openeducat_admission`

---

## ¿Qué hace este módulo?

Adapta el módulo de encuestas de Odoo para la integración académica. Permite vincular encuestas/exámenes a asignaturas y admisiones, gestiona los adjuntos de exámenes y permite la entrega de exámenes en el contexto del eLearning del campus.

## Funcionalidades principales

- Vinculación de encuestas con asignaturas y admisiones.
- Gestión de adjuntos en las encuestas (enunciados, recursos).
- Integración con el portal de eLearning para entrega de exámenes.
- Plantillas de email para entrega y corrección de exámenes.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `survey.survey` | Herencia | Asignatura, admisión, tipo de evaluación |
| `survey.user_input` | Herencia | Vinculación con el alumno |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i isep_survey \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u isep_survey \
    --stop-after-init --db_host=pgodoo_latest
```
