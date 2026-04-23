# isep_sale_subscription_extension

**Categoría:** addons_uisep
**Versión:** 16.0.1.0.0
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP
**Depende de:** `base`, `sale`, `sale_subscription`, `sales_team`, `account`, `web`, `report_xlsx`, `web_grid`, `isep_openeducat_sale`, `isep_website_sale_custom`, `isep_website_sale_monthly_price`

---

## ¿Qué hace este módulo?

Es el **choreographer** principal del flujo de suscripciones de ISEP. Gestiona el calendario de pagos de los alumnos (cuotas, fechas de vencimiento, aplazamientos), el seguimiento de la cartera de deuda y la generación de informes de estado de cuenta. Es el núcleo del sistema de financiación de matrículas.

## Funcionalidades principales

- Modelo de calendario de pagos con cuotas y fechas.
- Gestión de aplazamientos y reestructuraciones de pagos.
- Informes en Excel (XLSX) de cartera y estado de cuenta del alumno.
- Vista grid (web_grid) para planificación visual de cobros.
- Integración con el flujo de suscripciones de Odoo.
- Controlador JS para la vista grid de cobros.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `sale.order` | Herencia | Campos de calendario de pagos, cuotas |
| `account.move` | Herencia | Vinculación con el schedule de pagos |

## Vistas y UI

- Informes XLSX de cartera y estado de cuenta.
- Vista grid de cobros programados.
- Acciones de servidor para gestión de cobros.

## Notas técnicas

- Requiere `report_xlsx` para los informes Excel.
- El controlador JS gestiona la interacción con la vista `web_grid`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i isep_sale_subscription_extension \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u isep_sale_subscription_extension \
    --stop-after-init --db_host=pgodoo_latest
```
