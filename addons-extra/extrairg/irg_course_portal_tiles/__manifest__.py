{
    "name": "IRG Course Portal Tiles",
    "version": "16.0.1.0.0",
    "summary": "Add course-level portal tiles (Calendar, Practicas) and TFM link",
    "category": "Website",
    "author": "iRG",
    "license": "LGPL-3",
    "depends": ["isep_website_custom", "openeducat_web", "website_helpdesk"],
    "data": [
        "views/irg_course_portal_tiles_views.xml",
        "views/user_profile_openeducat_label_override.xml",
        "views/tfm_views.xml",
        "views/tfm_page_fallback.xml",
        "views/helpdesk_page.xml",
        "views/helpdesk_overrides.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "irg_course_portal_tiles/static/src/scss/irg_tiles.scss",
            "irg_course_portal_tiles/static/src/js/help_chatbot.js",
            "irg_course_portal_tiles/static/src/js/menu_patch.js"
        ]
    },
    "installable": True,
    "application": False,
}
