# irg_crm_date_open_filter

1. Titulo corto

   Filtro general por fecha de asignacion en CRM.

2. Resumen objetivo

   Exponer el campo nativo `date_open` de `crm.lead` en las vistas de busqueda generales de Leads y Oportunidades. El cambio permite localizar y filtrar registros por fecha de asignacion/apertura sin tocar el modulo nativo `crm`.

3. Motivo / justificacion

   `date_open` ya existe en Odoo 16 dentro de `crm.lead`, pero no aparece como criterio general en las busquedas estandar de CRM. Se implementa mediante un modulo extra con herencia XML para respetar la politica de no modificar core ni modulos existentes.

4. Alcance exacto

   - Modelo afectado: `crm.lead`.
   - Vistas afectadas por herencia:
     - `crm.view_crm_case_leads_filter`.
     - `crm.view_crm_case_opportunities_filter`.
   - No se crean modelos, controladores, assets ni reglas de seguridad.

5. Diseno tecnico

   - Crear modulo `irg_crm_date_open_filter` en `addons-extra/extrairg/`.
   - Heredar las vistas de busqueda CRM mediante `inherit_id`.
   - Insertar `<field name="date_open"/>` en la zona de campos generales de busqueda.
   - Insertar `<filter date="date_open"/>` junto a los filtros de fecha existentes.

6. Dependencias

   - `crm`.

7. Backwards-compatibility / migracion

   No requiere migracion de datos. El campo `date_open` es nativo y los registros existentes conservaran sus valores actuales.

8. Casos de prueba / criterios de aceptacion

   - El modulo instala/actualiza sin errores XML.
   - En CRM > Leads aparece `Fecha de asignacion` como criterio de busqueda y filtro de fecha.
   - En CRM > Pipeline/Oportunidades aparece `Fecha de asignacion` como criterio de busqueda y filtro de fecha.
   - La busqueda por rangos de fecha usa el campo `date_open`.

9. Rollback plan

   - Desinstalar `irg_crm_date_open_filter` desde Apps, o ejecutar:
     `docker exec odoo_latest odoo -c /etc/odoo/odoo.conf -d <dbname> -u crm --stop-after-init --db_host=pgodoo_latest` despues de retirar el modulo del addons path.

10. Estimacion y responsable

   - Estimacion: 0.5 horas.
   - Responsable: IRG / Copilot.