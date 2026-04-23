# isep_sign_sale

**Categoría:** addons_uisep
**Versión:** 0.1
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP
**Depende de:** `base`, `sale`, `sign`, `isep_form_data`, `l10n_latam_base`, `sale_subscription`

---

## ¿Qué hace este módulo?

Integra la firma electrónica en el proceso de matrícula. Cuando se confirma un pedido de venta de matrícula, genera automáticamente el documento de contrato de matrícula y lo envía al alumno para su firma digital mediante el módulo Sign de Odoo.

## Funcionalidades principales

- Generación automática del contrato de matrícula en el pedido de venta.
- Envío del documento para firma electrónica al alumno.
- Plantilla de contrato con datos del alumno y condiciones de matrícula.
- Seguimiento del estado de la firma desde el pedido.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `sale.order` | Herencia | Estado de firma, documento de matrícula |
| `sign.request` | Herencia | Vinculación con el pedido de venta |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i isep_sign_sale \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u isep_sign_sale \
    --stop-after-init --db_host=pgodoo_latest
```
