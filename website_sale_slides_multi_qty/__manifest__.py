# Copyright 2025 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Website Sale Slides Multi Qty",
    "version": "17.0.1.0.0",
    "category": "Website/eLearning",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/e-learning",
    "license": "AGPL-3",
    "depends": ["website_sale_slides_order_line_link", "base_vat"],
    "data": [
        "data/mail_template_data.xml",
        "views/slide_channel_partner_views.xml",
        "views/slide_channel_views.xml",
        "views/website_slides_templates_course.xml",
        "views/website_slides_templates_homepage.xml",
    ],
    "installable": True,
    "assets": {
        "web.assets_frontend": [
            "website_sale_slides_multi_qty/static/src/js/*.js",
        ],
        "web.assets_tests": [
            "website_sale_slides_multi_qty/static/tests/tours/*.js",
        ],
    },
}
