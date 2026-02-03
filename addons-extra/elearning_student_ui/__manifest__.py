{
    "name": "eLearning Student UI — Remove Internal Management",
    "version": "16.0.1.0.0",
    "summary": "Remove internal management options from student UI using frontend JS",
    "category": "Website",
    "author": "IGR Custom",
    "website": "https://example.com",
    "license": "LGPL-3",
    "depends": [
        "web",
        "website",
    ],
    "data": [
        # Only asset registration, no template patches
    ],
    "assets": {
        "web.assets_frontend": [
            "elearning_student_ui/static/src/js/elearning_student_ui.js",
        ],
    },
    "installable": True,
    "application": False,
}
