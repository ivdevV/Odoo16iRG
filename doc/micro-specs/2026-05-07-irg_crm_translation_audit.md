# Micro-spec: irg_crm_translation_audit

1. Title: Auditor de traducciones del CRM
2. Summary: Añade un asistente técnico en CRM para revisar qué términos de traducción están cargados para el CRM nativo y los módulos personalizados que extienden `crm.lead`.
3. Justification: La revisión previa confirma que no existe un módulo custom que gestione globalmente las traducciones del CRM. El objetivo es dar trazabilidad desde la interfaz de Odoo sin tocar core ni modificar módulos existentes.
4. Scope: Nuevo módulo en `addons-extra/extrairg/irg_crm_translation_audit`. Añade un wizard transient, vista formulario, acción y menú técnico bajo CRM. No cambia datos de leads ni activa traducción automática.
5. Design: Crea `irg.crm.translation.audit.wizard` con `_name` propio. El wizard usa ORM sobre `ir.translation` para contar términos por módulo e idioma y genera un resumen HTML. La búsqueda se limita a módulos CRM conocidos (`crm`, `irg_migration_fields`, `irg_academic_adaptations`, `irg_crm_extensions`, `irg_crm_gclid`, `irg_crm_lead_dedup`, `irg_crm_reactivacion`) y permite incluir módulos `isep_*` relacionados con CRM.
6. Depends: `crm`.
7. Backwards compatibility: Solo añade un modelo transient y un menú técnico. No altera columnas, vistas core ni comportamiento operativo del CRM.
8. Tests / Acceptance: El módulo instala sin errores. Un usuario administrador puede abrir CRM > Configuración > Auditor de traducciones CRM y pulsar “Actualizar resumen”. El resultado muestra idioma, módulos inspeccionados, conteos por módulo y muestras de términos.
9. Rollback: Desinstalar `irg_crm_translation_audit` con `-u`/Apps o eliminar el módulo de `addons-extra/extrairg/`; no hay migración de datos persistente.
10. Estimation / Responsible: 45 min. Responsible: iRG dev.
