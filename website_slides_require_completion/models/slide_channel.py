# Copyright 2025 Binhex - Adasat Torres de León
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SlideChannel(models.Model):
    _inherit = "slide.channel"

    require_slides_completion = fields.Boolean(
        string="Require previous slides completion",
        help="""If checked, the user has to complete previous slides before """
        """moving to the next one""",
        default=False,
    )
