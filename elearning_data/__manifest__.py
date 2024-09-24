# -*- coding: utf-8 -*-
# © 2024 Open Net Sarl
# License OPL-1 or later (https://www.odoo.com/documentation/17.0/legal/licenses.html#odoo-apps).

{
    "name": "eLearning Data",
    "summary": "An module that import data into eLearning",
    "category": "Uncategorized",
    "author": "Open Net Sàrl, Adam Bonnet <adambonnet0@gmail.com>",
    "depends": [
        "website_slides",
        ],
    "version": "17.0.1.0",
    "auto_install": False,
    "website": "https://www.open-net.ch",
    "license": "OPL-1",
    "data": [
        # Views
        "views/slide_slide.xml",
        # Data
        "data/res_lang.xml",
        "data/slide_channel.xml",
                # Getting Started
        "data/slide_slide_getting_started.xml",
        "data/slide_question_getting_started.xml",
                # Advanced Use
        "data/slide_slide_advanced_use.xml",
        "data/slide_question_advanced_use.xml",
        # Security
        "security/ir.model.access.csv",
        ],
    "assets": {},
    "installable": True,
}
