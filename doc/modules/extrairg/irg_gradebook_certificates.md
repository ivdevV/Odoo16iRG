# irg_gradebook_certificates

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP / iRG
**Depende de:** `isep_gradebook`, `website_sale`, `sale`, `portal`, `mail`, `website`

---

## ¿Qué hace este módulo?

Gestiona la solicitud y generación de certificados de notas para alumnos. Hay dos flujos:
- **Backend (admin/docente):** wizard directo que genera e imprime el PDF al instante.
- **Portal (alumno):** solicitud online con pago previo a través de la tienda.

Tipos de certificado disponibles: Digital (30€), Físico (40€), A Medida (40€), Físico Apostillado (80€). Se añaden cargos de envío Nacional (+20€) o Internacional (+60€) para los físicos.

## Funcionalidades principales

- Modelo de solicitud de certificado con estado y flujo de aprobación.
- Generación de PDF QWeb del certificado de notas.
- Wizard de generación desde el backend.
- Tienda online para pedido de certificados por el alumno (con pago).
- Cron para procesar solicitudes pendientes.
- Plantillas de email para notificaciones de estado.
- Secuencia numérica para los certificados.
- Reglas de seguridad por alumno.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.certificate.request` (nuevo) | Nuevo | Alumno, tipo, estado, pago, PDF |

## Vistas y UI

- `views/irg_certificate_request_views.xml` — gestión en el backend.
- `views/app_gradebook_student_views.xml` — botón de solicitud en la libreta del alumno.
- `views/menu.xml` — acceso desde menú.

## Notas técnicas

- Requiere `security/ir.model.access.csv` y `security/record_rules.xml`.
- Usa `data/sequence_data.xml`, `data/product_data.xml`, `data/mail_templates.xml`, `data/cron_data.xml`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_gradebook_certificates \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_gradebook_certificates \
    --stop-after-init --db_host=pgodoo_latest
```
