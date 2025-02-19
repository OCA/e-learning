# Copyright 2025 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Website Sale Slides Multi Qty",
    "version": "15.0.1.0.0",
    "category": "Website/eLearning",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/e-learning",
    "license": "AGPL-3",
    "summary": "",
    "depends": ["website_sale_slides_order_line_link"],
    "data": [
        "data/mail_template_data.xml",
        "security/ir.model.access.csv",
        "views/slide_channel_partner_views.xml",
        "views/slide_channel_views.xml",
        "views/website_slides_templates_course.xml",
        "views/website_slides_templates_homepage.xml",
        "views/website_slides_templates.xml",
    ],
    "installable": True,
    "assets": {
        "web.assets_frontend": [
            "website_sale_slides_multi_qty/static/src/js/*.js",
        ],
    },
}
