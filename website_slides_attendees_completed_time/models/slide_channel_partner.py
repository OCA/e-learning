# Copyright 2025 Binhex
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SlideChannelPartner(models.Model):
    _inherit = "slide.channel.partner"

    completed_time = fields.Float("Completed Time (hours)")

    def _recompute_completion(self):
        res = super()._recompute_completion()
        read_group_res = (
            self.env["slide.slide.partner"]
            .sudo()
            ._read_group(
                [
                    "&",
                    "&",
                    ("channel_id", "in", self.mapped("channel_id").ids),
                    ("partner_id", "in", self.mapped("partner_id").ids),
                    ("completed", "=", True),
                    ("slide_id.is_published", "=", True),
                    ("slide_id.active", "=", True),
                ],
                ["channel_id", "partner_id"],
                aggregates=["slide_id:recordset"],
            )
        )
        mapped_data = {
            (channel.id, partner.id): sum(slides.mapped("completion_time"), 0.0)
            for channel, partner, slides in read_group_res
        }

        for record in self:
            record.completed_time = mapped_data.get(
                (record.channel_id.id, record.partner_id.id), 0.0
            )
        return res
