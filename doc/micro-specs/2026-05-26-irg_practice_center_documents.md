# Micro-Spec: IRG Practice Center Documents (2026-05-26)

## 1. Titulo corto
Adjuntos documentales en centros de practicas

## 2. Resumen objetivo
Crear un modulo nuevo `irg_practice_center_documents` para permitir que los usuarios internos suban y gestionen documentos asociados a cada `practice.center` desde la ficha backend del centro.

## 3. Motivo / justificacion
- La ficha de `practice.center` contiene datos administrativos del centro, cursos, tutores y horarios, pero no ofrece un apartado claro para guardar documentos del centro.
- El equipo necesita subir adjuntos antes de revisar o mantener los horarios de practicas.
- El cambio debe ser aditivo y realizarse por herencia, sin modificar `isep_practices_2`.

## 4. Alcance exacto
- Nuevo modulo `irg_practice_center_documents` en `addons-extra/extrairg/`.
- Herencia de `practice.center` para anadir un campo Many2many de adjuntos (`ir.attachment`).
- Herencia de la vista formulario `isep_practices_2.view_practice_center_form` para insertar la seccion de documentos antes de `Practice Schedules`.
- Visualizacion del nombre de los documentos adjuntos en la seccion de documentacion.
- Test automatizado que verifique el campo y la posicion de la vista.
- Documentacion de modulo en `doc/modules/extrairg/irg_practice_center_documents.md`.

## 5. Fuera de alcance
- No se exponen documentos en portal.
- No se crea un modelo documental con metadatos propios.
- No se modifican flujos de solicitud de practicas, horarios, tutores ni cursos.
- No se cambian permisos de `ir.attachment`; se reutiliza la seguridad estandar de Odoo para usuarios internos.

## 6. Dependencias
- `isep_practices_2`

## 7. Criterios de aceptacion
1. La instalacion del modulo anade `document_ids` al modelo `practice.center`.
2. El campo permite relacionar varios registros `ir.attachment`.
3. La ficha de `practice.center` muestra una seccion "Center Documentation" antes de la seccion "Practice Schedules".
4. La seccion muestra el nombre de los documentos adjuntos.
5. La vista se modifica mediante `inherit_id` y `xpath`, sin editar el XML original.
6. El cambio queda documentado y validado en Odoo local cuando el entorno este disponible.

## 8. Rollback plan
Desinstalar `irg_practice_center_documents` o revertir el commit del modulo y actualizar la base de datos.
