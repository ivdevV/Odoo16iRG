# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "IRG MIS Builder Fix",
    "version": "16.0.1.0.1",
    "summary": (
        "Fixes KeyError: False when printing MIS reports caused by a "
        "stale move_lines_source reference after an Odoo module update."
    ),
    "author": "iRG",
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": ["mis_builder"],
    "data": [],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "auto_install": False,
}
