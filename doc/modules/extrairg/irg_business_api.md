# irg_business_api

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `irg_course_convocatorias_v2`, `irg_online_subject_opening`, `openeducat_admission`

---

## ¿Qué hace este módulo?

Expone un modelo de comandos `irg.api.operation` para que un agente (Lisa/MCP) lea datos académicos y cree o edite slides y secciones eLearning en borrador, sin `execute_kw` genérico ni métodos arbitrarios.

## Funcionalidades principales

- Lecturas paginadas de periodos, cursos, lotes, asignaturas, estructura eLearning, admisión, aperturas, acceso Campus y 360 mínimo.
- Lecturas opcionales de gradebook y estado Moodle si esos modelos existen (no son `depends`).
- Escrituras en dos pasos: preview → Approve. Borradores de artículo no publicados; publicar/despublicar son operaciones separadas.
- Idempotencia por `(usuario, código, idempotency_key)` y auditoría en snapshots.

## Vistas y UI

- `views/api_operation_views.xml` — árbol, formulario y búsqueda. Botones Approve/Reject. Sin borrado en UI (`delete="0"`).
- Menú raíz **IRG Business API → Operations** (grupo Business API User o Settings).

## Seguridad

- Grupo `group_irg_business_api_user`.
- `write()` y `unlink()` del modelo siempre denegados. No usar flags de contexto para saltarse esa guarda.
- Payload máximo 64 KiB; HTML 32k; página máxima 100; entorno `production` rechazado.

## Instalación / Actualización

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf -d <dbname> \
  -i irg_business_api --stop-after-init
```

Contrato: `addons-extra/extrairg/irg_business_api/doc/api-contract.md`.
Pruebas: `--test-tags /irg_business_api`.

## Limitaciones

Fases 3–6 (clonación Online, matrícula, sync Moodle de escritura, encuestas de escritura, adjuntos) no están implementadas. Desinstalar no revierte escrituras ya aplicadas.
