# irg_crm_translation_audit

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** AGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `crm`

---

## ¿Qué hace este módulo?

Añade un asistente técnico para auditar las traducciones cargadas en CRM y en módulos personalizados relacionados. Su objetivo es ayudar a revisar qué términos existen en el catálogo clásico `ir.translation`, agrupándolos por módulo y tipo, sin modificar ni traducir registros.

El asistente se abre desde la configuración de CRM y está pensado para usuarios administradores. Permite seleccionar el idioma, incluir o excluir módulos CRM de `addons_uisep` y aplicar un filtro técnico por nombre de término. El resultado se muestra como un resumen HTML con contadores y una muestra de términos encontrados.

## Funcionalidades principales

- Asistente transient `irg.crm.translation.audit.wizard` para inspección puntual de traducciones CRM.
- Selector de idioma basado en `res.lang`, con valor por defecto tomado del contexto o del idioma del usuario.
- Opción para incluir módulos CRM de `addons_uisep` además del bloque CRM/core de IRG.
- Filtro técnico por nombre de término, con valor inicial `crm`.
- Resumen visual con idioma auditado, módulos inspeccionados, total de términos, conteo por módulo y conteo por tipo.
- Tabla de muestra con hasta 25 términos y columnas disponibles de `ir.translation` (`module`, `type`, `name`, `src`, `value`).
- Aviso cuando la búsqueda alcanza el límite de 5000 términos.
- Acceso desde el menú de configuración de CRM, restringido a administradores del sistema.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.crm.translation.audit.wizard` | Nuevo transient | `lang_id`, `include_isep_crm`, `name_filter`, `result_html` |
| `ir.translation` | Consulta técnica | Lectura de términos por idioma, módulo, tipo, nombre, origen y valor traducido |

## Vistas y UI

- `views/crm_translation_audit_views.xml` define el formulario modal del asistente.
- El formulario incluye los campos `lang_id`, `include_isep_crm`, `name_filter` y el resultado HTML de solo lectura.
- El botón **Actualizar resumen** ejecuta `action_refresh` y recalcula el informe en la misma ventana modal.
- Añade la acción `action_irg_crm_translation_audit`.
- Añade el menú **Auditor de traducciones CRM** bajo `crm.crm_menu_config`, con acceso limitado al grupo `base.group_system`.

## Dependencias externas

- `crm` — aporta el menú de configuración CRM donde se incorpora el asistente y el contexto funcional de auditoría.

## Seguridad

- `security/ir.model.access.csv` concede permisos de lectura, escritura, creación y borrado sobre el asistente transient solo al grupo `base.group_system`.
- El menú también queda restringido a `base.group_system`, por lo que la herramienta está orientada a administradores.
- El módulo no define controladores HTTP ni endpoints públicos.

## Notas técnicas

- El asistente no traduce, crea ni actualiza términos; únicamente consulta `ir.translation` y guarda el HTML del resultado en el propio wizard.
- Usa `expression.OR` y `expression.AND` para construir el dominio de búsqueda combinando módulo e índice técnico.
- La consulta se limita a 5000 términos para evitar respuestas excesivas en la interfaz.
- El HTML se construye con `markupsafe.escape` para evitar inyección de contenido al mostrar valores procedentes de traducciones.
- Si `ir.translation` no está disponible en la instancia, se lanza un `UserError` explicando que no se puede auditar el catálogo clásico de traducciones.
- No utiliza `sudo()`, SQL raw, crons, assets JS/SCSS ni controladores.
- Incluye un test básico que crea el asistente, ejecuta `action_refresh` y comprueba que se genera una acción de ventana con contenido HTML.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_crm_translation_audit \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_crm_translation_audit \
    --stop-after-init --db_host=pgodoo_latest
```
