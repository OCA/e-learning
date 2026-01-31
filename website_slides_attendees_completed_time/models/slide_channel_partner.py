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
                ["channel_id", "partner_id", "slide_id:array_agg"],
                groupby=["channel_id", "partner_id"],
                lazy=False,
            )
        )
        mapped_data = dict()
        Slide = self.env["slide.slide"]
        for item in read_group_res:
            mapped_data.setdefault(item["channel_id"][0], dict())
            mapped_data[item["channel_id"][0]][item["partner_id"][0]] = sum(
                Slide.browse(set(item["slide_id"])).mapped("completion_time"), 0.0
            )
        for record in self:
            record.completed_time = mapped_data.get(record.channel_id.id, dict()).get(
                record.partner_id.id, 0.0
            )
        return res
