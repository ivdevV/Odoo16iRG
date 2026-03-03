from odoo import fields, models


class IrgBlockingProcessService(models.AbstractModel):
    _name = "irg.blocking.process.service"
    _description = "IRG Blocking Process Status Service"

    def _module_operations_count(self):
        return self.env["ir.module.module"].sudo().search_count([
            ("state", "in", ("to install", "to upgrade", "to remove")),
        ])

    def _active_blocking_queries_count(self):
        self.env.cr.execute(
            """
            SELECT COUNT(*)
            FROM pg_stat_activity
            WHERE datname = current_database()
              AND state = 'active'
              AND pid <> pg_backend_pid()
              AND (
                    query ILIKE '%ir_module_module%'
                 OR query ILIKE '%button_immediate_install%'
                 OR query ILIKE '%button_immediate_upgrade%'
                 OR query ILIKE '%button_immediate_uninstall%'
                 OR query ILIKE '%ir_cron%'
              )
            """
        )
        return int(self.env.cr.fetchone()[0] or 0)

    def _long_running_queries_count(self, threshold_seconds=20):
        self.env.cr.execute(
            """
            SELECT COUNT(*)
            FROM pg_stat_activity
            WHERE datname = current_database()
              AND state = 'active'
              AND pid <> pg_backend_pid()
              AND now() - query_start > interval %s
            """,
            [f"{int(threshold_seconds)} seconds"],
        )
        return int(self.env.cr.fetchone()[0] or 0)

    def get_status(self):
        module_ops = self._module_operations_count()
        blocking_queries = self._active_blocking_queries_count()
        long_queries = self._long_running_queries_count()

        sources = []
        if module_ops:
            sources.append(f"module_operations:{module_ops}")
        if blocking_queries:
            sources.append(f"blocking_queries:{blocking_queries}")
        if long_queries:
            sources.append(f"long_queries:{long_queries}")

        return {
            "blocking": bool(sources),
            "sources": sources,
            "checked_at": fields.Datetime.to_string(fields.Datetime.now()),
        }
