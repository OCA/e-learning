# © 2024 Open Net Sarl


{
    "name": "eLearning - Data",
    "summary": "An module that import data into eLearning",
    "category": "Uncategorized",
    "author": "Open Net Sàrl, Adam Bonnet <adambonnet0@gmail.com>, Odoo Community Association (OCA)",  # noqa: E501
    "depends": [
        "elearning_url_slide_slide",
        "elearning_shuffle_slide_answer",
        "website_slides",
    ],
    "version": "17.0.0.1.0",
    "auto_install": False,
    "website": "https://github.com/OCA/e-learning",
    "license": "AGPL-3",
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
    ],
    "assets": {},
    "installable": True,
}
