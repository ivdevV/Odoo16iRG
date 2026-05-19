# irg_survey_second_attempt_fix

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `isep_survey`

---

## ¿Qué hace este módulo?

Corrige un bug por el que al realizar el segundo intento de un examen (slide tipo survey), siempre se mostraba la nota del primer intento en lugar de la del intento actual. El fix asegura que cada intento muestre correctamente su propia puntuación.

## Funcionalidades principales

- Corrección del cálculo de nota en el segundo (y posteriores) intentos.
- Sin cambios de modelo ni de vistas; es un fix de lógica en Python.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `survey.user_input` (o slide relacionado) | Herencia | Fix en cálculo de nota por intento |

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
