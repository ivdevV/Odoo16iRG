# iRG Quiz Auto-Scoring

## Descripción
Módulo de extensión para Odoo 16 que automatiza el cálculo y asignación de puntajes en surveys/cuestionarios de tipo Quiz o Examen.

## Funcionalidades

### 1. Distribución automática de puntajes
Cuando un survey de tipo Quiz/Examen se crea sin puntajes en sus preguntas, este módulo puede distribuir automáticamente 100 puntos de forma equitativa entre todas las preguntas.

**Ejemplo:**
- Survey con 5 preguntas sin puntaje
- Cada pregunta recibe automáticamente: 100 / 5 = **20 puntos**

### 2. Auditoría de cambios
Todos los cambios realizados se registran en el chatter del survey para auditoría completa:
- Fecha y hora de la acción
- Usuario que ejecutó la acción
- Número de preguntas configuradas

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

## Modelo heredado

### `survey.survey` (Survey/Cuestionario)
- **Nuevo método:** `action_auto_score_quiz()`
  - Distribuye puntajes equitativamente entre preguntas
  - Registra la acción en auditoría
  - Compatible únicamente con surveys de tipo: `quiz`, `exam`, `cert`
  
- **Métodos auxiliares:**
  - `_log_auto_score_action(notes)`: Registra acciones en auditoría (chatter)

---

## Seguridad y Permisos

El módulo utiliza los permisos estándar de `survey.survey`:
- **Lectura**: Todos los usuarios con acceso a surveys
- **Escritura**: Solo gerentes ERP
- **Acción**: Solo gerentes ERP pueden ejecutar auto-scoring

---

## Casos de uso

### Caso 1: Nueva encuesta/quiz de examen
Un instructor crea un survey de tipo "Quiz" con 20 preguntas sin puntajes. Al clic de un botón, recibe 5 puntos cada una (100/20).

### Caso 2: Correcciones uniformes
Si los puntajes se necesitan asignar de forma uniforme, el módulo distribuye 100 puntos proporcionalmente.

---

## Limitaciones y consideraciones

- ✓ Solo afecta surveys de tipo `quiz`, `exam` o `cert`
- ✓ Solo modifica preguntas **SIN puntaje** (points = 0 o NULL)
- ✓ Si el survey ya tiene todos los puntajes asignados, rechaza la acción
- ✓ No afecta encuestas de otros tipos (feedback, assessment, etc.)

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
- Puntaje asignado por pregunta

Los logs se almacenan en:
- **Chatter del survey** (Odoo UI)
- **Logs de aplicación** (odoo.log)

---

## Dependencias

- `survey` (requerido, módulo estándar de Odoo)

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
