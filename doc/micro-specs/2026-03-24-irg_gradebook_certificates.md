# Micro-spec: irg_gradebook_certificates
**Fecha:** 2026-03-24  
**Módulo:** `irg_gradebook_certificates`  
**Ruta:** `addons-extra/extrairg/irg_gradebook_certificates/`

---

## 1. Título corto
Solicitud y generación de Certificados de Notas — backend interno y portal con pago.

## 2. Resumen objetivo
Permitir a docentes/admin generar certificados de notas al instante desde el backend (wizard → PDF inmediato), y a alumnos solicitarlos y pagarlos vía portal de Odoo; el certificado digital se entrega automáticamente tras el pago y el físico pasa a cola de gestión.

## 3. Motivo / justificación
El modelo `app.gradebook.student` ya contiene todos los datos necesarios (asignaturas, notas, admisión, alumno). No se toca el core — se usa `_inherit` y QWeb propio. La funcionalidad es nueva y no existe en ningún módulo nativo ni en `addons_uisep`.

## 4. Alcance exacto
- Modelo nuevo: `irg.certificate.request`
- Herencia: `app.gradebook.student` (botón + stat button)
- Herencia: `sale.order` (campo + hook post-pago)
- Wizard transient: `irg.certificate.wizard`
- Reporte QWeb PDF: certificate_templates.xml
- Portal: controller + templates en `/campus/certificates`
- 6 productos de servicio (precio fijo)
- 3 plantillas de email
- Menú backend bajo "Calificaciones"

## 5. Diseño técnico

### Tipos de certificado
| Tipo | Precio base | Envío aplicable |
|------|------------|-----------------|
| digital | 30 € | No |
| physical | 40 € | Sí |
| custom | 40 € | No |
| physical_apostilled | 80 € | Sí |

### Envío (solo físico / apostillado)
| Tipo | Precio |
|------|--------|
| national | 20 € |
| international | 60 € |

### Estados
`draft → pending_payment → paid → in_process → sent → done` | `cancelled`

### Flujo backend (origen: internal)
`app.gradebook.student` form → botón "Generar Certificado" → `irg.certificate.wizard` → PDF generado y descargado → `irg.certificate.request` creado en `done`.

### Flujo portal (origen: portal)
`/campus/certificates/new` → POST → crea `irg.certificate.request (pending_payment)` + `sale.order` → redirect `/shop/cart` → pago → `sale.order.action_confirm()` hook → si digital: genera PDF + `done`; si físico: `paid` → cola admin.

### XPaths en app.gradebook.student form
```
//button[@name='state_to_done']  → position=before (botón Generar Certificado)
//div[hasclass('oe_title')]      → position=before (div.oe_button_box stat button)
```

## 6. Dependencias
```python
['isep_gradebook', 'website_sale', 'sale', 'portal', 'mail', 'website']
```

## 7. Backwards-compatibility / migración
- Sin cambios en modelos existentes.
- `sale.order` solo añade campo Many2one `certificate_request_id` (nullable, no breaking).
- Los productos se crean con `noupdate="1"`.

## 8. Casos de prueba / criterios de aceptación
1. Admin abre libreta en `done` → pulsa "Generar Certificado" → wizard → PDF descargado.
2. Alumno portal → `/campus/certificates/new` → elige Digital → payment → estado auto `done` + attachment.
3. Alumno portal → elige Físico Nacional → tras pago → estado `paid` en backend → admin procesa → `in_process` → `sent` con tracking → alumno recibe email.
4. Alumno portal no puede ver certificados de otro alumno (record rule).
5. Físico sin tipo de envío → ValidationError.

## 9. Rollback
```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf -d <db> \
  --uninstall-modules irg_gradebook_certificates --stop-after-init --db_host=pgodoo_latest
```
Eliminar carpeta `addons-extra/extrairg/irg_gradebook_certificates/`.

## 10. Estimación y responsable
- Estimación: 3–4 jornadas
- Responsable: equipo iRG
