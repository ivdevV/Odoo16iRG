{
    "name": "iRG Gradebook Moodle Mapping Admin",
    "version": "16.0.1.0.0",
    "category": "Website/eLearning",
    "summary": "Administración del mapeo jerárquico de Moodle",
    "author": "iRG",
    "depends": ["irg_gradebook_moodle_routing"],
    "data": [
        "security/ir.model.access.csv",
        "views/moodle_mapping_admin_views.xml",
        "views/mapping_import_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
