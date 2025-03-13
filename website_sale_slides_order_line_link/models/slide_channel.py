# Copyright 2025 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SlideChannelPartner(models.Model):
    _inherit = "slide.channel.partner"

    sale_order_line_ids = fields.One2many(
        comodel_name="sale.order.line",
        inverse_name="slide_channel_partner_id",
        string="Sale Order Lines",
    )

    @api.model_create_multi
    def create(self, vals_list):
        sale_order_lines = self.env.context.get("course_sale_order_lines")
        records = super().create(vals_list)
        if not sale_order_lines:
            return records
        for record in records:
            record.sale_order_line_ids = sale_order_lines.filtered(
                lambda line: line.product_id == record.channel_id.product_id
                and line.order_id.partner_id == record.partner_id
            )
        return records
