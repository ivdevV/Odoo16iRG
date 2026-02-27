{
    "name": "IRG Course Portal Tiles",
    "version": "16.0.1.0.0",
    "summary": "Add course-level portal tiles (Calendar, Practicas) and TFM link",
    "category": "Website",
    "author": "iRG",
    "license": "LGPL-3",
    "depends": ["isep_website_custom", "irg_elearning_restrictions"],
    "data": [
        "views/irg_course_portal_tiles_views.xml",
        "views/tfm_views.xml",
        "views/override_elearning_templates.xml",
    ],
    "installable": True,
    "application": False,
}
