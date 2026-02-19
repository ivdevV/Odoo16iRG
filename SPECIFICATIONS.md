# SPECIFICATIONS — Política de desarrollo de módulos extra (Odoo 16)

## Propósito
Todas las modificaciones del comportamiento nativo de Odoo se implementarán mediante **módulos extra** (no tocar el core). Este documento contiene las reglas, plantilla de micro-specs y checklist para garantizar seguridad y calidad.

---

## Reglas obligatorias
- Ubicación obligatoria: `addons-extra/extrairg/`.
- Prefijo obligatorio en el nombre del módulo: `irg_` (ej.: `irg_sale_order_override`).
- Nunca modificar módulos nativos de Odoo.
- Cada cambio debe contar con una micro-spec aprobada antes de implementación.
- Objetivo de versión: **Odoo 16** — seguir la documentación oficial v16.

---

## Estructura mínima de un módulo extra
- `__manifest__.py` (version: `16.0.x.x`) con `depends` explícitos.
- `__init__.py`
- `models/` (si hay lógica Python)
- `views/` (XML con `inherit_id` + `xpath` cuando aplique)
- `security/ir.model.access.csv` (si se añaden modelos o permisos)
- `static/` (assets si aplica)
- `tests/` (pytest)

Ejemplo de ruta válida:
- `addons-extra/extrairg/irg_example_override/`

---

## Plantilla obligatoria de micro-spec (archivo en `doc/micro-specs/`)
Cada micro-spec debe incluir:
1. Título corto
2. Resumen objetivo (1–2 frases)
3. Motivo / justificación (por qué override y por qué no tocar core)
4. Alcance exacto (modelos, vistas, assets, reports)
5. Diseño técnico (clases a heredar, `xpath` previsto, IDs externos usados)
6. Dependencias (`depends` en `__manifest__`)
7. Backwards-compatibility / migración (si aplica)
8. Casos de prueba / criterios de aceptación
9. Rollback plan (comandos para revertir/desinstalar)
10. Estimación y responsable

Formato recomendado: Markdown, ejemplo `doc/micro-specs/2026-02-12-irg_ejemplo.md`.

---

## Buenas prácticas (resumen)
- Usar `_inherit` y `xpath` para vistas; no editar XML core.
- No usar monkey-patching de librerías nativas.
- Evitar SQL directo salvo que esté justificado; documentar y testear.
- Usar `env.ref()` y `ref()` en XML; evitar hardcodes.
- Todas las cadenas deben ser traducibles (`_()`).
- Añadir `ir.model.access.csv` cuando se introducen modelos o cambios de reglas.
- Tests obligatorios para lógica crítica y migraciones.
- Registrar cambios en `README` o changelog del módulo.

---

## Checklist de PR (obligatorio)
- [ ] Micro-spec aprobada y referenciada en el PR.
- [ ] Módulo ubicado en `addons-extra/extrairg` y nombre empieza por `irg_`.
- [ ] `__manifest__` con `version: '16.0.x.x'` y `depends` correctos.
- [ ] No hay cambios en módulos nativos.
- [ ] Tests añadidos y pasan localmente.
- [ ] `ir.model.access.csv` incluido si procede.
- [ ] Documentación y rollback plan presentes.

---

## Seguridad y permisos
- Revisar ACLs y record rules antes de merge.
- Justificar cualquier uso de `sudo()`.
- No exponer endpoints sin validación/CSRF y permisos.

---

## Tests y despliegue
- Unit tests con `pytest` para lógica.
- Tests de integración (instalación del módulo + workflows críticos).
- QA: staging -> monitor logs -> producción.

---

## Referencias
- Odoo 16 Developer: https://www.odoo.com/documentation/16.0/developer.html

---

> Nota: los módulos nuevos deben respetar la convención de nombres y ubicarse en `addons-extra/extrairg/` — esto centraliza código propio y facilita despliegues.
