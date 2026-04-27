# irg_survey_regrade_attempts

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `survey`, `isep_survey`, `isep_gradebook`

---

## ¿Qué hace este módulo?

Permite a los administradores recalificar intentos de cuestionario ya completados (`survey.user_input`) y sincronizar la nueva nota con la libreta de calificaciones. Útil cuando hay errores en la puntuación original o cuando se ajustan los criterios de calificación.

## Funcionalidades principales

- Botón de "Recalificar" en el formulario del intento de cuestionario.
- Recalcula la puntuación del intento y actualiza la libreta.
- Integración con `isep_gradebook` para la sincronización de notas.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `survey.user_input` | Herencia | Botón y método de recalificación |

## Vistas y UI

- `views/survey_user_input_views.xml` — botón de recalificación en el formulario.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_survey_regrade_attempts \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_survey_regrade_attempts \
    --stop-after-init --db_host=pgodoo_latest
```
