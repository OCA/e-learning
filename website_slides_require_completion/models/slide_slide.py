# Copyright 2025 Binhex - Adasat Torres de León
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SlideSlide(models.Model):
    _inherit = "slide.slide"

    is_blocked = fields.Boolean(compute="_compute_is_blocked", compute_sudo=False)

    def _get_previous_slide(self):
        return self.search(
            [
                ("is_category", "=", False),
                ("sequence", "<", self.sequence),
                ("channel_id", "=", self.channel_id.id),
            ],
            order="sequence desc",
            limit=1,
        )

    def _compute_is_blocked(self):
        for slide in self:
            previous_slide = slide._get_previous_slide()
            if not previous_slide or not slide.channel_id.require_slides_completion:
                slide.is_blocked = False
            else:
                slide.is_blocked = not previous_slide.user_has_completed
