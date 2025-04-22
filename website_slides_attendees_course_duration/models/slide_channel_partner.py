# Copyright 2025 Binhex
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SlideChannelPartner(models.Model):

    _inherit = "slide.channel.partner"

    total_time = fields.Float(related="channel_id.total_time")
