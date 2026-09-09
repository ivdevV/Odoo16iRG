# Plan — canal eLearning TFM Online

## Alcance

Corregir el flujo TFM cuando la matrícula exacta es Online, especialmente para
lotes reales como `MOPCONL2606`:

- permitir configurar `Convocatorias TFM` en las categorías del canal Online;
- resolver el canal Online aunque el clon conserve el enlace al HomeClass pero
  falte el enlace directo inverso en el HomeClass;
- mostrar en el portal el acceso al canal Online efectivo;
- mantener intacto el comportamiento HomeClass y cerrar el acceso cuando la
  familia de canales es ambigua o inválida.

Base: `2eda902239b45b16ec504d160ef6668d24fabc0d` (`origin/Dev_iRG`).

## Clasificación y capacidad

Misión completa, tier `standard`: bugfix localizado en vista eLearning, routing
de dos modelos existentes y pruebas. El flujo web y el filtrado por convocatoria
tienen impacto de autorización, por lo que se solicita Security Advisor antes de
modificar código funcional.

## Conocimiento consultado

- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`
- `.agents/knowledge/odoo_development_modding/artifacts/irg_elearning_url_slide.md`
- `.agents/knowledge/odoo_development_modding/artifacts/irg_campus_workshops_portal_customization.md`

Se mantendrá el addon independiente `irg_tfm_convocatorias`; no se modificarán
los addons `irg_course_convocatorias_v2`, `website_slides` ni OpenEduCat.

## Criterios de aceptación

1. `MOPCONL2606` se interpreta como Online y resuelve el clon de su canal TFM.
2. Un enlace directo HomeClass → Online válido sigue siendo prioritario.
3. Si falta ese enlace directo, un único clon Online que apunta al HomeClass se
   usa como recuperación segura; cero o varios candidatos cierran el acceso.
4. La vista Online permite ver y editar `Convocatorias TFM` en categorías, no en
   materiales.
5. El portal genera el enlace hacia el canal Online efectivo para el propietario
   con convocatoria activa.
6. HomeClass continúa usando el canal base y no se amplían permisos de usuarios
   externos.
7. Solo usuarios internos pueden modificar `irg_tfm_convocation_ids`, incluso si
   una llamada evita la interfaz normal.

## Implementación y TDD

El RED de runtime Odoo no es viable: la política del repositorio exige
`docker-compose.local.yml` y el usuario prohibió ejecutar Docker en este equipo.
Antes del código de producción se añadirán casos Odoo que reproduzcan el lote
real, el enlace inverso único y la ambigüedad, además de un contrato estático de
vista/enrutamiento que debe fallar contra el código actual. La alternativa GREEN
será el validador estático, parseo XML, `compileall` con caché externa y revisión
del diff; no se afirmará ejecución de tests Odoo.

## Archivos funcionales previstos

- `models/slide_channel.py`
- `views/slide_tfm_views.xml`
- `tests/test_tfm_elearning.py`
- `__manifest__.py`
- `missions/irg-tfm-convocatorias/artifacts/static_validator.py`

## Gates

1. Security Advisor: `[YES]`, condicionado a selección no transitiva, fallback
   inverso único y protección server-side de la edición de convocatorias.
2. RED alternativo documentado.
3. Implementación mínima y GREEN estático.
4. Review independiente de código.
5. Validación independiente y `verification.json`.
6. Documentación y changelog.
7. Comprobación final de Git.

`e2e_testsprite` se activa por el cambio XML/web, pero se registrará `skipped`
porque necesita el runtime local Docker expresamente prohibido. No habrá commit,
push ni PR sin una autorización nueva y específica.
