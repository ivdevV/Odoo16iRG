# irg_crm_date_open_filter

> Nota: el nombre tecnico del modulo se conserva por continuidad de despliegue. El campo funcional correcto es `fecha_reactivacion`.

1. Titulo corto

   Campos de reactivacion en busqueda y columnas CRM.

2. Resumen objetivo

   Exponer los campos de reactivacion de `crm.lead` en las vistas de busqueda generales de Leads/Oportunidades y en las columnas opcionales de Leads. El cambio permite localizar, filtrar y mostrar registros por fecha, campana, fuente y referido de reactivacion sin tocar el modulo nativo `crm`.

3. Motivo / justificacion

   `fecha_reactivacion` ya existe en `crm.lead` a traves de `irg_crm_extensions`, y los campos `irg_campana_reactivacion`, `irg_fuente_reactivacion` e `irg_referido_reactivacion` existen a traves de `irg_crm_reactivacion`. Estos campos no aparecen como columnas opcionales en el listado estandar de Leads ni como criterios generales de busqueda de Leads. Se implementa mediante un modulo extra con herencia XML para respetar la politica de no modificar core ni modulos existentes.

4. Alcance exacto

   - Modelo afectado: `crm.lead`.
   - Vistas afectadas por herencia:
     - `crm.view_crm_case_leads_filter`.
   - `crm.view_crm_case_opportunities_filter`.
   - `crm.crm_case_tree_view_leads`.
   - No se crean modelos, controladores, assets ni reglas de seguridad.

5. Diseno tecnico

   - Crear modulo `irg_crm_date_open_filter` en `addons-extra/extrairg/`.
   - Depender de `irg_crm_extensions`, que define `fecha_reactivacion`.
   - Depender de `irg_crm_reactivacion`, que define `irg_campana_reactivacion`, `irg_fuente_reactivacion` e `irg_referido_reactivacion`.
   - Heredar las vistas de busqueda de Leads y Oportunidades mediante `inherit_id`.
   - Heredar la vista de lista de Leads mediante `inherit_id`.
   - Insertar los campos de reactivacion en la zona de campos generales de busqueda.
   - Insertar `<filter date="fecha_reactivacion"/>` junto a los filtros de fecha existentes.
   - Insertar los campos de reactivacion con `optional="hide"` despues de `create_date` en el listado de Leads para que aparezcan en el selector de columnas opcionales.

6. Dependencias

   - `crm`.
   - `irg_crm_extensions`.
   - `irg_crm_reactivacion`.

7. Backwards-compatibility / migracion

   No requiere migracion de datos. Los campos ya existen en sus modulos propietarios y los registros existentes conservaran sus valores actuales.

8. Casos de prueba / criterios de aceptacion

   - El modulo instala/actualiza sin errores XML.
   - En CRM > Leads aparece `Fecha Reactivacion` como criterio de busqueda y filtro de fecha.
   - En CRM > Leads aparece `Fecha Reactivacion` en el selector de columnas opcionales del listado.
   - En CRM > Leads aparecen `Campana de Reactivacion`, `Fuente de Reactivacion` y `Referido de Reactivacion` como criterios de busqueda y columnas opcionales.
   - En CRM > Pipeline/Oportunidades aparece `Fecha Reactivacion` como criterio de busqueda y filtro de fecha.
   - En CRM > Pipeline/Oportunidades aparecen `Campana de Reactivacion`, `Fuente de Reactivacion` y `Referido de Reactivacion` como criterios de busqueda.
   - La busqueda por rangos de fecha usa el campo `fecha_reactivacion`.

9. Rollback plan

   - Desinstalar `irg_crm_date_open_filter` desde Apps, o ejecutar:
     `docker exec odoo_latest odoo -c /etc/odoo/odoo.conf -d <dbname> -u crm --stop-after-init --db_host=pgodoo_latest` despues de retirar el modulo del addons path.

10. Estimacion y responsable

   - Estimacion: 0.5 horas.
   - Responsable: IRG / Copilot.