# Copyright 2025 Binhex - Adasat Torres de León
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Courses's Slides Require Previous Slides Completion",
    "summary": """If checked, the user has to complete previous slides before """
    """moving to the next one.""",
    "version": "16.0.1.0.0",
    "category": "Website/eLearning",
    "author": "Binhex, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/e-learning",
    "depends": ["web", "website_slides"],
    "data": [
        "views/slide_channel_views.xml",
        "views/website_slides_templates_course.xml",
        "views/website_slides_templates_lesson_fullscreen.xml",
        "views/website_slides_templates_lesson_embed.xml",
        "views/website_slides_templates_utils.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_slides_require_completion/static/src/js/*.js",
            "website_slides_require_completion/static/src/xml/*.xml",
        ],
    },
    "license": "AGPL-3",
    "maintainers": ["adasatorres"],
}
