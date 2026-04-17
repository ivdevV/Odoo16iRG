# Cambios requeridos en workflow n8n (Odoo 16)

## Objetivo
Evitar doble ejecución/bucle y alinear la integración con el módulo `irg_interactive_content`.

## Contexto de integración actual
El webhook desde Odoo se dispara **solo en alta real de PDF** (create de `slide.slide` con binario y `slide_category='document'`).
Aun así, en n8n hay ajustes necesarios para:
1) evitar inconsistencias de campos Odoo,
2) mapear el JSON interactivo esperado por frontend,
3) prevenir errores por PDF vacío.

---

## 1) Nodo `Odoo: Create Interactive` (obligatorio)

### Problemas detectados
- Se usa `slide_type` en vez de `slide_category`.
- No se marca el nuevo slide como interactivo.
- No se vincula con el slide original.
- No se guarda `x_interactive_json` (fuente del render interactivo).

### Cambios
En `fieldsToCreateOrUpdate.fields`, usar estos campos:

- `name`: `={{ $json.summary.substring(0, 50) }}`
- `slide_category`: `article`
- `channel_id`: `={{ $('Odoo: Get PDF').first().json.channel_id[0] }}`
- `html_content`: `={{ $json.content_html }}`
- `x_is_interactive`: `={{ true }}`
- `x_original_slide_id`: `={{ $json.original_id }}`
- `x_interactive_json`: `={{ JSON.stringify($json.interactive_payload) }}`
- `description`: `summary`

> Nota: dejar `slide_type` fuera. En Odoo 16 para `slide.slide` el campo correcto es `slide_category`.

---

## 2) Nodo `Format Data` (obligatorio)

### Problemas detectados
- `flashcards` sale como `front/back`, pero Odoo espera `term/definition`.
- `knowledge_check` no se transforma a `quiz` compatible.
- Falta objeto `interactive_payload` consolidado para `x_interactive_json`.

### Salida recomendada del nodo
Debe retornar:
- `content_html`
- `summary`
- `original_id`
- `channel_id`
- `interactive_payload` con estructura:
  - `mermaid_code: string`
  - `flashcards: [{ term, definition }]`
  - `content_html: string`
  - `quiz: [{ question, options, correct_answer }]`

### Fragmento sugerido (JS dentro de `Format Data`)
```javascript
const originalId = $("Webhook (Odoo Trigger)").first().json.body.id;
const channelId = $("Odoo: Get PDF").first().json.channel_id[0];

const flashcards = (d.flashcards || []).map((f) => ({
  term: f.front || "",
  definition: f.back || "",
}));

const quiz = (d.knowledge_check || []).map((q) => {
  const options = Array.isArray(q.options) ? q.options : [];
  const idx = Number.isInteger(q.correct_index) ? q.correct_index : -1;
  return {
    question: q.question || "",
    options,
    correct_answer: idx >= 0 && idx < options.length ? options[idx] : "",
  };
});

return {
  json: {
    content_html: fullHtml,
    summary: d.module_summary || "Sin resumen",
    original_id: originalId,
    channel_id: channelId,
    interactive_payload: {
      mermaid_code: d.mermaid_code || "",
      flashcards,
      content_html: fullHtml,
      quiz,
    },
  },
};
```

---

## 3) Nodo `Extract from File` (obligatorio)

### Problema detectado
Error intermitente: `The PDF file is empty, i.e. its size is zero bytes`.

### Cambios
Agregar un `IF` antes de `Convert to File` o antes de `Extract from File`:
- Condición: `document_binary_content` existe y longitud > 0.
- Si NO cumple:
  - ramificar a un nodo de fin controlado (log/alerta)
  - opcional: `Wait` 2-5s + reintento de `Odoo: Get PDF` una vez.

Expresión ejemplo:
```javascript
={{ !!$json.document_binary_content && $json.document_binary_content.length > 0 }}
```

---

## 4) Nodo `Odoo: Hide Original` (recomendado)

Mantener actualización de `is_published=false`, pero no tocar campos de contenido/binario.
Esto evita efectos colaterales innecesarios en el PDF original.

---

## 5) Reglas anti-bucle (resumen)

- El slide interactivo creado por n8n debe llevar:
  - `x_is_interactive=true`
  - `x_original_slide_id=<id original>`
  - `slide_category='article'`
- El original solo se oculta (`is_published=false`).
- No recrear/actualizar el original con binario desde n8n.

---

## 6) Contrato de datos Odoo ↔ n8n esperado

### Entrada webhook desde Odoo
```json
{
  "id": 123,
  "name": "Nombre del slide",
  "channel_id": 45
}
```

### Salida final hacia `Odoo: Create Interactive`
```json
{
  "summary": "...",
  "content_html": "...",
  "original_id": 123,
  "channel_id": 45,
  "interactive_payload": {
    "mermaid_code": "graph TD; A-->B;",
    "flashcards": [{ "term": "...", "definition": "..." }],
    "content_html": "...",
    "quiz": [{ "question": "...", "options": ["..."], "correct_answer": "..." }]
  }
}
```

---

## 7) Checklist rápida de validación

- [ ] Crear un PDF nuevo en Odoo dispara 1 ejecución en n8n.
- [ ] La ejecución crea 1 slide interactivo (`article`).
- [ ] El slide interactivo tiene `x_is_interactive=true`.
- [ ] El slide interactivo tiene `x_original_slide_id` al PDF original.
- [ ] El slide interactivo tiene `x_interactive_json` válido.
- [ ] El original queda oculto (`is_published=false`).
- [ ] No aparece error de PDF vacío; si aparece, la rama IF corta/reintenta.
