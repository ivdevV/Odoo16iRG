Title: Hacer editable `birth_date` en op.admission
Date: 2026-04-20
Author: Automated change by Copilot

1. Context
   - El campo `birth_date` en `op.admission` está definido con `states={'done':[('readonly', True)]}` y se vuelve no editable en ciertos estados.

2. Objetivo
   - Eliminar las condiciones que impiden editar la fecha de nacimiento para que siempre sea editable.

3. Alcance
   - Crear un módulo `irg_admission_birthdate_edit` en `addons-extra/extrairg/` que redefina el campo `birth_date` sobre `op.admission`.

4. Diseño
   - Heredar el modelo `op.admission` y volver a declarar `birth_date = fields.Date(..., required=True)` sin la propiedad `states`.

5. Seguridad
   - No se crean nuevos modelos; no son necesarias reglas de acceso adicionales.

6. Migración
   - Instalar/actualizar el módulo para aplicar el cambio.

7. Pruebas
   - Verificar en UI que el campo `Fecha de nacimiento` es editable en todos los estados.

8. Rollback
   - Desinstalar o revertir el módulo para restaurar la definición original.
