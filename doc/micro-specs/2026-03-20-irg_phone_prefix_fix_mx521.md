# 2026-03-20 — irg_phone_prefix_fix (MX +521)

## 1. Título corto
Preservación de prefijo +521 en teléfonos de contactos y desactivación de reformateo UI en formulario de partner.

## 2. Resumen objetivo
Evitar que Odoo elimine automáticamente el dígito "1" en números mexicanos con formato +521.
Asegurar consistencia visual y de guardado en los campos phone/mobile.

## 3. Motivo / justificación
Odoo 16 usa phone_validation (libphonenumber), que normaliza +521XXXXXXXXXX a +52XXXXXXXXXX sin error.
Se requiere override en módulo extra para preservar la entrada del usuario sin modificar core.

## 4. Alcance exacto
- Modelos: override de res.partner._phone_format y onchange de phone/mobile.
- Vistas: reemplazo de widget phone a widget char en formulario de contacto.
- Assets: no aplica.
- Reports: no aplica.

## 5. Diseño técnico
- Módulo: irg_phone_prefix_fix
- Clase heredada: res.partner
- Método clave: _phone_format(number, country=None, company=None, force_format='E164')
- Helpers:
  - _irg_strip_phone
  - _irg_user_typed_mx1
- Vista heredada:
  - inherit_id: base.view_partner_form
  - xpath:
    - //field[@name='phone'][@widget='phone']
    - //field[@name='mobile'][@widget='phone']
- IDs externos:
  - view_partner_form_irg_phone_widget

## 6. Dependencias
- base
- phone_validation

## 7. Backwards-compatibility / migración
- Sin migración de datos obligatoria.
- Los valores existentes permanecen intactos.
- Para aplicar lógica y vista en una base ya operativa: actualizar módulo con -u irg_phone_prefix_fix.

## 8. Casos de prueba / criterios de aceptación
1. Al capturar +52 1 55 1234 5678, el valor guardado conserva el "1".
2. Al reabrir el contacto, phone/mobile muestran el mismo valor (sin pérdida del dígito).
3. Campos phone/mobile no se reformatean al hacer foco/blur en formulario.
4. No hay regressions para números no mexicanos.
5. El módulo instala y actualiza sin errores de carga.

## 9. Rollback plan
1. Revertir commit asociado en rama Dev_iRG.
2. Actualizar base sin el override (o desinstalar módulo si procede):
   - odoo -u irg_phone_prefix_fix -d <DB> --stop-after-init
3. Limpiar caché de assets y reiniciar servicios según pipeline.

## 10. Estimación y responsable
- Estimación: 2-4 horas (análisis, fix, validación funcional).
- Responsable: Copilot + equipo IRG (validación funcional en beta).
