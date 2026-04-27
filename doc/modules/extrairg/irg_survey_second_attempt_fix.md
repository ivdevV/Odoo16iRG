# irg_survey_second_attempt_fix

**Categoría:** extrairg
**Versión:** 16.0.1.1.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `isep_survey`

---

## ¿Qué hace este módulo?

Habilita el segundo intento real en exámenes tipo test de eLearning y corrige un bug por el que, al volver al examen, se mostraba la calificación del primer intento en lugar de permitir iniciar un nuevo intento. El fix asegura un mínimo de dos intentos para surveys académicos tipo examen y mantiene la puntuación correcta por intento.

## Funcionalidades principales

- Configura los surveys tipo `exam` con `is_attempts_limited=True` y `attempts_limit=2` como mínimo.
- Corrige exámenes ya existentes durante instalación y actualización del módulo.
- Corrige el cálculo de estado aprobado/suspenso (`scoring_success`) en el segundo y posteriores intentos.
- Sin cambios de vistas; es un fix de lógica en Python.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `survey.survey` | Herencia | Límite mínimo de dos intentos para exámenes |
| `survey.user_input` | Herencia | Fix en cálculo de nota y estado por intento |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_survey_second_attempt_fix \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_survey_second_attempt_fix \
    --stop-after-init --db_host=pgodoo_latest
```
