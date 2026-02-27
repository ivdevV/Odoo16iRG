{
    "name": "IRG Course Portal Tiles",
    "version": "16.0.1.0.0",
    "summary": "Add course-level portal tiles (Calendar, Practicas) and TFM link",
    "category": "Website",
    "author": "iRG",
    "license": "LGPL-3",
    "depends": ["isep_website_custom", "openeducat_web"],
    "data": [
        "views/irg_course_portal_tiles_views.xml",
        "views/tfm_views.xml",
        "views/tfm_page_fallback.xml",
        "views/assets.xml",
    ],
    "installable": True,
    "application": False,
}
