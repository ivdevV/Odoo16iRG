# Cierre de expediente al autocerrar la libreta

## Problema

Cuando una libreta de calificaciones se cierra sola, académica no recibe aviso y la fecha de cierre de expediente del alumno sigue vacía. Ese campo, `op.student.file_closing_date`, ya existe y se muestra en la ficha del alumno. Ningún código lo escribe: el autocierre de `irg_gradebook_auto_close` solo pasa la libreta a `done` mediante `state_to_done()`.

## Alcance

Módulo nuevo `irg_gradebook_expediente_close` en `addons-extra/extrairg/`.

Dependencias: `irg_gradebook_auto_close`, `isep_student_filter`, `mail`.

Incluido:

- Al terminar un autocierre que deja la libreta en `done`, escribir la fecha de hoy en `op.student.file_closing_date` si ese campo está vacío.
- En ese mismo caso, enviar un correo a `academica@institutoraimongaja.com` notificando el cierre de expediente, con alumno, curso, número de admisión, nombre de la libreta y la fecha guardada.

Fuera de alcance:

- Cerrar la libreta a mano con Finalizar. Ese camino no escribe la fecha ni envía correo.
- Rellenar fechas de libretas que ya estaban en `done` antes de instalar el módulo.
- Borrar o cambiar una fecha ya guardada, también si la libreta se reabre y el autocierre la vuelve a cerrar.
- Generar diploma, certificado de notas o carta de disertación, y adjuntarlos al correo.
- Corregir `isep_openeducat_reports`, que busca una libreta en estado `closed`. Los estados reales son `draft`, `in_progress` y `done`.
- Hacer configurable el destinatario.

## Disparo

El módulo hereda `_irg_try_auto_close()` en `app.gradebook.student`. No hereda `state_to_done()`.

Antes de llamar a `super()`:

- Se queda con las libretas del recordset que están en `in_progress`, tienen `student_id` y cuyo alumno tiene `file_closing_date` vacío.

Después de `super()`:

- Recorre esas candidatas en el orden del recordset.
- Si la libreta no quedó en `done`, pasa a la siguiente.
- Si el alumno ya tiene `file_closing_date`, pasa a la siguiente. Así, dos libretas del mismo alumno cerradas en la misma llamada producen una sola fecha y un solo correo: los de la primera que sí quedó en `done`.
- Si sigue vacía, escribe `fields.Date.context_today(gradebook)` en el alumno y envía el aviso de esa libreta.

La escritura de la fecha y el envío usan `sudo()`. Quien guarda la última nota y dispara el autocierre puede no tener permiso de escritura sobre el alumno. La evaluación de si la libreta está lista y el cambio a `done` siguen en el entorno del usuario, dentro de `super()`.

Si la escritura de la fecha falla, la transacción entera se deshace, incluido el cierre. El `sudo()` cubre el permiso; un fallo aquí es un defecto, no un aviso omitido.

## Correo

Plantilla `irg_gradebook_expediente_close.mail_template_expediente_close`, modelo `app.gradebook.student`, con `noupdate="1"`. Un administrador puede ajustar el texto en la plantilla. El código fuerza el destinatario en cada envío, así que un cambio de la plantilla no redirige el aviso.

- `email_to`: `academica@institutoraimongaja.com`, pasado en `email_values`.
- `email_from`: `Instituto Raimon Gaja <academica@institutoraimongaja.com>`.
- Asunto: `CIERRE DE EXPEDIENTE: <alumno> — <número de admisión> — <curso>`. El alumno es `student_id.display_name` y el curso es `course_id.display_name`. Si el número de admisión está vacío, el aviso sale igual, con ese hueco vacío.
- Cuerpo: el texto de abajo. Incluye el correo del alumno (`partner_id.email`) porque académica necesita contactarle. Si no tiene correo, la celda queda vacía.
- Fecha en el cuerpo: `format_date` con `dd/MM/yyyy`. El asunto usa marcadores `{{ }}`. El cuerpo va en QWeb (`t-out`), porque en Odoo 16 el campo `body_html` se renderiza con ese motor y no evalúa `{{ }}`.
- Sin adjuntos y sin pedir la generación de un diploma. El mensaje solo notifica el cierre.

Texto que verá académica:

> **CIERRE DE EXPEDIENTE**
>
> La libreta de calificaciones ha quedado finalizada y se ha registrado la fecha de cierre de expediente.
>
> | | |
> | --- | --- |
> | Alumno | nombre del alumno |
> | Correo del alumno | email del contacto |
> | Curso | nombre del curso |
> | Admisión | número de admisión |
> | Libreta | nombre de la libreta |
> | Fecha de cierre de expediente | dd/MM/yyyy |

El envío es `send_mail(gradebook.id, force_send=True, raise_exception=True)`. `app.gradebook.student` ya hereda `mail.thread`, así que el mensaje queda en el historial de esa libreta. `auto_delete` es falso.

La fecha se escribe antes del envío. El envío va dentro de `self.env.cr.savepoint()`. Si `send_mail` lanza cualquier excepción, incluida una que deja la transacción de PostgreSQL abortada, el savepoint se deshace, se registra el error en el log con el id de la libreta y no se relanza. La libreta sigue en `done` y la fecha se conserva. No hay reintento propio: el aviso solo sale cuando la fecha pasa de vacía a rellena, y ese paso ya ocurrió.

## Estructura

```text
addons-extra/extrairg/irg_gradebook_expediente_close/
  __init__.py
  __manifest__.py
  models/__init__.py
  models/app_gradebook_student.py
  data/mail_template.xml
  tests/__init__.py
  tests/test_expediente_close.py
```

Versión del manifiesto: `16.0.1.0.0`. Licencia `LGPL-3`. No hay modelo nuevo ni `ir.model.access.csv`.

## Pruebas

Suite en el módulo, `TransactionCase`, etiqueta `post_install` y `-at_install`:

- Libreta lista y alumno sin fecha: al completar la última nota, `_irg_try_auto_close()` deja la libreta en `done`, escribe la fecha de hoy y crea un `mail.mail` a `academica@institutoraimongaja.com` ligado a esa libreta, con alumno, correo, curso, número de admisión, libreta y fecha `dd/MM/yyyy`. Esa prueba intercepta la conexión SMTP: comprueba el mensaje creado y no necesita un buzón real.
- Alumno que ya tiene fecha: el autocierre no cambia la fecha y no crea correo.
- `state_to_done()` directo sobre una libreta lista: la libreta pasa a `done`, la fecha sigue vacía y no hay correo.
- `send_mail` lanza una excepción: la libreta queda en `done`, la fecha queda escrita y la excepción no sale de `_irg_try_auto_close()`.
- Dos libretas del mismo alumno, ambas listas, en una sola llamada: una fecha y un solo correo, el de la primera del recordset que quedó en `done`.

## Validación prevista

El diff no toca vistas ni QWeb bajo `views/`, `templates/` o `report/`, ni assets, portal, website, controladores HTTP ni plantillas de diploma. La plantilla vive en `data/mail_template.xml`. El check `e2e_testsprite` se registra `skipped` con esa justificación de alcance.

## Clasificación de entrada

Jev, sobre la petición original, devolvió clase efectiva `full` con vínculo activo y sin aviso de seguridad:

```json
{"status": "ok", "skipped_reason": null, "model": "jev-1.13.0", "mission_class": "full", "mission_class_confidence": 1.0, "mission_class_binding": true, "exceeds_simple_limits": true, "exceeds_simple_noul": 0.91, "needs_security_advisor": false, "security_noul": 0.11, "security_keyword_hit": false, "effective_class": "full", "effective_class_binding": true}
```
