# Plan — irg-admission-unimarconi-mail

## Objetivo

En la ficha de una admisión cuyo lote empieza por `MO`, un botón abre el
compositor de correo con la plantilla de iRG. El botón del mensaje lleva a
`https://oficialidad.institutoraimongaja.com`. El formulario cumplimentado
sigue entrando por el webhook de oficialidad como `matricula-unimarconi`.

Diseño aprobado: `docs/superpowers/specs/2026-10-15-irg-admission-unimarconi-mail-design.md`.

Plan de implementación: `docs/superpowers/plans/2026-10-15-irg-admission-unimarconi-mail.md`.

Módulo nuevo: `addons-extra/extrairg/irg_admission_unimarconi_mail`
(`16.0.1.0.0`, depende de `openeducat_admission` y `mail`). Sin modelos
nuevos. No se modifican `irg_student_oficialidad_documents` ni
`irg_student_oficialidad_webhook`.

## Clasificación

- Clase: `full`.
- Tier: `complex` (más de cinco archivos: modelo, vista, plantilla, logo y pruebas).
- Jev intake: `skipped` (`http_error`). `effective_class_binding` es falso.
  La clase la fija esta política.
- Security Advisor: no. No hay autenticación, secreto, migración,
  concurrencia, despliegue ni borrado histórico.

## jev_intake

```json
{
  "status": "skipped",
  "skipped_reason": "http_error",
  "model": null,
  "mission_class": null,
  "mission_class_confidence": null,
  "mission_class_binding": false,
  "exceeds_simple_limits": false,
  "exceeds_simple_noul": null,
  "needs_security_advisor": false,
  "security_noul": null,
  "security_keyword_hit": false,
  "effective_class": null,
  "effective_class_binding": false
}
```

## Criterios de aceptación

1. En una admisión con lote `MO`, el botón se ve en borrador y en el resto de estados.
2. En una admisión con lote `MP` o `MB`, el botón no se ve y la acción no abre el compositor.
3. Sin correo, el compositor no se abre y se pide el correo.
4. Con correo, el compositor sale con el asunto, el saludo, el nombre del curso, el remitente académico y el botón hacia `https://oficialidad.institutoraimongaja.com`.
5. Tras enviar, el mensaje queda en el chatter y se puede enviar otra vez.
6. Los módulos de documentos y webhook de oficialidad no cambian.
7. Las pruebas del módulo pasan, y el E2E de la vista pasa en la validación.

## E2E

El diff toca `views/op_admission_views.xml`. El check `e2e_testsprite` es
obligatorio. `projectPath` es el directorio del módulo, nunca la raíz del
repositorio.

## Roles

| Rol | Responsabilidad |
| --- | --- |
| Orquestador | Plan y clasificación |
| Coder | TDD del módulo |
| Reviewer | Revisión del código, la vista, la plantilla y las pruebas |
| Validator | Repite los checks y emite `verification.json` |
| E2E tester | `e2e_testsprite` contra el runtime local |
| Documenter | Uso, limitaciones y changelog tras la validación |
