# Biblia IRG de Modulos y Automatizaciones (Odoo 16)

Version: 2026-03-23
Ambito: Desarrollo, mantenimiento, hotfix y evolucion de modulos `irg_`.
Audiencia: Desarrolladores y agentes (Copilot/LLM) que trabajan en este repo.

---

## 1. Objetivo de esta guia

Este documento unifica como crear, modificar y operar modulos y automatizaciones en este proyecto, usando la experiencia acumulada en micro-specs, incidentes y fixes reales.

Objetivos concretos:
- Reducir regresiones por cambios de rutas, vistas heredadas y automatizaciones.
- Estandarizar decisiones tecnicas para que dos personas/agentes implementen de forma consistente.
- Acelerar troubleshooting con runbooks listos para usar.
- Mantener cumplimiento estricto de [SPECIFICATIONS.md](../../SPECIFICATIONS.md).

---

## 2. Reglas no negociables (fuente de verdad)

Basado en [SPECIFICATIONS.md](../../SPECIFICATIONS.md):

1. Todo cambio funcional se hace en modulo extra bajo `addons-extra/extrairg/`.
2. El modulo debe empezar por `irg_`.
3. Nunca editar core de Odoo ni modulos nativos para meter fixes directos.
4. Cada cambio debe tener micro-spec en `doc/micro-specs/`.
5. Manifest en version `16.0.x.x` y `depends` explicitos.
6. Se debe entregar changelog corto y claro.
7. Para logica critica: tests obligatorios.
8. Seguridad: revisar ACL/rules y justificar cualquier `sudo()`.
9. Despliegue: push dispara Jenkins, no asumir reinicio manual salvo excepcion operativa.

---

## 3. Mapa operativo del ecosistema IRG

### 3.1 Dominios y modulos principales

- Website/Checkout:
  - `irg_website_checkout_fixes`
  - `irg_website_sale_monthly_price`
  - `irg_website_sale_monthly_default_combo`
  - `irg_checkout_financing_sign_sync`

- Pagos/Suscripciones:
  - `irg_payment_stripe_recurring`
  - `irg_sale_subscription_esp`
  - `irg_subscription_esp_single_invoice`
  - `irg_custom_discount`

- Forum/Web editor hardening:
  - `irg_forum_web_editor_save_guard`
  - `irg_web_editor_fix`
  - `irg_forum_email_notify`
  - `irg_forum_batch_visibility`

- Academico/OpenEduCat/Survey/Quiz:
  - `irg_quiz_auto_scoring`
  - `irg_survey_regrade_attempts`
  - `irg_exam_score_100`
  - `irg_timetable_*`
  - `irg_op_*`

- Operacion/Cron guards:
  - `irg_isep_cron_update_guard`

### 3.2 Donde mirar segun problema

- Cuotas/precio mensual en `/shop`:
  - `addons-extra/extrairg/irg_website_sale_monthly_price/`
  - `addons-extra/extrairg/irg_website_sale_monthly_default_combo/`
  - `addons-extra/extrairg/irg_sale_subscription_esp/`

- Firma + sincronizacion checkout:
  - `addons-extra/extrairg/irg_checkout_financing_sign_sync/`

- Incidencias Stripe recurrente:
  - `addons-extra/extrairg/irg_payment_stripe_recurring/`

- Errores de editor/forum (500 al guardar HTML):
  - `addons-extra/extrairg/irg_forum_web_editor_save_guard/`
  - `addons-extra/extrairg/irg_web_editor_fix/`

- Bloqueos por cron durante updates:
  - `addons-extra/extrairg/irg_isep_cron_update_guard/`

---

## 4. Flujo canonico para crear modulo nuevo

### Paso 1: Abrir micro-spec

Crear archivo en `doc/micro-specs/` con formato fecha + nombre, por ejemplo:
- `doc/micro-specs/2026-03-23-irg_ejemplo.md`

