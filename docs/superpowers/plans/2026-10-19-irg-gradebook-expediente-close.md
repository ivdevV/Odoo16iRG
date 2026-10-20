# Cierre de expediente al autocerrar la libreta — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Al autocerrar una libreta, guardar la fecha de cierre de expediente del alumno si está vacía y avisar a académica con la plantilla de este plan.

**Architecture:** Módulo nuevo que hereda `_irg_try_auto_close()`. Después de `super()`, escribe `file_closing_date` con `sudo()` y envía `mail.template` con el destinatario forzado. `state_to_done()` no se hereda.

**Tech Stack:** Odoo 16, `irg_gradebook_auto_close`, `isep_student_filter`, `mail`.

## Global Constraints

- Módulo `addons-extra/extrairg/irg_gradebook_expediente_close`, versión `16.0.1.0.0`, licencia `LGPL-3`.
- No editar módulos existentes.
- Destinatario forzado: `academica@institutoraimongaja.com`.
- Remitente: `Instituto Raimon Gaja <academica@institutoraimongaja.com>`.
- Fecha: `fields.Date.context_today(gradebook)`, solo si `file_closing_date` está vacía.
- Correo solo cuando esa escritura ocurre.
- `send_mail(..., force_send=True, raise_exception=True)` dentro de `try/except Exception`; el log lleva el id de la libreta; no se relanza.
- Dos libretas del mismo alumno en una llamada: la primera que queda en `done`.
- Sin barrido de históricas y sin commit hasta autorización explícita.

---

### Task 1: Pruebas en rojo

**Files:**
- Create: `addons-extra/extrairg/irg_gradebook_expediente_close/tests/test_expediente_close.py`
- Create: esqueleto instalable sin hook ni plantilla

- [ ] Escribir los cinco casos de la spec y ejecutarlos con el tag `/irg_gradebook_expediente_close`.
- [ ] Esperado: fallan los casos que exigen fecha y correo. El cierre manual, que no debe hacer nada nuevo, puede pasar ya.

### Task 2: Plantilla y hook

**Files:**
- Create: `addons-extra/extrairg/irg_gradebook_expediente_close/data/mail_template.xml`
- Create: `addons-extra/extrairg/irg_gradebook_expediente_close/models/app_gradebook_student.py`

La plantilla es esta:

```xml
<record id="mail_template_expediente_close" model="mail.template">
    <field name="name">Cierre de expediente — Aviso a académica</field>
    <field name="model_id" ref="isep_gradebook.model_app_gradebook_student"/>
    <field name="subject">Cierre de expediente: {{ object.student_id.display_name }} — {{ object.admission_id.application_number or '' }} — {{ object.course_id.display_name }}</field>
    <field name="email_from">Instituto Raimon Gaja &lt;academica@institutoraimongaja.com&gt;</field>
    <field name="email_to">academica@institutoraimongaja.com</field>
    <field name="auto_delete" eval="False"/>
</record>
```

El cuerpo, en una tabla de etiquetas grises, dice: «La libreta de calificaciones ha quedado finalizada y se ha registrado la fecha de cierre de expediente.» Filas: Alumno, Correo del alumno, Curso, Admisión, Libreta, Fecha de cierre de expediente (`format_date` `dd/MM/yyyy`). `noupdate="1"`.

El hook filtra candidatas `in_progress` sin fecha, llama a `super()`, y en las que quedan `done` escribe la fecha con `sudo()` y envía la plantilla. La lectura de «¿ya tiene fecha?» también es `sudo()`, para que la segunda libreta del mismo alumno vea la escritura de la primera.

- [ ] Implementar el mínimo para poner las pruebas en verde.
- [ ] Volver a ejecutar el mismo comando de Odoo. Esperado: 0 failed.

### Task 3: Evidencia

- [ ] Guardar la salida roja y la verde en `missions/irg-gradebook-expediente-close/artifacts/`.
- [ ] Actualizar `execution.md`. Review y validación quedan para después de GREEN.
