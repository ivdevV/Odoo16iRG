# AGENTS.md - Odoo16iRG

## Regla obligatoria de desarrollo

Todo desarrollo en este proyecto debe seguir siempre el flujo:

1. Plan
2. Implementacion
3. Validacion
4. Documentacion

Cada fase se delegara o ejecutara con el rol indicado, y los subagentes solo se lanzaran cuando llegue su fase correspondiente:

- Plan: lo realiza el agente principal, actuando como orquestador del trabajo.
- Implementacion: la realiza un subagente codificador usando la skill `Especialista en Desarrollo Odoo 16`.
- Validacion: la realiza un subagente testeador usando la skill `superpowers:verification-before-completion` como regla principal de evidencia antes de cierre. Cuando el cambio sea una feature, bugfix o cambio de comportamiento, tambien debera aplicar TDD con `superpowers:test-driven-development` siempre que sea viable.
- Documentacion: la realiza un subagente documentador despues de que el validador haya pasado los testeos. Usara la skill `documentation-writer` cuando aplique y documentara todos los cambios, modulos nuevos, configuracion, pruebas realizadas, criterios de uso y limitaciones conocidas. Si se crea o modifica un modulo `irg_*`, debera actualizar `doc/modules/extrairg/irg_<module>.md`. Tambien debera incluir un changelog claro y conciso al cierre.

## Politica de modelos por rol

Los modelos se elegiran segun el rol y la dificultad de la tarea. Si el modelo preferido no esta disponible, se usara el equivalente mas cercano en capacidad:

- Orquestador / Plan: usar el modelo de razonamiento mas capaz disponible. Preferido: `gpt-5.5` o equivalente superior.
- Codificador / Implementacion: usar un modelo fuerte de codigo. Preferido: `gpt-5.4` o equivalente adecuado cuando el plan este cerrado.
- Testeador / Validacion: usar un modelo fuerte en razonamiento y depuracion. Preferido: `gpt-5.4` o equivalente; puede escalar al modelo del orquestador si aparecen fallos complejos.
- Documentador / Documentacion: usar un modelo ligero. Preferido: `mini` o `nano`, salvo documentacion critica o arquitectura compleja.
- Security Advisor: usar un modelo de razonamiento alto cuando revise acciones con riesgo.

La validacion debe incluir, como minimo:

- Testeos unitarios o pruebas automatizadas adecuadas al cambio.
- Testeos a nivel Odoo ejecutados en un Odoo local usando `docker-compose.local.yml`.

Una vez realizados esos testeos, se notificara al usuario para que revise el resultado. No se subira nada a `Dev_iRG` en GitHub hasta recibir su OK explicito.

No se debe dar por terminado un cambio sin documentar que se ha seguido este flujo o explicar explicitamente por que una parte concreta no pudo ejecutarse.

## Perfil de seguridad para revisiones sensibles

Cuando una fase proponga comandos, cambios de archivos o acciones con riesgo de seguridad, integridad o perdida de datos, se usara el siguiente perfil de revision:

- Nombre: Security Advisor.
- Rol: experto estricto en seguridad y revisor de codigo.
- Criterio: verificar la seguridad de cambios de archivos, comandos shell y ejecuciones de herramientas antes de aprobarlos.
- Herramientas esperadas: lectura de archivos, listado de directorios, busqueda de texto y busqueda web si hiciera falta contexto.
- Estilo de decision: respuesta final obligatoria con `[YES] Reason: ...` o `[NO] Reason: ...`, siendo el veredicto la ultima linea.
- Reglas clave: ignorar urgencias retoricas, comprobar alcance, proteger datos valiosos como logs o historicos, preservar contratos funcionales, detectar APIs inexistentes o sintaxis imposible, comprobar que la justificacion coincide con el cambio real y rechazar operaciones destructivas o degradaciones no justificadas.
