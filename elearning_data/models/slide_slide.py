# -*- coding: utf-8 -*-
# © 2024 Open Net Sarl
# License OPL-1 or later (https://www.odoo.com/documentation/17.0/legal/licenses.html#odoo-apps).

from odoo import models, fields


class SlideSlide(models.Model):
    _inherit = "slide.slide"

    elearning_url_ids = fields.One2many(
        comodel_name="elearning.url", inverse_name="slide_id", string="eLearning URLs"
    )

    url = fields.Char(compute="_elearning_compute_url", store=False, required=False, readonly=True)   

    def _elearning_compute_url(self):
        lang = self.env.context.get("lang") or self.env.user.lang
        for record in self:
            fallback_lang_code = "fr_FR"
            elearning_url_ids = record.elearning_url_ids.filtered(
                lambda r: r.lang.code == lang
            )
            if not elearning_url_ids:
                elearning_url_ids = record.elearning_url_ids.filtered(
                    lambda r: r.lang.code == fallback_lang_code
                )
            record.url = elearning_url_ids.url
