# irg_sign_position_fix

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `isep_sign_sale`, `irg_sale_order_extended`

---

## ¿Qué hace este módulo?

Ajusta la posición vertical (`posY`) del recuadro de firma en el documento de matrícula para que quede correctamente alineado en la plantilla. Corrige un problema de posicionamiento que hacía que el recuadro de firma se superpusiera o quedara desplazado del espacio designado.

## Funcionalidades principales

- Override de la vista de mensaje de pago para ajustar el posicionamiento del recuadro de firma.

## Vistas y UI

- `views/payment_message.xml` — ajuste de posición del bloque de firma.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_sign_position_fix \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_sign_position_fix \
    --stop-after-init --db_host=pgodoo_latest
```
