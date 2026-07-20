# Gradebook Template Precedence Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Corregir el autocierre para que una línea nunca añada categorías ausentes en el template principal de la libreta, conservando las excepciones que eliminan requisitos por línea.

**Architecture:** El módulo `irg_gradebook_auto_close` extenderá por `_inherit` el compute `app.gradebook.subject.compute_data_show()`. Después de la lógica base calculará los cuatro `show_*` como intersección entre los tipos del template principal y los del template de línea; si no existe template de línea, heredará el principal.

**Tech Stack:** Odoo 16 ORM, Python, `TransactionCase`, Docker Compose local y PostgreSQL.

## Global Constraints

- No modificar `isep_gradebook` ni ningún módulo existente fuera de `irg_gradebook_auto_close`.
- Seguir TDD: prueba RED observada antes de editar producción.
- Mantener `_irg_is_ready_to_close()` y `state_to_done()` como ruta de cierre.
- Refrescar los `show_*` almacenados únicamente para la libreta tocada antes del check;
  no realizar barrido global durante instalación/upgrade.
- No hacer commit ni push remoto sin autorización explícita posterior.
- Validar mediante `docker-compose.local.yml` contra `test_irg_db`.

---

## Clasificación y routing

Tier: `standard`.

Justificación: afecta tres archivos del addon y pruebas acotadas; corrige una regla de negocio reproducida sin autenticación, concurrencia, migraciones, secretos ni borrado de datos. No se activa Security Advisor.

- Plan: agente principal.
- Implementación: subagente codificador Odoo 16, tier `standard`.
- Validación: subagente testeador independiente, tier `standard`.
- Anti-patrones/calidad: revisión independiente después de GREEN.
- Documentación: subagente documentador después de `verification.json: passed`.

### Task 1: Regresión de precedencia efectiva

**Files:**
- Modify: `addons-extra/extrairg/irg_gradebook_auto_close/tests/test_auto_close.py`

**Interfaces:**
- Consumes: `_create_gradebook_template()`, `_create_student_gradebook()` y `_add_result()` existentes.
- Produces: pruebas de precedencia que usan registros Odoo reales.

- [ ] **Step 1: Escribir la prueba RED del caso Dev**

Crear una libreta cuyo template principal contenga solo `exam`, asignar a su `op.subject` un template con `exam` y `assignment`, crear únicamente un examen positivo y afirmar:

```python
self.assertFalse(line.show_assignment)
self.assertEqual(gradebook.state, "done")
```

- [ ] **Step 2: Ejecutar RED**

Run:

```bash
docker compose -f docker-compose.local.yml run --rm odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -u irg_gradebook_auto_close --test-enable \
  --test-tags /irg_gradebook_auto_close \
  --stop-after-init --log-level=test
```

Expected: exactamente la nueva prueba falla porque `show_assignment` es `True` o la libreta permanece `in_progress`; los tests anteriores no deben introducir errores de infraestructura.

- [ ] **Step 3: Añadir las regresiones complementarias**

Añadir pruebas reales para:

```text
principal Asignación+Examen AND línea Solo Examen -> no exige asignación
principal Asignación+Examen AND línea sin template -> exige asignación
```

La segunda debe permanecer `in_progress` hasta crear la asignación y cerrar después.

### Task 2: Intersección de categorías

**Files:**
- Create: `addons-extra/extrairg/irg_gradebook_auto_close/models/app_gradebook_subject.py`
- Modify: `addons-extra/extrairg/irg_gradebook_auto_close/models/__init__.py`

**Interfaces:**
- Consumes: `gradebook_student_id.gradebook_id`, `gradebook_id` y `gradebook_template_ids.type`.
- Produces: override `compute_data_show()` compatible con los campos compute existentes.

- [ ] **Step 1: Importar la extensión**

Añadir `from . import app_gradebook_subject` a `models/__init__.py`.

- [ ] **Step 2: Implementar la lógica mínima**

Crear el override que llama primero a `super().compute_data_show()` y aplica:

```python
student_types = set(student_template.gradebook_template_ids.mapped("type"))
line_types = (
    set(line_template.gradebook_template_ids.mapped("type"))
    if line_template
    else student_types
)
effective_types = student_types & line_types
```

Después asignar `show_assignment`, `show_exam`, `show_interaction` y `show_foro` según pertenencia a `effective_types`. Si no hay template principal, conservar el resultado base.

- [ ] **Step 3: Ejecutar GREEN objetivo y completo**

Ejecutar el mismo comando de Task 1. Expected: todas las pruebas anteriores más las nuevas pasan, con `0 failed`, `0 errors` y exit `0`.

- [ ] **Step 4: Comprobar sintaxis y alcance**

Compilar todos los Python del addon dentro del compose, comprobar imports, manifest y ausencia de cambios en `addons-extra/addons_uisep/isep_gradebook`.

### Task 3: Validación independiente y evidencia

**Files:**
- Create: `missions/fix-gradebook-template-precedence/verification.json`
- Create: `missions/fix-gradebook-template-precedence/artifacts/`
- Update: `missions/fix-gradebook-template-precedence/execution.log`
- Create: `missions/fix-gradebook-template-precedence/diff.patch`

**Interfaces:**
- Consumes: addon y tests finales.
- Produces: contrato de verificación auditable.

- [ ] **Step 1: Repetir upgrade y suite en un agente nuevo**

Expected: suite completa verde y caso exacto `AD003762` demostrado con datos equivalentes.

- [ ] **Step 1b: Probar un valor almacenado obsoleto**

Simular `show_assignment=True` persistido en una línea cuyo template efectivo es
`Solo Examen`, escribir la nota final y afirmar que el trigger recalcula la línea y
cierra la libreta sin barrer otras libretas.

- [ ] **Step 2: Revisar anti-patrones y calidad**

Verificar que la línea solo elimina requisitos, que no hay cierre directo, monkey-patch, modificación de `isep_gradebook`, contexto global ni cambio de datos.

- [ ] **Step 3: Emitir `verification.json`**

`status` solo será `passed` si todos los checks funcionales, sintácticos y de alcance pasan.

### Task 4: Documentación

**Files:**
- Modify: `addons-extra/extrairg/irg_gradebook_auto_close/README.md`
- Modify: `.agents/knowledge/odoo_development_modding/artifacts/irg_gradebook_auto_close.md`
- Create: `missions/fix-gradebook-template-precedence/CHANGELOG.md`

- [ ] **Step 1: Documentar la precedencia efectiva**

Explicar la intersección de templates, el caso Dev reproducido, los casos de uso y la limitación de no hacer barrido retroactivo.

- [ ] **Step 2: Regenerar el parche de misión**

Incluir solo addon, micro-spec y artefactos de esta misión; excluir cambios locales ajenos, `verification.json`, `artifacts/` y el propio parche cuando sea necesario para evitar autorreferencia.

## Definición de terminado

- El caso `Solo Examen` principal + línea interna `Asignación/Examen` cierra con examen/final positivos.
- Una línea `Solo Examen` continúa eliminando asignación en una libreta mixta.
- Una línea sin override hereda el template principal.
- Suite completa y revisiones pasan.
- `verification.json` tiene `status: passed`.
- No se ha hecho push remoto.
