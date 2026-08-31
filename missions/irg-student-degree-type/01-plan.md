# Plan de misión: irg-student-degree-type

## Fuente y alcance

- Fuente: petición de ficha de alumno, campo «Tipo de titulación» bajo
  Estado de pago, estilo etiqueta de la captura CRM.
- Knowledge consultada:
  - `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`
  - `.agents/knowledge/odoo_development_modding/artifacts/irg_student_payment_status.md`
  - `.agents/workflows/odoo16_codebase_knowledge.md`
- Patrón de referencia: `irg_op_course_modality` (catálogo Many2many +
  tags) y `irg_student_birth_citizenship` (xpath en ficha de alumno).
- Objetivo: crear `addons-extra/extrairg/irg_student_degree_type` sin
  modificar módulos existentes.
- Rama base: `Dev_iRG` (`35b2552ae`). Worktree:
  `.worktrees/irg-student-degree-type`, rama `feat/irg-student-degree-type`.

## Decisiones cerradas

- Many2many (no Selection ni Many2one) para reproducir el widget de
  etiquetas con color y aspa de borrado.
- Posición: `emergency_contact` `position="after"` en
  `openeducat_core.view_op_student_form`. En la ficha real, Estado de pago
  se inserta después de ese campo (Studio o vista local); al aplicar
  después nuestra herencia de prioridad por defecto, la etiqueta queda
  debajo de Estado de pago cuando ese campo ya está en la columna.
- Dependencia única: `openeducat_core`. No se depende de
  `irg_student_payment_status` para no inflar el grafo de instalación.
- Sin semilla de tipos: se crean desde el widget.
- E2E TestSprite obligatorio: el diff toca `views/`.

## Tier y capacidad

- Misión completa, tier `standard`: módulo nuevo acotado, un modelo de
  catálogo, un campo, vistas y tests. El conteo de ficheros incluye
  boilerplate Odoo, no lógica cross-module.
- Capacidad: implementación y pruebas sólidas.
- Security Advisor: no aplica (no cambia autenticación, concurrencia,
  migraciones históricas, secretos ni despliegue).

## Fases y propietarios

1. **Plan — orquestador**: este documento.
2. **Implementación/TDD — codificador**: tests RED, implementación mínima,
   GREEN.
3. **Review — revisor independiente**.
4. **Validación — validador independiente** con
   `docker-compose.local.yml` + overlay del worktree.
5. **E2E — e2e-tester** tras el resto de checks en verde.
6. **Documentación**.
7. **Publicación**: no commit, push ni PR sin autorización explícita.

## Criterios de aceptación

Ver `00-spec.md`.

## Riesgos y pruebas

- **XPath**: `emergency_contact` existe en la vista canónica; test de
  `get_view` comprueba orden en el arch combinado.
- **Permisos**: usuarios internos leen el catálogo; back-office crea y
  escribe; unlink solo admin back-office.
- **No colisión** con `titulacion` / `x_studio_titulacion` /
  `study_type_id`.

## Disparo E2E

Obligatorio: vistas XML de formulario de `op.student`.

## Comandos previstos

```bash
docker compose -f docker-compose.local.yml \
  -f missions/irg-student-degree-type/docker-compose.worktree.yml \
  run --rm --no-deps odoo_local odoo -c /etc/odoo/odoo.conf \
  -d irg_sdt_test -i irg_student_degree_type --test-enable \
  --test-tags /irg_student_degree_type --without-demo=all \
  --max-cron-threads=0 --stop-after-init --log-level=test
```
