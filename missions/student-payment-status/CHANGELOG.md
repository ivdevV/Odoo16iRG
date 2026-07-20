# Changelog de misión: student-payment-status

## 2026-07-16

- Se creó el módulo aislado `irg_student_payment_status` con estados
  almacenados, métricas live, parámetros robustos, cron diario, chatter,
  actividades y vistas de alumno.
- El Review corrigió la agregación multimoneda para usar
  `amount_residual_signed`, eliminó una segunda búsqueda de facturas y reforzó
  el XPath de los ribbons.
- La acción manual quedó protegida, antes de cualquier ruta con `sudo()`, por
  grupo back-office, ACL de escritura y reglas de registro.
- Las actividades propias se completan con `action_feedback()` al salir de
  moroso; una reincidencia crea un seguimiento nuevo y los reruns permanecen
  idempotentes.
- Validación preliminar: instalación fresca y 15 tests, 0 fallos y 0 errores;
  checks de Python, XML, manifest, seguridad, alcance y cleanup aprobados.
- Validación UI: filtros, agrupación, decoraciones, ribbons, smart button,
  chatter, actividad y facturas vencidas comprobados en navegador.
- Caveats: notificación estándar de `mail.activity`; warnings preexistentes de
  `irg_sale_order_extended`, labels heredados y tag `report` deprecado. Bloqueo
  de campus, reclamaciones por email y cuotas Stripe quedan fuera de alcance.
