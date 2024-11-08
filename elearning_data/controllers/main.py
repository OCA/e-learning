# -*- coding: utf-8 -*-

from odoo.addons.website_slides.controllers.main import WebsiteSlides
from random import shuffle

class WebsiteSlides(WebsiteSlides):
    def _get_slide_quiz_data(self, slide):
        res = super()._get_slide_quiz_data(slide)
        for question_data in res.get('slide_questions'):
            shuffle(question_data['answer_ids'])
        return res