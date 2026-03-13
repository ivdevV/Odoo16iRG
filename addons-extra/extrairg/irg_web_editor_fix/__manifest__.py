{
    "name": "IRG Web Editor Fix",
    "summary": "Guard OdooEditor raw commands against invalid anchor methods",
    "version": "16.0.1.0.0",
    "category": "Website/Website",
    "author": "IRG",
    "license": "LGPL-3",
    "depends": [
        "web_editor",
        "website_forum"
    ],
    "data": [],
    "assets": {
        "web_editor.assets_wysiwyg": [
            "irg_web_editor_fix/static/src/js/odoo_editor_apply_raw_command_guard.js"
        ]
    },
    "installable": True,
    "application": False
}
