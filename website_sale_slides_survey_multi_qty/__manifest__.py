# Copyright 2025 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Website Sale Slides Survey Multi Qty",
    "version": "17.0.1.0.0",
    "category": "Website/eLearning",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/e-learning",
    "license": "AGPL-3",
    "depends": ["website_sale_slides_multi_qty", "website_slides_survey"],
    "data": [
        "report/survey_templates.xml",
        "views/survey_templates.xml",
        "views/survey_user_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_sale_slides_survey_multi_qty/static/src/xml/website_slides_fullscreen.xml",
        ],
    },
}
