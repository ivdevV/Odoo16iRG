# IRG Online Subject Opening

## 1. Titulo corto

Apertura individual de asignaturas online por admision.

## 2. Resumen objetivo

Crear un modulo extra para calcular y guardar fechas de apertura de asignaturas online por alumno y asignatura. Las aperturas se escalonan cada 30 dias desde la fecha de admision y solo aplican a lotes cuyo codigo contiene `ONL`, excluyendo los que contienen `MONL`.

## 3. Motivo / justificacion

El calendario actual de asignaturas se define a nivel de lote mediante `op.subject.to.batch.date_from/date_to`, lo que aplica a todos los alumnos del lote por igual. La necesidad es individual porque la base de calculo es `op.admission.admission_date`; por tanto se requiere un modulo extra con herencia para no tocar OpenEduCat ni los modulos existentes.

## 4. Alcance exacto

- Crear el modelo `irg.online.subject.opening` para almacenar ventanas por admision/asignatura.
- Extender `op.admission` para generar, regenerar y sincronizar el calendario individual.
- Ajustar la autoinscripcion eLearning para admisiones online aplicables.
- Mostrar el calendario en la ficha de admision.
- Ajustar el portal del alumno para usar fechas individuales en admisiones online aplicables.
- No modificar modulos nativos ni custom existentes.

## 5. Diseno tecnico

- Nuevo modulo: `addons-extra/extrairg/irg_online_subject_opening`.
- Nuevo modelo: `irg.online.subject.opening`.
- Herencia Python: `_inherit = 'op.admission'`.
- Herencia XML backend: `openeducat_admission.view_op_admission_form`.
- Herencia QWeb portal: `irg_subject_fix.user_profile_content_details_irg_fix`.
- Regla de lote aplicable: `ONL` incluido y `MONL` excluido, normalizando el codigo a mayusculas.
- Orden de asignaturas: `op.subject.code`.
- Fechas: `opening_date = admission_date + 30 * indice`; `closing_date = opening_date + 29 dias`.
- Sincronizacion: copiar fechas a `slide.channel.partner.date_from/date_to` para mantener el flujo eLearning existente.

## 6. Dependencias

- `isep_elearning_custom`
- `irg_subject_fix`
- `isep_subject_precedence`
- `website_slides`

## 7. Backwards-compatibility / migracion

El modulo no altera datos globales de lote ni reemplaza `op.subject.to.batch`. Las admisiones no aplicables, incluyendo lotes `MONL`, conservan el comportamiento vigente. Al instalarse, las aperturas se generaran al crear/actualizar admisiones o al ejecutar los flujos de autoinscripcion; no se requiere migracion destructiva.

## 8. Casos de prueba / criterios de aceptacion

- Un lote `MOPCONL` genera aperturas individuales.
- Un lote con `MONL` no genera aperturas individuales.
- Un lote sin `ONL` no genera aperturas individuales.
- Las asignaturas se ordenan por codigo.
- Tres asignaturas con admision `2026-05-07` abren en `2026-05-07`, `2026-06-06` y `2026-07-06`.
- Cada cierre representa una ventana inclusiva de 30 dias.
- Cambiar `admission_date` regenera fechas.
- La sincronizacion con `slide.channel.partner` usa las fechas individuales en admisiones aplicables.

## 9. Rollback plan

Desinstalar el modulo desde Apps o ejecutar:

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf -d <dbname> -u base --stop-after-init --db_host=pgodoo_latest
```

Si se requiere retirada de codigo, revertir el commit del modulo y actualizar la instancia. Los datos globales de lotes no se modifican por este modulo.

## 10. Estimacion y responsable

Estimacion: 1 jornada tecnica incluyendo pruebas basicas y documentacion. Responsable: IRG / GitHub Copilot bajo revision funcional del equipo academico.
