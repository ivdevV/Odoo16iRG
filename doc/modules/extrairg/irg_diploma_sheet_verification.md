# irg_diploma_sheet_verification

**Categoría:** extrairg
**Versión:** 16.0.1.1.1
**Licencia:** AGPL-3
**Instalable:** Sí
**Autor:** ISEP / iRG
**Depende de:** `website`, `irg_generacion_diplomas`

---

## ¿Qué hace este módulo?

Permite la verificación pública de validez de diplomas mediante el escaneo de un código QR. Al acceder a la URL `/verificar?id=CODIGO`, el módulo consulta primero el registro local de diplomas de Odoo (`irg.diploma.registry`) y, si no lo encuentra, realiza un fallback a una base de datos histórica almacenada en un Google Sheet público (en formato CSV).

## Funcionalidades principales

- **Página de verificación pública**: Endpoint `/verificar` (y `/web/verificar`) para consultar e interactuar con el estado del diploma desde el sitio web de Odoo.
- **Endpoint de API**: `/verificar_api` para verificaciones externas, retornando un objeto JSON con los metadatos del diploma.
- **Búsqueda en Odoo**: Consulta en la base de datos de Odoo mediante el modelo `irg.diploma.registry`.
- **Fallback a Google Sheet CSV**: En caso de no existir en Odoo, si el código coincide con el patrón histórico de 3 letras y 4 números (ej. `DAN-5026`), consulta y analiza dinámicamente un archivo CSV de Google Sheets publicado en la web.
- **Desvinculación del menú Acciones**: Se remueve el wizard del menú desplegable de "Acciones" en la ficha del alumno para centralizar el flujo en la cabecera.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.diploma.registry` (heredado) | Heredado | `verification_code` (Código de verificación QR único) |

## Vistas y UI

- `views/diploma_action_views.xml` — Sobrescribe la acción del wizard para anular su binding con el modelo `op.student`.
- `views/diploma_verify_templates.xml` — Template del sitio web (`portal_verify_diploma`) para mostrar el resultado y datos del diploma.

## Notas técnicas

- **URL de fallback Google Sheet (CSV)**:
  `https://docs.google.com/spreadsheets/d/e/2PACX-1vQWMkf_KDPsymfZpgnAZwklWDraZAm2hudY9ORarnkx9dxxbNPLjcKFr_3FdKt7Z-Cvxia3hWNt2puZ/pub?output=csv`
- **Regex para códigos históricos**: `^[A-ZÁÉÍÓÚÜÑ]{3}-\d{4}$`.
- **Prevención de fallos por mobile QR scanners**: Se define un objeto `window.ethereum` vacío en la vista para prevenir que ciertos navegadores móviles o extensiones de monederos cripto inyecten scripts que rompan el JavaScript de la página de verificación.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_diploma_sheet_verification \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_diploma_sheet_verification \
    --stop-after-init --db_host=pgodoo_latest
```

## Historial de Cambios

### Versión 16.0.1.1.1
- **Eliminación del menú de Acciones**: Desvinculación de la acción del wizard de diplomas del menú de Acciones del estudiante (`binding_model_id = False`) para centralizar la generación en el botón de la cabecera.

### Validación 16.0.1.1.1
- Carga de Odoo exitosa localmente y verificación de que la acción de generación de diplomas ya no se muestra en el menú "Acciones" de la ficha del alumno (`op.student`).
