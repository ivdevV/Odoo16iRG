# Plan — irg-admission-register-export-nationality

## Alcance

Añadir la columna **Nacionalidad** al Excel (y al CSV, que comparte las mismas columnas) que genera el wizard de `irg_admission_register_export` desde cada `op.admission.register`.

Fuente del dato, confirmada: `op.student.nationality` (`res.country`), vía `admission.student_id.nationality`. No se usa `citizenship_country_id` ni `partner.country_id`.

Si la admisión no tiene alumno o el alumno no tiene nacionalidad, la celda queda vacía.

## Clasificación

- Tier misión: `full` (cambio de comportamiento del producto en un export operativo).
- Capacidad: `standard` (lógica acotada, 2–5 archivos funcionales, contexto claro).
- Security Advisor: no aplica (ni autenticación, ni migraciones, ni secretos, ni borrado histórico).
- E2E TestSprite: `skipped`. El diff no toca vistas/QWeb, `static/`, portal, `website`, controladores HTTP ni plantillas de diploma/certificado; solo Python del wizard y tests.

## Knowledge consultada

- `.agents/knowledge/odoo_development_modding/artifacts/student_partner_delegated_fields.md`: `nationality` vive en `op.student`, no es campo delegado de `res.partner`.
- `.agents/knowledge/odoo_development_modding/artifacts/irg_admission_gender_fix.md`: patrón de fixtures de admisión; no se reutiliza su dependencia de `period`.
- Misión `student-birth-citizenship-fields`: `citizenship_country_id` es independiente de `nationality`; queda fuera de alcance.

## Diseño técnico

- Módulo existente (pedido explícito): `addons-extra/extrairg/irg_admission_register_export`.
- Un único punto de cambio funcional: lista `_COLUMNS` en `wizard/admission_export_wizard.py`. `_get_rows`, `_build_csv` y `_build_xlsx` ya recorren esa lista.
- Extraer: `a.student_id.nationality.name or ''`.
- Posición: al final, tras `Estado`, para no desplazar las columnas actuales.
- Etiqueta: `Nacionalidad`.
- Versión del módulo: `16.0.1.0.0` → `16.0.1.1.0`.
- Sin cambios de seguridad, XML ni dependencias.

## Archivos

- Modificar: `addons-extra/extrairg/irg_admission_register_export/wizard/admission_export_wizard.py`
- Modificar: `addons-extra/extrairg/irg_admission_register_export/__manifest__.py`
- Crear: `addons-extra/extrairg/irg_admission_register_export/tests/__init__.py`
- Crear: `addons-extra/extrairg/irg_admission_register_export/tests/test_admission_export.py`
- Documentar: `doc/modules/extrairg/irg_admission_register_export.md`, `doc/modules/INDEX.md`, changelog de misión.

## Criterios de aceptación

1. El Excel (y el CSV) incluye la cabecera `Nacionalidad`.
2. El valor es el nombre de `student_id.nationality`.
3. Sin alumno o sin nacionalidad → cadena vacía.
4. El resto de columnas no cambia de orden ni de etiqueta.

## Pruebas

TDD en runtime `docker-compose.local.yml`, base desechable:

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf -d test_irg_arex_nat_20260908 \
  -i irg_admission_register_export --test-enable \
  --test-tags=/irg_admission_register_export --stop-after-init \
  --http-port=8099 --log-level=test
```

RED: tests que exigen la columna y el valor **antes** de tocar `_COLUMNS`.
GREEN: columna mínima y misma suite en verde.
Validación: el validador repite syntax + suite en otra base desechable, sin editar código.

Al terminar: drop de bases de prueba y evidencia de limpieza.

## Roles

1. Plan — orquestador (este documento).
2. Implementación/TDD — coder.
3. Review — agente distinto del coder, solo código y tests.
4. Validación — agente distinto del coder; emite `verification.json`.
5. Documentación — tras Review y Validación `passed`.
