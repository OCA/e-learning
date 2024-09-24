# © 2024 Open Net Sarl


from odoo import fields, models


class eLearningUrl(models.Model):
    _name = "elearning.url"

    lang = fields.Many2one(
        comodel_name="res.lang",
        string="Language",
        default=lambda self: self.env["res.lang"].search(
            [("code", "=", self.env.context.get("lang", self.env.user.lang))]
        ),
    )

    slide_id = fields.Many2one(comodel_name="slide.slide", string="Slide")

    url = fields.Char(string="URL")

    _sql_constraints = [
        (
            "unique_lang_slide_id",
            "UNIQUE(lang, slide_id)",
            "URL for this language already exists for this slide.",
        )
    ]
