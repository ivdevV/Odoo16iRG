# Ejecución — canal eLearning TFM Online

## 2026-09-09 — diagnóstico y preparación

- Evidencia visual: el modal `Secciones Online` usa una vista distinta a las
  categorías nativas y no expone `irg_tfm_convocation_ids`.
- Evidencia de código: `irg_course_convocatorias_v2` define
  `irg_online_section_ids` con tree/form propios y readonly; la vista TFM actual
  solo extiende `irg_native_section_ids`.
- Evidencia de routing: `_irg_tfm_family_channels()` y
  `_irg_tfm_effective_channel()` dependen del puntero directo
  `base.irg_online_channel_id`, aunque el repositorio permite clones que solo
  conservan `irg_homeclass_channel_id`.
- El parser puro devuelve `('ONL', 2606)` para `MOPCONL2606`; el corte del lote no
  es la causa.
- Worktree limpio, rama `codex/tfm-online-elearning-fix`, base y
  `origin/Dev_iRG` en `2eda902239b45b16ec504d160ef6668d24fabc0d`.
- Docker no se ejecutará por instrucción explícita del usuario.

## TDD

Security Advisor: `[YES]`. Condiciones incorporadas al plan:

- validar que el puntero directo Online regresa al mismo HomeClass;
- usar un único enlace inverso exacto como fallback, nunca expansión transitiva;
- con cero o varios candidatos, fallar cerrado;
- proteger en servidor la escritura de `irg_tfm_convocation_ids`;
- en el espejo Online mantener bloqueados creación, borrado, lotes, fechas,
  publicación, canal y jerarquía.

RED alternativo ejecutado antes del código de producción:

- comando: `static_validator.py` con el Python integrado de Codex;
- resultado: exit 1;
- causa esperada: faltan el fallback inverso acotado, la protección server-side
  y el editor Online estrecho;
- evidencia: `artifacts/red-static.txt`.

Implementación mínima:

- `_irg_tfm_online_channel()` valida el puntero directo y recupera como máximo
  dos candidatos inversos para aceptar solo uno;
- `_irg_tfm_family_channels()` y `_irg_tfm_effective_channel()` usan esa selección;
- `slide.slide.create/write` rechazan cambios externos de convocatorias;
- la vista Online sustituye el espejo calculado por el One2many relacionado,
  filtrado a categorías, sin creación/borrado y con solo convocatoria editable;
- versión elevada a `16.0.1.0.4`.

GREEN del codificador:

- `static_validator.py`: 13/13 grupos, 75 tests y 39 contratos;
- `compileall`: exit 0 con caché externa;
- `git diff --check`: exit 0;
- XPath nuevo: una coincidencia exacta en la vista padre.

Review independiente ronda 1: NO APROBADO por un P2. Un autorenlace podía
seleccionar HomeClass como canal Online. Se reabre Implementación con dos casos
RED adicionales antes de corregir.

RED de autorenlace: el validador reconoció 77 pruebas y falló únicamente el
contrato `online_inverse_fallback_is_exact_and_bounded`. Se añadió el cambio
mínimo: rechazar el directo cuando coincide con la base y excluir la base de la
búsqueda inversa.

GREEN ronda 2: 13/13 grupos, 77 pruebas estructurales, 39 contratos, compileall
y diff-check en exit 0.

Review independiente ronda 2: APROBADO, sin nuevos hallazgos.

## Validación independiente

Estado final: `passed`.

- validador estático: 13/13 grupos, 77 pruebas estructurales y 39 contratos;
- `compileall`: exit 0 con caché externa y limpieza confirmada;
- manifest y siete XML: válidos;
- XPath Online: una coincidencia exacta en la vista padre;
- `git diff --check`: exit 0;
- alcance limitado al addon TFM y a sus artefactos de misión;
- pruebas Odoo y TestSprite: `skipped` con justificación porque el usuario
  prohibió expresamente ejecutar Docker en este ordenador.

Evidencia y contrato de cierre: `verification.json` y `artifacts/validation-*`.

## Documentación

- documentación del módulo actualizada a 16.0.1.0.4;
- changelog ampliado con la corrección Online;
- añadido conocimiento reutilizable sobre resolución segura de clones eLearning
  y edición estrecha de categorías espejadas.