Debe incluir los 10 puntos definidos en [SPECIFICATIONS.md](../../SPECIFICATIONS.md).

### Paso 2: Scaffolding minimo

Estructura esperada:

```text
addons-extra/extrairg/irg_modulo_nuevo/
  __init__.py
  __manifest__.py
  models/
  views/
  security/
  static/
  tests/
```

Notas:
- No crear carpetas innecesarias si no se usan.
- Si hay modelo nuevo, incluir `security/ir.model.access.csv` desde el inicio.

### Paso 3: Implementar por herencia (no core)

- Python: `_inherit` + `super()`.
- XML: `inherit_id` + `xpath` robusto.
- JS/OWL: patch acotado y defensivo.

### Paso 4: Tests minimos

- Unit test de logica critica.
- Al menos un test de no-regresion del bug que motivó el cambio.

### Paso 5: Changelog + validacion

- Changelog corto.
- Revisar `depends`, version y rutas.

---

## 5. Flujo canonico para modificar modulo existente

### 5.1 Analisis previo obligatorio

Antes de tocar codigo:
1. Identificar modulo owner del feature.
2. Confirmar orden de herencia y prioridades (XML/manifest/dependencies).
3. Revisar si existe otro override del mismo metodo/template.
4. Verificar impacto colateral en checkout, cron y pricing.

### 5.2 Regla de compatibilidad

- Mantener API publica y firmas salvo necesidad fuerte.
- Cambios pequeños y localizados.
- Fallbacks explicitos para datos incompletos.

### 5.3 Regla de pruebas en fixes

Cada fix debe tener:
- Caso que falla antes.
- Caso que pasa despues.
- Escenario de fallback.

---

## 6. Automatizaciones: patron estandar

### 6.1 Tipos de automatizacion en este repo

1. Cron jobs (`ir.cron`)
2. Hooks de modelo (`create/write/action_*`)
3. Webhooks/callbacks de pago
4. Scripts de import/export
5. JS frontend que altera defaults/combinaciones

### 6.2 Reglas de diseno para automatizaciones

- Idempotencia: correr 2 veces no debe duplicar ni romper.
- Trazabilidad: log suficiente para auditar.
- Guardas: cortar ejecucion en condiciones de riesgo.
- Timeouts y volumen: no bloquear workers con loops pesados sin paginacion.
- Rollback funcional: tener modo desactivar/desinstalar/revertir.

### 6.3 Cron safe pattern

Aplicar patron de `irg_isep_cron_update_guard`:
- Antes de ejecutar logica pesada, verificar si hay modulos en `to install`, `to upgrade`, `to remove`.
- Si si: early return + log informativo.

---

## 7. Fragilidad de paths y como blindarse

La mayor fuente de regresion en este repo es fragilidad de rutas/selectores/herencias.

### 7.1 XML/QWeb/XPath

Riesgos:
- XPath demasiado especifico (rompe con cambios menores upstream).
- Herencias en conflicto por prioridad.

Mitigaciones:
- Preferir anclas semanticas (`hasclass`, ids estables, bloques nombrados).
- Evitar xpaths largos por posicion.
- Documentar `inherit_id` y por que ese anchor.
- Validar colision con otros modulos que heredan la misma vista.

### 7.2 Python override chain

Riesgos:
- Multiples modulos override del mismo metodo.
- Orden MRO inesperado por `depends`.

Mitigaciones:
- Revisar todos los `_inherit` y `super()` de ese metodo antes de cambiar.
- Añadir comentario tecnico cuando haya fallback sensible.
- Evitar devolver estructuras distintas a las esperadas por upstream.

### 7.3 JS/frontend assets

Riesgos:
- Load order de assets.
- Selectores CSS/DOM fragiles.

Mitigaciones:
- Parches defensivos (null checks y feature detection).
- Clases de enganche propias (`irg-*`) cuando sea posible.
- Probar en `/shop`, `/shop/cart`, `/shop/address`, `/shop/payment` segun alcance.

