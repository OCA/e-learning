# © 2024 Open Net Sarl


from odoo import fields, models


class SlideSlide(models.Model):
    _inherit = "slide.slide"

    elearning_url_ids = fields.One2many(
        comodel_name="elearning.url", inverse_name="slide_id", string="eLearning URLs"
    )

    url = fields.Char(
        compute="_compute_elearning_url", store=False, required=False, readonly=True
    )

    def _compute_elearning_url(self):
        lang = self.env.context.get("lang") or self.env.user.lang
        fallback_lang_code = "fr_FR"
        for record in self:
            elearning_url_ids = record.elearning_url_ids.filtered(
                lambda r: r.lang.code == lang
            )
            if not elearning_url_ids:
                elearning_url_ids = record.elearning_url_ids.filtered(
                    lambda r: r.lang.code == fallback_lang_code
                )
            record.url = elearning_url_ids.url
