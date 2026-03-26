# Micro-spec: irg_website_sale_monthly_default_combo

1. Titulo: Alinear precio de listado con combinacion por defecto de ficha
2. Resumen: El listado de tienda mostrara la misma cuota/mes que la combinacion por defecto en ficha de producto.
3. Justificacion: Evitar discrepancias visuales de precio entre grid y detalle sin tocar core.
4. Alcance: Override de `website_sale.products_item` y helper en `product.template`.
5. Diseno tecnico: Modulo `irg_website_sale_monthly_default_combo` con `_inherit` y `xpath`.
6. Dependencias: `isep_website_sale_monthly_price`, `isep_website_sale_custom`, `website_sale`.
7. Compatibilidad: Cambio de presentacion; no altera precios de orden ni facturacion.
8. Criterios de aceptacion: Mismo importe mensual en listado y ficha para producto y combinacion por defecto.
9. Rollback: Desinstalar modulo `irg_website_sale_monthly_default_combo`.
10. Estimacion/Responsable: 1h / equipo iRG.
