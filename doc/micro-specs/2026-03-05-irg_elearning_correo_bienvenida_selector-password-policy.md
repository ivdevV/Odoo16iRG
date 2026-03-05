# Micro-spec: Política de contraseña en correo de bienvenida (rematrícula)

## 1. Título
Condicional de contraseña para correos de bienvenida en rematrícula

## 2. Resumen
Al enviar correo de bienvenida por nueva matrícula de un alumno existente, mostrar contraseña solo si es reutilizable (misma contraseña previa disponible). Si no es posible, no incluir contraseña en el correo.

## 3. Motivo / justificación
Evitar exposición innecesaria de credenciales y cumplir la regla operativa: si ya se envió contraseña antes, reenviar la misma o no enviar contraseña.

## 4. Alcance exacto
- `addons-extra/addons_uisep/irg_elearning_correo_bienvenida_selector/models/op_admission.py`
- `addons-extra/addons_uisep/irg_elearning_correo_bienvenida_selector/data/mail_template_online.xml`

## 5. Diseño técnico
- Nuevo método `_welcome_password_context()` en `op.admission`:
  - Detecta si hubo bienvenida previa enviada (`email_send_ok=True`) para el mismo usuario/email.
  - Obtiene contraseña reutilizable desde `res.users.new_password_user` (si existe el campo).
  - Define contexto:
    - `welcome_show_password` (bool)
    - `welcome_password_value` (str)
- `send_mail()` pasa ese contexto a la plantilla.
- La plantilla online muestra el bloque de contraseña solo si `welcome_show_password` es verdadero.

## 6. Dependencias
Sin cambios de dependencias en manifest.

## 7. Backwards-compatibility / migración
Compatible hacia atrás: si no existe `new_password_user`, el bloque de contraseña se oculta en rematrícula.

## 8. Casos de prueba / criterios de aceptación
1. Primera bienvenida de alumno: se muestra contraseña.
2. Rematrícula con `new_password_user` disponible: se muestra misma contraseña.
3. Rematrícula sin `new_password_user`: no se muestra contraseña.
4. En todos los casos se mantiene usuario/login y enlace al campus.

## 9. Rollback plan
Revertir commit del módulo `irg_elearning_correo_bienvenida_selector` y actualizar módulo.

## 10. Estimación y responsable
- Estimación: 1h
- Responsable: Equipo IRG
