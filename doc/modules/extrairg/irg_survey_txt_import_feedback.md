# irg_survey_txt_import_feedback

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `survey`, `website_slides_survey`, `isep_survey`

---

## ¿Qué hace este módulo?

Proporciona un wizard para importar preguntas de tipo test (4 opciones) desde archivos TXT, con feedback genérico automático. Permite a los docentes crear baterías de preguntas de forma masiva sin entrar una a una en la interfaz de encuestas.

## Funcionalidades principales

- Wizard de importación de preguntas desde TXT.
- Formato esperado: pregunta con 4 opciones (a-d) e indicación de la respuesta correcta.
- Generación automática de feedback genérico para cada pregunta.
- Integración con el tipo de slide `survey` del eLearning.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.survey.txt.import.wizard` (nuevo) | Nuevo | Archivo TXT, encuesta destino |

## Vistas y UI

- `views/survey_views.xml` — botón de importación en la encuesta.
- `views/survey_txt_import_wizard_views.xml` — formulario del wizard.

## Notas técnicas

- Requiere `security/ir.model.access.csv` por el modelo del wizard.
- Dependencia Python de `requests` no aplica (no usa `external_dependencies`).

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_survey_txt_import_feedback \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_survey_txt_import_feedback \
    --stop-after-init --db_host=pgodoo_latest
```