### 7.4 Infra path/entorno

Riesgos:
- Comandos DB en host cuando binarios viven en contenedor.
- Usuario/rol DB incorrecto.

Mitigaciones:
- Operar `pg_dump/psql` dentro de contenedor PostgreSQL.
- Verificar rol real (`odoo` u otro) antes de dump/query.
- Confirmar tamano real del backup y no solo existencia de archivo.

---

## 8. Catalogo de fallos recurrentes y solucion estandar

### Caso A: Cuotas inconsistentes entre ficha y buscador

Sintoma:
- En buscador de `/shop` una cuota aparece distinta o como precio total.

Patron de solucion:
1. Revisar `_search_render_results_prices` y origen de `combination_info`.
2. Priorizar `min_installment_price/min_installment_months` para busqueda cuando la combinacion default sea contado.
3. Mantener fallback al comportamiento anterior.

Referencia:
- `irg_website_sale_monthly_price`
- `irg_website_sale_monthly_default_combo`

### Caso B: Placeholders `{}` en checkout

Sintoma:
- Textos de cuotas muestran `{}` literal.

Patron de solucion:
1. Heredar template correcto de cart summary.
2. Reemplazar placeholders por `t-esc` con variable real.
3. Validar flujo anonimo y logueado.

Referencia:
- `irg_website_checkout_fixes`
- `irg_sale_subscription_esp`

### Caso C: 500 al guardar contenido de forum/editor

Sintoma:
- Error interno al guardar post o contenido HTML.

Patron de solucion:
1. Sanitizar HTML en create/write.
2. Fallback seguro para contenido invalido.
3. Parchar JS editor en modo defensivo si el fallo es client-side.

Referencia:
- `irg_forum_web_editor_save_guard`
- `irg_web_editor_fix`

### Caso D: Perdida de +521 en telefonos MX

Sintoma:
- Odoo normaliza y elimina el `1` en `+521...`.

Patron de solucion:
1. Override controlado de `_phone_format` en `res.partner`.
2. Evitar reformateo UI agresivo cuando corresponda.
3. Testear numeros no MX para no romper global.

Referencia:
- `irg_phone_prefix_fix`

### Caso E: Update bloqueado por procesos concurrentes

Sintoma:
- Upgrade/instalacion se bloquea o tarda por cron en paralelo.

Patron de solucion:
1. Aplicar guard antes de cron pesado.
2. Exponer indicador visual de proceso bloqueante si aplica.
3. Reintentar update en ventana limpia.

Referencia:
- `irg_isep_cron_update_guard`
- `irg_blocking_process_topbar_indicator`

---

## 9. Testing matrix por tipo de cambio

### 9.1 Cambios en pricing/checkout

Minimo:
- Caso anonimo + logueado.
- `/shop` listado, ficha, carrito, address, payment.
- Confirmar consistencia de cuota y total.

### 9.2 Cambios en automatizacion/cron

Minimo:
- Idempotencia (segunda corrida).
- Ejecucion con y sin condicion de guarda.
- Verificar logs y estado final.

### 9.3 Cambios en formularios/editor

Minimo:
- Guardado de contenido valido.
- Guardado de contenido malformado (no 500).
- Render posterior correcto.

### 9.4 Cambios de datos/importacion

Minimo:
- Preview antes de importar.
- Backup comprobado.
- Conteo antes/despues.
- Rollback claro.

---

## 10. Runbooks operativos

### Runbook 1: Diagnostico rapido de 500 en Odoo Docker

1. Ver estado contenedores.
2. Revisar logs recientes de Odoo y Postgres.
3. Verificar espacio en disco host/contenedores.
4. Buscar `Traceback|ERROR|Exception`.
5. Si procede, reiniciar servicio segun politica operativa.

### Runbook 2: Backup DB seguro en Docker

