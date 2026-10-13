# Plan: CIF en centros de prácticas

## Petición

Añadir en cada centro de prácticas un campo donde se pueda registrar su CIF.

## jev_intake

```json
{"status": "skipped", "skipped_reason": "http_error", "model": null, "mission_class": null, "mission_class_confidence": null, "mission_class_binding": false, "exceeds_simple_limits": false, "exceeds_simple_noul": null, "needs_security_advisor": false, "security_noul": null, "security_keyword_hit": false, "effective_class": null, "effective_class_binding": false}
```

`effective_class_binding` es falso y `status` es `skipped` por `http_error`. Clasifica el orquestador: misión `full`. No hay términos de autenticación, secretos, migración de datos, despliegue ni borrado histórico, así que no se convoca al Security Advisor.

## Clasificación

- Clase: `full`. Es un cambio de producto: campo nuevo, vista de formulario y prellenado del convenio.
- Tier: `standard`. El cambio funcional es un `Char` en `practice.center`, su vista y el uso de ese valor al generar el contacto y el NIF/CIF del convenio. El contexto está en `isep_practices_2` e `irg_practice_agreement_sign`.
- Capacidad: Grok 4.7. El runtime no permite seleccionar otro modelo.
- E2E TestSprite: obligatorio. El diff toca `views/practice_center_views.xml`.

## Contexto

`practice.center` no tiene CIF. `create_res_partner` crea el `res.partner` sin `vat`. Los convenios guardan `center_vat` y, si nadie lo escribe a mano, lo copian de `partner_id.vat`. Por eso el NIF/CIF del convenio sale vacío aunque el centro ya esté dado de alta.

Conocimiento consultado: `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`. El módulo nuevo va en `addons-extra/extrairg/` con prefijo `irg_` y herencia; no se edita `isep_practices_2`.

## Alcance

Módulo nuevo `irg_practice_center_cif`:

- Campo `cif` (`Char`, etiqueta CIF) en `practice.center`.
- Visible en el formulario, después de Nombre oficial; también en la lista y en la búsqueda.
- Al pulsar Generate Center, el CIF del centro se copia a `res.partner.vat`.
- Al crear un convenio sin NIF/CIF explícito, `center_vat` toma el CIF del centro. Si el centro no tiene CIF, se mantiene el `vat` del contacto.
- Un CIF escrito a mano en el convenio no se pisa.

Fuera de alcance: validación del formato del CIF, el formulario público de alta de centros y reescribir convenios ya creados.

## Criterios de aceptación

1. La ficha del centro permite guardar un CIF.
2. La lista y la búsqueda permiten ver y buscar por ese CIF.
3. Generate Center deja ese CIF en el VAT del contacto creado.
4. Un convenio nuevo sin `center_vat` explícito recibe el CIF del centro.
5. Si el centro no tiene CIF, el convenio sigue pudiendo usar el VAT del contacto.
6. No se modifica el código de módulos ya existentes.

## Pruebas

- Unidad, sin Odoo, de `resolve_center_cif`: el CIF del centro gana; si falta, se usa el VAT del contacto; los espacios se recortan.
- Módulo Odoo (`TransactionCase`) para el campo, las vistas, Generate Center y el prellenado del convenio, con `docker-compose.local.yml`.
- `e2e_testsprite` después de que el resto de checks pase, contra el runtime local y una base desechable. `projectPath` será el directorio del módulo.

## Riesgos

- El daemon de Docker no está en marcha en este momento. Las pruebas de módulo y el E2E dependen de ese runtime.
- `action_create_agreement` ya escribe `center_vat` desde el partner. El módulo nuevo debe volver a aplicar el CIF del centro después de esa copia, sin editar el módulo de firma.
