# irg_generacion_diplomados_website_verify

## Proposito

Este modulo permite validar diplomas de diplomados desde el QR del PDF usando el sitio web del propio Odoo.

Extiende la validacion existente de `irg_generacion_diplomas` para que la ruta publica `/verificar` reconozca tambien registros de `irg.diplomado.registry`.

## Dependencias

- `website`
- `irg_generacion_diplomas`
- `irg_generacion_diplomados`

## Comportamiento

- La URL del QR de nuevos PDFs de diplomados se construye con `web.base.url`.
- La ruta usada es `/verificar/?id=<numero_registro>`.
- Si existe `op.sign_certificate`, se conservan los parametros de sello `stamp`, `data_str` y `certificate_id`.
- `/verificar` muestra una pagina web con los datos del diplomado cuando encuentra `irg.diplomado.registry.name`.
- `/verificar_api` devuelve JSON con `document_type = diplomado` cuando el codigo pertenece a un diplomado.
- La validacion anterior de diplomas convencionales sigue delegando en `irg_generacion_diplomas`.

## Uso

1. Instalar o actualizar `irg_generacion_diplomados_website_verify`.
2. Confirmar que `web.base.url` apunta al dominio publico correcto.
3. Generar o regenerar un diploma de diplomado.
4. Escanear el QR del PDF.
5. Comprobar que abre `/verificar/?id=<registro>` y muestra el diplomado como valido.

## Limitaciones

- Los PDFs generados antes de instalar este modulo conservan el QR antiguo hasta que se regeneren.
- `action_reprint()` solo regenera el PDF si el registro no tiene `attachment_id`; si ya existe un adjunto antiguo, hay que eliminarlo o regenerarlo mediante un flujo especifico.

## Validacion Ejecutada

```bash
python3 -m compileall "addons-extra/extrairg/irg_generacion_diplomados_website_verify"
```

```bash
python3 - <<'PY'
from lxml import etree
etree.parse('addons-extra/extrairg/irg_generacion_diplomados_website_verify/views/diplomado_verify_templates.xml')
print('OK')
PY
```

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -u irg_generacion_diplomados_website_verify --test-enable --test-tags irg_generacion_diplomados_website_verify --stop-after-init --http-port=8099 --log-level=test
```

Resultado Odoo: `0 failed, 0 error(s) of 3 tests`.
