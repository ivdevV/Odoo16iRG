{
    "name": "iRG Gradebook Moodle Routing",
    "version": "16.0.1.0.0",
    "category": "Website/eLearning",
    "summary": "Routing de cursos y actividades Moodle para la libreta",
    "author": "iRG",
    "depends": ["irg_gradebook_moodle_wizard"],
    "data": [
        "security/ir.model.access.csv",
        "views/moodle_routing_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
