# Misión: Habilitar Edición de Bloque de Código en Destacado eLearning (codeview)

## Alcance
El usuario indica que en la sección destacada de eLearning (configurada en `op.course`), teoricamente se puede inyectar bloques de código (aparece la opción en el editor enriquecido del campo HTML) pero al intentar escribir o poner algo dentro de la caja de código, el editor de Odoo no le deja interactuar correctamente.
Esto es debido a las limitaciones y bugs nativos de la barra del editor de Odoo 16 cuando se trabaja en modo visual con bloques de código (`<pre><code>`).

Para solucionar esto de manera limpia y robusta, se propone habilitar la opción `codeview` en el editor del campo HTML `irg_featured_section_body`. Al activar `'codeview': true` en el XML, aparecerá el botón `</>` en la barra de herramientas del editor, permitiendo al usuario cambiar a la vista HTML de código fuente e inyectar bloques de código fuente HTML directamente sin sufrir los bugs del cursor en el editor visual.

## Clasificación de Complejidad
- **Tier**: `trivial`
- **Justificación**: Afecta a un solo archivo XML de vista (`op_course_views.xml`) para añadir la opción `'codeview': true` en las opciones del widget `html`. No se introduce nueva lógica ni hay riesgos de seguridad, concurrencia o integridad de datos.
- **Modelos**:
  - Plan: Gemini 3.5 Flash (High) (Orquestador principal)
  - Implementación: Gemini 3.5 Flash (High) (Tier trivial)
  - Validación: Gemini 3.5 Flash (High)
  - Documentación: Gemini 3.5 Flash (High)

## Fases de Desarrollo

### 1. Plan
- Investigar la definición de las vistas del curso `op.course` en el módulo `irg_course_elearning_featured_section`.
- Diseñar la adición del atributo `options="{'safe': True, 'codeview': True}"` en la vista `op_course_views.xml`.

### 2. Implementación
- Modificar el campo `irg_featured_section_body` en la vista XML.

### 3. Validación
- Realizar pruebas de compilación y parsing XML localmente.
- Ejecutar test unitarios/integración en el contenedor local de Odoo si aplica, o realizar validación visual subiendo el docker y confirmando el comportamiento.

### 4. Documentación
- Actualizar el changelog y la base de conocimiento si corresponde.
