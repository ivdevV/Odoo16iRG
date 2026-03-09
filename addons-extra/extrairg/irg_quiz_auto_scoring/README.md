# iRG Quiz Auto-Scoring

## Descripción
Módulo de extensión para Odoo 16 que automatiza el cálculo y asignación de puntajes en cuestionarios.

## Funcionalidades

### 1. Distribución automática de puntajes
Cuando un cuestionario se crea sin puntajes en sus preguntas, este módulo puede distribuir automáticamente 100 puntos de forma equitativa entre todas las preguntas.

**Ejemplo:**
- Cuestionario con 5 preguntas sin puntaje
- Cada pregunta recibe automáticamente: 100 / 5 = **20 puntos**

### 2. Recálculo de resultados de estudiantes
Una vez distribuidos los puntajes, el módulo procesa todos los intentos (resultados) anteriores:
- Si la respuesta fue **correcta**: asigna el puntaje completo de la pregunta
- Si la respuesta fue **incorrecta**: asigna 0 puntos
- Recalcula el total y porcentaje de cada intento

### 3. Sincronización con boletín de calificaciones
Si el módulo `openeducat_grading` está instalado, los puntajes se sincronizan automáticamente con el boletín de calificaciones de los estudiantes.

---

## Instalación

```bash
# Ubicar en el servidor de Odoo
# addons-extra/extrairg/irg_quiz_auto_scoring/

# Instalar el módulo
odoo -u irg_quiz_auto_scoring -d <nombre_base_datos> --stop-after-init
```

---

## Uso

1. **Abrir un cuestionario** (`Educación > Cuestionarios > Cuestionarios`)
2. **Verifique el estado**: El cuestionario debe estar en estado "Draft" (Borrador) o "In-Progress"
3. **Haga clic en el botón** "🎯 Auto-calcular Puntajes"
4. **Confirme**: El sistema mostrará:
   - Número de preguntas configuradas
   - Puntaje asignado a cada pregunta
   - Número de intentos de estudiantes re-evaluados
   - Puntaje total del cuestionario

### Ejemplo de flujo:
```
Cuestionario: "Examen de Matemáticas"
┌─ 5 preguntas sin puntaje inicial
├─ Click "Auto-calcular Puntajes"
└─ Resultado:
   ✓ 5 preguntas → 20 puntos c/u
   ✓ 12 intentos de estudiantes → re-evaluados
   ✓ Puntaje total: 100 puntos
```

---

## Modelos heredados

### `op.quiz` (Cuestionario)
- **Nuevo método:** `action_auto_score_quiz()`
  - Distribuye puntajes
  - Procesa resultados
  - Sincroniza con gradebook
  
- **Métodos auxiliares:**
  - `_process_quiz_result(result)`: Recalcula un intento específico
  - `_sync_with_gradebook()`: Sincroniza con boletín
  - `_is_grading_module_installed()`: Verifica disponibilidad de módulo
  - `_log_auto_score_action(notes)`: Registra acciones en auditoría

### `op.quiz.result` (Intento/Resultado)
- **Nuevo método:** `recalculate_score()`
  - Recalcula puntaje de un intento individual

---

## Seguridad y Permisos

El módulo utiliza los permisos estándar de `openeducat_quiz`:
- **Lectura**: Todos los usuarios con acceso a cuestionarios
- **Escritura**: Solo gerentes y docentes
- **Acción**: Solo gerentes ERP pueden ejecutar auto-scoring

---

## Casos de uso

### Caso 1: Nueva plantilla de examen
Un profesor crea un template de 20 preguntas sin puntajes. Al clic de un botón, recibe 5 puntos cada una (100/20).

### Caso 2: Corrección de exámenes previos
Si los puntajes se asignan después de que estudiantes ya intentaron el cuestionario, el módulo re-evalúa todos los intentos automáticamente.

### Caso 3: Integración con boletín
Los puntajes actualizados se reflejan automáticamente en el boletín de calificaciones de cada estudiante.

---

## Limitaciones y consideraciones

- ✓ Solo afecta preguntas **SIN puntaje** (mark = 0 o NULL)
- ✓ Requiere que el cuestionario esté en estado "Draft" o "In-Progress"
- ✓ Si el cuestionario ya tiene puntajes en alguna pregunta, rechaza la acción
- ✓ No afecta cuestionarios en estado "Done" o "Cancel"
- ✓ La sincronización con gradebook es opcional (depende de openeducat_grading)

---

## Desinstalación y Rollback

### Desinstalar el módulo
```bash
odoo -u irg_quiz_auto_scoring -d <db> --uninstall-module=irg_quiz_auto_scoring --stop-after-init
```

### Restaurar base de datos a un punto anterior
```bash
# Si es necesario revertir cambios, usar backup:
pg_restore -d <db> backup_previo.dump
```

---

## Auditoría y Logs

Cada ejecución de auto-scoring registra:
- Fecha y hora
- Usuario que ejecutó la acción
- Número de preguntas configuradas
- Número de intentos procesados
- Puntaje asignado por pregunta

Los logs se almacenan en:
- **Chatter del cuestionario** (Odoo UI)
- **Logs de aplicación** (odoo.log)

---

## Dependencias

- `openeducat_quiz` (requerido)
- `openeducat_grading` (opcional, para sincronización de boletín)

---

## Changelog

### Versión 16.0.1.0
- ✓ Distribución automática de puntajes
- ✓ Recálculo de resultados de estudiantes
- ✓ Sincronización con boletín (opcional)
- ✓ Botón de acción en formulario de cuestionario
- ✓ Auditoría en chatter

---

## Soporte y contacto

Para reportar bugs o solicitar mejoras, contactar al equipo de desarrollo iRG.

---

**Última actualización:** Marzo 9, 2026  
**Versión:** 16.0.1.0  
**Autor:** iRG Inc
