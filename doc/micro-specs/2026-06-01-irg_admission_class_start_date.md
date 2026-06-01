# IRG Admission Class Start Date

## 1. Titulo corto

Fecha de inicio de clases en admisiones.

## 2. Resumen objetivo

Crear un modulo extra para anadir una fecha de inicio de clases en `op.admission`. El campo sera de tipo fecha y se mostrara solo en el formulario de admision.

## 3. Motivo / justificacion

El equipo necesita registrar en cada admision una fecha especifica de inicio de clases, independiente de la fecha de admision, vencimiento o inicio de cuotas. La funcionalidad debe implementarse por herencia en un modulo `irg_*` para no modificar OpenEduCat ni modulos existentes.

## 4. Alcance exacto

- Crear el modulo `irg_admission_class_start_date` en `addons-extra/extrairg/`.
- Extender el modelo `op.admission` con un campo `fields.Date`.
- Heredar el formulario `openeducat_admission.view_op_admission_form` para mostrar el campo.
- No modificar vistas tree/listado ni search/agrupaciones.
- No crear automatizaciones, validaciones de negocio ni nuevos modelos.

## 5. Diseno tecnico

- Modulo: `addons-extra/extrairg/irg_admission_class_start_date`.
- Modelo heredado: `_inherit = 'op.admission'`.
- Campo tecnico: `irg_class_start_date`.
- Etiqueta visible: `Fecha de inicio de clases`.
- Tipo: `fields.Date`.
- Comportamiento: `copy=False`, editable desde la admision y sin relacion ni calculo sobre el lote.
- Vista heredada: `openeducat_admission.view_op_admission_form`.
- XPath previsto: insertar el campo despues de `//field[@name='due_date']`, dentro de la pestana `Admission Detail`.

## 6. Dependencias

- `openeducat_admission`

## 7. Backwards-compatibility / migracion

El cambio solo anade una columna nueva opcional en `op.admission`. Las admisiones existentes no requieren migracion de datos y el campo quedara vacio hasta que se informe manualmente.

## 8. Casos de prueba / criterios de aceptacion

- El modulo se instala o actualiza sin errores.
- El formulario de admision muestra el campo `Fecha de inicio de clases` despues de `Due Date`.
- El campo permite seleccionar y guardar una fecha.
- Al reabrir la admision, la fecha guardada persiste.
- El campo sigue siendo editable desde la admision aunque la admision este en estado `done`, siempre que el usuario tenga permisos de escritura sobre `op.admission`.
- El campo no aparece en listados ni en la busqueda de admisiones.

## 9. Rollback plan

Desinstalar el modulo `irg_admission_class_start_date` desde Apps o revertir el commit que lo introduce y actualizar la instancia. Al retirar el modulo, la columna agregada deja de estar disponible desde Odoo; no se modifican datos funcionales de OpenEduCat.

## 10. Estimacion y responsable

Estimacion: 1 hora tecnica incluyendo implementacion, revision de sintaxis y documentacion. Responsable: IRG / GitHub Copilot bajo revision funcional del equipo academico.