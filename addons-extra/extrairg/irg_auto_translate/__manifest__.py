{
    "name": "IRG Auto Translate (skeleton)",
    "version": "16.0.1.0.0",
    "summary": "Skeleton for automatic translation of OpenEduCat records",
    "description": "Adds translation support for op.subject and a batched wizard/cron to run translations.",
    "category": "Tools",
    "depends": ["base", "website", "openeducat_core"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "data/ir_config_parameter.xml",
        "data/ir_cron.xml",
        "wizard/translate_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "AGPL-3",
}
{
    "name": "IRG Auto Translate",
    "version": "16.0.1.0.0",
    "summary": "Auto-translate OpenEduCat and website content via DeepL/Google",
    "category": "Tools",
    "author": "IRG",
    "website": "https://institutoraimongaja.example",
    "license": "OPL-1",
    "depends": [
        "website",
        "openeducat_core",
        "irg_language_nav"
    ],
    "data": [
        "data/ir_config_parameter.xml",
        "data/cron.xml",
    ],
    "installable": True,
    "application": False,
}
