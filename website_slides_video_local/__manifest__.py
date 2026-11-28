# Copyright 2026 Graeme Gellatly <gdgellatly@gmail.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "eLearning: Self-Hosted Video",
    "summary": "Upload a video file on a course lesson, instead of YouTube, "
    "Vimeo or Google Drive",
    "version": "19.0.1.0.0",
    "category": "Website/eLearning",
    "author": "Graeme Gellatly, Odoo Community Association (OCA)",
    "maintainers": ["gdgellatly"],
    "website": "https://github.com/OCA/e-learning",
    "license": "LGPL-3",
    "development_status": "Beta",
    "depends": ["website_slides"],
    "data": [
        "views/slide_slide_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_slides_video_local/static/src/js/slides_course_fullscreen_player.esm.js",
            "website_slides_video_local/static/src/xml/slides_fullscreen_video_local.xml",
        ],
    },
    "installable": True,
}
