# IRG Forum Web Editor Save Guard

1. Titulo corto
- Guard rail para guardado de contenido en forum.post desde web editor.

2. Resumen objetivo
- Evitar errores 500 al crear o editar mensajes del foro cuando llega HTML mal formado.
- Sanitizar y aplicar fallback seguro para que la operacion no tumbe la peticion.

3. Motivo / justificacion
- El crash ocurre en una ruta de negocio critica (publicacion/edicion de foro).
- Se implementa en modulo extra para no tocar core Odoo ni modulos de terceros.

4. Alcance exacto
- Modelo: forum.post.
- Campos protegidos en create/write: content, description, body.
- Sin cambios de vistas ni assets.

5. Diseno tecnico
- Heredar forum.post en modulo irg_forum_web_editor_save_guard.
- En create/write:
  - Intento 1: html_sanitize para campos texto objetivo.
  - Intento 2 (fallback si falla): escapar texto y convertir saltos de linea a <br/>.
- Mantener super() como punto final de persistencia.

6. Dependencias
- website_forum.

7. Backwards-compatibility / migracion
- No hay cambios de esquema ni migracion de datos.
- Comportamiento compatible: solo normaliza contenido invalido.

8. Casos de prueba / criterios de aceptacion
- Crear post con contenido valido: guarda sin cambios funcionales.
- Editar post con contenido problematico: no retorna 500.
- Verificar que el contenido sigue renderizando en la vista del foro.

9. Rollback plan
- Desinstalar modulo irg_forum_web_editor_save_guard o revertir commit.
- Actualizar lista de apps y reiniciar servicios via pipeline.

10. Estimacion y responsable
- Estimacion: 1 hora.
- Responsable: GitHub Copilot + equipo IRG.
