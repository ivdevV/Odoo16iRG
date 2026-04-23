# irg_sale_subscription_esp

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** Odoo (customizado por IRG)
**Depende de:** `sale`, `website_sale`, `sale_subscription`, `isep_sale_subscription_extension`, `isep_sale_subscription_custom`, `isep_website_sale_custom`

---

## ¿Qué hace este módulo?

Override español del sistema de suscripciones y financiación del ecommerce. Automatiza el desglose de los gastos de financiación en los pedidos de venta, calculando la diferencia entre el precio de contado y el precio financiado, y creando líneas de servicio dedicadas para representar ese coste.

Es el módulo que adapta el flujo de suscripciones genérico de ISEP al mercado español con sus particularidades de financiación.

## Funcionalidades principales

- Desglose automático de gastos de financiación en líneas de pedido.
- Generación de línea de servicio para el coste de financiación.
- Override del controlador de checkout para garantizar el orden correcto de dependencias.
- Resumen del carrito adaptado al flujo de financiación.

## Vistas y UI

- `views/cart_summary.xml` — resumen de carrito con desglose de financiación.

## Notas técnicas

- La dependencia de `isep_website_sale_custom` garantiza que el controller override de este módulo tenga prioridad.
- `data/product_data.xml` crea el producto de servicio para la línea de financiación.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_sale_subscription_esp \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_sale_subscription_esp \
    --stop-after-init --db_host=pgodoo_latest
```