1. Ejecutar dump dentro del contenedor PostgreSQL.
2. Usar rol DB correcto (confirmar antes).
3. Copiar al host y validar tamano > 0.
4. Guardar nombre con fecha/hora.

### Runbook 3: Importacion segura de excepciones/precios

1. Backup validado.
2. Generar preview de mapeos.
3. Importar en staging.
4. Verificar muestra en UI y en DB.
5. Solo entonces promover a produccion.

### Runbook 4: Hotfix web pricing

1. Localizar cadena de overrides (`_get_combination_info`, `_search_render_results_prices`, templates).
2. Aplicar fix minimo con fallback.
3. Testear ficha/listado/buscador.
4. Documentar micro-spec + changelog.

---

## 11. Plantillas reutilizables

### 11.1 Plantilla de micro-spec (resumen rapido)

1. Titulo corto
2. Resumen objetivo
3. Motivo
4. Alcance exacto
5. Diseno tecnico
6. Dependencias
7. Compatibilidad/migracion
8. Casos de prueba
9. Rollback
10. Estimacion y responsable

### 11.2 Plantilla de changelog corto

- Fecha
- Modulo
- Problema observado
- Solucion aplicada
- Impacto
- Riesgo residual
- Validaciones realizadas

### 11.3 Plantilla de PR checklist

- [ ] Micro-spec creada/aprobada
- [ ] No hay cambios en core
- [ ] `depends` y version correctos
- [ ] Tests agregados/ejecutados
- [ ] ACL incluidas (si aplica)
- [ ] Rollback definido
- [ ] Changelog incluido

---

## 12. Comandos base de referencia

### Actualizar modulo en Odoo

```bash
python3 odoo-bin -c /etc/odoo/odoo.conf -d <DB> -u <modulo_irg> --stop-after-init
```

### Actualizar multiples modulos

```bash
python3 odoo-bin -c /etc/odoo/odoo.conf -d <DB> -u modulo_a,modulo_b --stop-after-init
```

### Commit convencional

```bash
git add -A
git commit -m "irg: descripcion corta del fix"
git push
```

Nota: en este repo, el push dispara pipeline Jenkins de despliegue.

---

## 13. Politica de mantenimiento de esta guia

- Owner sugerido: equipo IRG (dev lead + 1 backup).
- Actualizacion obligatoria cuando:
  1. se crea un nuevo patron de automatizacion,
  2. aparece un incidente critico nuevo,
  3. cambia una regla de SPECIFICATIONS.
- Frecuencia recomendada: al cierre de cada bloque de cambios relevante.

---

## 14. Referencias cruzadas (micro-specs clave)

- [2026-02-12-irg-stripe-recurring-hardening.md](2026-02-12-irg-stripe-recurring-hardening.md)
- [2026-02-12-checklist-staging-stripe-checkout-sign.md](2026-02-12-checklist-staging-stripe-checkout-sign.md)
- [2026-03-13-irg_website_sale_monthly_default_combo.md](2026-03-13-irg_website_sale_monthly_default_combo.md)
- [2026-03-16-irg_website_checkout_fixes.md](2026-03-16-irg_website_checkout_fixes.md)
- [2026-03-20-irg_phone_prefix_fix_mx521.md](2026-03-20-irg_phone_prefix_fix_mx521.md)
- [2026-03-03-irg_isep_cron_update_guard.md](2026-03-03-irg_isep_cron_update_guard.md)
- [2026-03-13-irg-forum-web-editor-save-guard.md](2026-03-13-irg-forum-web-editor-save-guard.md)
- [2026-03-13-irg-web-editor-fix.md](2026-03-13-irg-web-editor-fix.md)

---

## 15. Cierre

Si una solucion propuesta no puede explicarse con este marco (reglas, ownership, pruebas, rollback), no esta lista para desplegarse.

Primero consistencia y trazabilidad; despues velocidad.
