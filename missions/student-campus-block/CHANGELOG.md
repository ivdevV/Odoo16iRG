# Changelog — student-campus-block

## 16.0.1.0.0 — 2026-07-14

### Añadido

- Nuevo módulo aislado `irg_student_campus_block`, dependiente únicamente de `openeducat_core`.
- Campo computado no almacenado `op.student.irg_campus_blocked`, derivado del estado real de `user_id.active`.
- Acciones explícitas e idempotentes para bloquear y desbloquear el acceso autenticado del usuario portal vinculado.
- Botones mutuamente excluyentes y con confirmación en el formulario de estudiante.
- Ribbon rojo «Campus bloqueado», coordinado con el ribbon «Archived» de OpenEduCat para evitar solapamientos.
- Registro en chatter del operador real, usuario objetivo y resultado cuando existe un cambio efectivo.
- Suite de 11 pruebas Odoo para comportamiento, permisos, idempotencia, chatter, vista y cruces de rematrícula.

### Seguridad

- Acciones disponibles únicamente para `openeducat_core.group_op_back_office_admin`, tanto en vista como en servidor.
- Rechazo de usuarios internos, públicos o sin grupo portal antes de elevar permisos.
- Uso de `sudo()` limitado a `res.users.write({'active': ...})`; el chatter conserva la autoría del operador real.
- Sustitución del toggle ambiguo inicial por dos acciones explícitas para resistir peticiones obsoletas o repetidas.

### Validación

- Upgrade e instalación en Odoo 16: 11/11 métodos de test, 0 fallos y 0 errores.
- Verificación HTTP/JSON-RPC real de denegación a faculty, bloqueo, invalidación del acceso en la siguiente petición y restauración tras desbloqueo.
- Compilación Python, Ruff, parseo XML, carga de vista, alcance de `sudo()` y tabla de visibilidad de ribbons validados.

### Limitaciones conocidas

- El bloqueo afecta al acceso autenticado a Odoo, no a Moodle.
- No se elimina físicamente una sesión de Redis; Odoo rechaza la sesión del usuario inactivo en su siguiente petición.
- Si un usuario archivado se desvincula de `op.student`, el flujo opcional de rematrícula de `irg_sale_manual_confirmation_wizard` no lo encuentra con su búsqueda actual y puede producir `ValidationError` por login duplicado. Es un comportamiento preexistente y queda fuera del alcance de este módulo.
