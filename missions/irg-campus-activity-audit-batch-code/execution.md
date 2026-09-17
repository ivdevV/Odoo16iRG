# execution.md — irg-campus-activity-audit-batch-code

- 2026-09-17: Prod no cruza alumnos. Logs: `call_button` 11:30:40 UTC, 41 queries, 3.7s, HTTP 200. Sin traceback. SELECT: emails existen; `op.course.code=TG`, `op.batch.code=DITGHC2606`. El parser extraía el lote y lo comparaba con el curso.
