# Changelog — irg-tfm-delivery-review-gradebook

## 16.0.1.2.0 — 2026-09-16

### Añadido

- Modelo `irg.tfm.entrega.revision`: una revisión auditada por versión de
  entrega inmutable, con ACL de **Revisor TFM**, sin borrado y con metadatos
  `reviewed_by` / `reviewed_at` calculados en servidor.
- Formulario backend de revisión y acción **Revisar entrega** en el árbol de
  entregas del expediente.
- El alumno dueño ve en el portal el estado publicado y el comentario de cada
  versión; el texto se escapa y no hay rutas de mutación portal.
- Sincronización bidireccional `tesis.model.points_fin` ↔
  `app.gradebook.result.scoring_total` con vínculo `irg_tfm_thesis_id` de
  servidor, resolución exacta por familia Canal TFM y
  `op.subject.slide_channel_id`.
- Guardas de identidad en resultado, línea, libreta, admisión, matrícula y
  expediente (archivos de herencia por modelo, desviación intencionada del
  file map de Task 6).

### Seguridad

- Contexto público, `default_*` y vínculos de cliente no autorizan ni crean el
  enlace TFM. El token interno de diferimiento es un `object()` comparado con
  `is`.
- Autorización del actor antes de `sudo` estrecho. Orden de bloqueo
  matrícula → tesis → libreta → línea → resultados; cada operación pareada en
  un savepoint.
- Nota finita `0` o `1..10`; se rechaza una plantilla de libreta que redondee,
  recorte o transforme la calificación.

### Operación

- Un examen nuevo en la línea TFM exige expediente activo y configuración
  unívoca. Sin eso, la libreta deja de aceptar ese examen hasta activar el
  expediente o corregir Canal TFM / asignatura / línea.
- No se admite escribir a la vez matrícula y convocatoria del expediente, ni
  un lote mixto de resultados TFM y no TFM.

### Validación

- Review independiente (tres pases): C1 e I1–I4 resueltos; menores M1–M12
  abiertos y no bloqueantes.
- Validación independiente `passed`: contratos estáticos, `compileall`, XML y
  `git diff --check`.
- Odoo/PostgreSQL/dos cursores/TestSprite no se ejecutaron: el usuario prohibió
  Docker en este equipo. El alcance de vistas/QWeb/portal sí dispararía E2E
  cuando el runtime esté autorizado.
