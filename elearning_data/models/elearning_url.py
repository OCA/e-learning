# -*- coding: utf-8 -*-
# © 2024 Open Net Sarl
# License OPL-1 or later (https://www.odoo.com/documentation/17.0/legal/licenses.html#odoo-apps).

from odoo import models, fields

class eLearningUrl(models.Model):
    _name = "elearning.url"
    
    lang = fields.Many2one(comodel_name="res.lang", string="Language", default=lambda self: self.env["res.lang"].search([("code", "=", self.env.context.get("lang", self.env.user.lang))]))
    
    slide_id = fields.Many2one(comodel_name="slide.slide", string="Slide")
    
    url = fields.Char(string="URL")
    
    _sql_constraints = [
        (
            "unique_lang_slide_id",
            "UNIQUE(lang, slide_id)",
            "URL for this language already exists for this slide.",
        )]