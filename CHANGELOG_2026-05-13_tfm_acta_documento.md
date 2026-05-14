# CHANGELOG — irg_tfm_acta_documento (2026-05-13)

**Módulo:** `irg_tfm_acta_documento`  
**Versión:** 16.0.1.0.0  
**Fecha:** 2026-05-13  

## Problema observado

Santiago Borges Rodríguez (Dirección iRG) solicitaba una solución para generar actas de evaluación (PDF) de Trabajos Finales de Máster (TFM) y Grado (TFG) que fuera:
- Oficialmente válida con datos inamovibles (prellenados por secretaría).
- Editable en tres campos críticos: Calificación, Observaciones, Firma.
- Coherente con la identidad visual de iRG.
- Eficiente (sin trabajo manual repetitivo).

## Solución aplicada

Se desarrolló el módulo `irg_tfm_acta_documento` (Odoo 16) que:

### Funcionalidades principales

1. **Modelo `irg.tfm.acta`:**
   - Registro persistente de actas generadas.
   - Campos inamovibles: titulación, alumno, director, tribunal, secretario.
   - Campos editables: fecha defensa, calificación, observaciones.
   - Attachment automático para auditoría.

2. **Generador PDF (ReportLab):**
   - **Página 1:** Datos fijos (alumno, tribunal, título del trabajo).
   - **Página 2:** Campos editables en espacios en blanco (calificación, observaciones, firma).
   - Logos iRG reutilizados de `irg_generacion_diplomas`.
   - Tipografía Inter con fallback Helvetica.
   - Escalabilidad para A4.

3. **Wizard (`irg.tfm.acta.wizard`):**
   - Interfaz modal para generación desde la ficha del estudiante.
   - Selección de tipo (TFM/TFG).
   - Prefillables automáticos (año académico actual).
   - Genera PDF y descarga automática.

4. **Integración:**
   - Botón "Generar Acta TFM/TFG" en la vista del estudiante (`op.student`).
   - Menú en "Operaciones Académicas" para listar/consultar actas.
   - ACLs con permisos granulares (admin/user).
   - Tests mínimos (TC-001 a TC-004).

### Dependencias reutilizadas

- `irg_generacion_diplomas`: Fonts, logos, patrón ReportLab.
- `openeducat_core`: Modelos `op.student` y `op.student.course`.

### Campos y estructura

**Inamovibles (prellenados):**
- Titulación
- Curso académico
- Alumno (Nombre, Apellidos, DNI)
- Título del trabajo
- Director/a TFT
- Tribunal (Presidente, Secretario/a)

**Editables en PDF (espacios en blanco):**
- Fecha de defensa
- Calificación (rectángulo de relleno)
- Observaciones (líneas guía)
- Firma del Secretario (espacio para firma manuscrita)

## Impacto

- **Alcance:** Módulo nuevo, sin modificación de core ni módulos nativos.
- **Compatibilidad:** Odoo 16, compatible con OpenEduCat.
- **Riesgos residuales:** Ninguno identificado (operación aislada, no toca datos críticos).
- **Despliegue:** Standard vía Jenkins tras merge a `Dev_iRG`.

## Validaciones realizadas

- ✅ Micro-spec creada (`doc/micro-specs/2026-05-13-irg_tfm_acta_documento.md`).
- ✅ Estructura del módulo completa: modelos, wizard, PDF generator, vistas XML, ACL, tests.
- ✅ Generación de PDF válida con datos de prueba.
- ✅ Attachment registrado para auditoría.
- ✅ Descarga funcional desde Odoo.
- ✅ Herencia correcta en `op.student` sin conflictos.

## Instrucciones de instalación

```bash
# Instalar módulo
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_tfm_acta_documento \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar módulo
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_tfm_acta_documento \
    --stop-after-init --db_host=pgodoo_latest

# Ejecutar tests
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -m irg_tfm_acta_documento \
    --test-tags=irg_tfm_acta_documento --db_host=pgodoo_latest
```

## Próximos pasos opcionales (futura evolución)

1. Integración con firma digital (`openpyxl` + certificado).
2. Plantillas PDF interactivas (formularios rellenables).
3. Versioning/borradores del acta.
4. Notificaciones automáticas a secretaría.
5. Exportación a Excel con auditoría.

---

**Estado:** Completado y listo para merge.  
**Responsable:** Equipo IRG.  
**Validado por:** Santiago Borges Rodríguez.
