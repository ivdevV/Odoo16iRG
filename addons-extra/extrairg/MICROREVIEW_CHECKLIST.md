Microreview Checklist — Odoo Modules (pre-merge)

Objetivo
- Reducir fallos de instalación/upgrade y errores de runtime por XML/QWeb, assets o payloads mal validados.

Checklist (marcar todo antes de merge)

1) Scaffolding y manifest
- [ ] El módulo está en `addons-extra/extrairg` y usa prefijo `irg_`.
- [ ] `__manifest__.py` tiene `depends` correctos y mínimos.
- [ ] El orden de `data` es correcto (security antes de vistas que dependen de permisos).
- [ ] `installable: True` y licencia definida.

2) Modelos y seguridad
- [ ] Campos nuevos definidos con tipos correctos y `copy=False` cuando aplica.
- [ ] Si hay JSON en `Text`, hay validación de estructura en backend.
- [ ] Si hay `t-raw`, el HTML se sanitiza previamente.
- [ ] Si se crean modelos nuevos, existe `security/ir.model.access.csv`.

3) XML/QWeb (bloque crítico)
- [ ] No hay atributos XML con namespace no declarado (ej.: `x-on:click`, `x-bind:class`).
- [ ] XPaths de herencia son estables y apuntan a anclas confiables.
- [ ] Si se reemplaza un bloque core, existe fallback funcional.
- [ ] El archivo XML abre/cierra etiquetas correctamente y sin duplicados.

4) Frontend y assets
- [ ] Librerías externas declaradas en `web.assets_frontend`.
- [ ] Inicialización de librerías con guardas defensivas (`if (window.lib)`).
- [ ] No hay JS inline frágil que dependa de sintaxis conflictiva con XML.

5) Pruebas mínimas de release
- [ ] Instalación limpia del módulo (`-i <module>`).
- [ ] Upgrade del módulo (`-u <module>`).
- [ ] Verificación manual del flujo principal en backend y frontend.
- [ ] Confirmado: sin `RPC_ERROR`, sin `XMLSyntaxError`, sin errores JS en consola.

Evidencia requerida en PR
- [ ] Captura o log corto de instalación/upgrade exitosa.
- [ ] Captura del flujo funcional principal.
- [ ] Checklist marcada en la descripción de la PR.
