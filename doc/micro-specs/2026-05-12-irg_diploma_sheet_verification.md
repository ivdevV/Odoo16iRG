# Micro-spec: irg_diploma_sheet_verification
**Fecha:** 2026-05-12  
**Módulo:** `irg_diploma_sheet_verification`  
**Ruta:** `addons-extra/extrairg/irg_diploma_sheet_verification/`

---

## 1. Título corto
Verificación pública de diplomas por QR en el portal Odoo con fallback a Google Sheet.

## 2. Resumen objetivo
Mostrar en una página pública de Odoo el resultado de verificación de diplomas escaneados por QR, replicando el flujo del sitio anterior: primero Odoo y luego Google Sheet histórico.

## 3. Motivo / justificación
Los QR históricos apuntan a `/verificar/?id=CODIGO` y sus datos viven en una hoja de Google publicada como CSV. Odoo ya dispone de `irg_generacion_diplomas`, que crea registros nuevos en `irg.diploma.registry`; este módulo añade compatibilidad histórica sin modificar el módulo existente.

## 4. Alcance exacto
- Sobrescribir la ruta pública `/verificar/` para renderizar una página website/portal de Odoo.
- Buscar primero en `irg.diploma.registry` por `registry_number` y `state = valid`.
- Si no existe, consultar el CSV público de Google Sheet y buscar por columna `Codigo`.
- Mostrar mensajes visuales de certificado válido, no encontrado o instrucción de escaneo.
- Sobrescribir la generación de QR de `irg.diploma.wizard` para usar el dominio configurado en Odoo.
- Separar `registry_number` (`IRG-2026-0220`) del código QR verificable (`ABC-5026`).
- Vincular el wizard al menú Acción de `op.student` para que aparezca de forma consistente.

## 5. Diseño técnico
- Controlador nuevo con misma ruta que el módulo base, cargado después por dependencia.
- Parser CSV con `urllib.request` y `csv.DictReader`.
- Normalización: quitar espacios y convertir a mayúsculas.
- Nomenclatura histórica aceptada: `AAA-0000` incluyendo letras acentuadas (`ÁÉÍÓÚÜÑ`).
- Nuevo campo `verification_code` en `irg.diploma.registry`, único e indexado.
- Nueva secuencia `irg.diploma.verification.code`, iniciada en `5026` para continuar tras el último código histórico del Sheet (`NAT-5025`).
- URL base del QR resuelta desde `irg_diploma_sheet_verification.verify_base_url` o, si no existe, desde `web.base.url`.
- Template QWeb propio usando `website.layout`.

## 6. Dependencias
```python
['website', 'irg_generacion_diplomas']
```

## 7. Backwards-compatibility / migración
- No se modifican modelos ni tablas existentes.
- Se añade un campo nullable a `irg.diploma.registry`; los diplomas antiguos siguen verificando por `registry_number`.
- Los QR antiguos siguen usando `/verificar/?id=...`.
- Los QR nuevos generados desde Odoo apuntan al dominio configurado en cada entorno.

## 8. Casos de prueba / criterios de aceptación
1. `/verificar/` sin `id` muestra instrucción para escanear el QR.
2. `/verificar/?id=DAN-5002` encuentra el registro histórico en Google Sheet y muestra alumno/curso/código.
3. `/verificar/?id=<registry_number_odoo>` encuentra el registro válido de Odoo.
4. `/verificar/?id=NO-EXISTE` muestra mensaje de no encontrado.
5. Un diploma nuevo generado desde Odoo contiene QR con base `https://app.institutoraimongaja.com/verificar/`.

## 9. Rollback
```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf -d <db> \
  --uninstall-modules irg_diploma_sheet_verification --stop-after-init --db_host=pgodoo_latest
```
Eliminar carpeta `addons-extra/extrairg/irg_diploma_sheet_verification/`.
