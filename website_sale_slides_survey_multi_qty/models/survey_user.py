# Copyright 2025 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SurveyUserInput(models.Model):
    _inherit = "survey.user_input"

    channel_partner_id = fields.Many2one("slide.channel.partner")
    slide_channel_partner_name = fields.Char(
        related="channel_partner_id.slide_channel_partner_name"
    )
    slide_channel_partner_email = fields.Char(
        related="channel_partner_id.slide_channel_partner_email"
    )
    slide_channel_partner_phone = fields.Char(
        related="channel_partner_id.slide_channel_partner_phone"
    )
