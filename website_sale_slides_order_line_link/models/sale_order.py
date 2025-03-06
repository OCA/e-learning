# Copyright 2025 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _action_confirm(self):
        course_lines = self.order_line.filtered(
            lambda line: line.product_id.channel_ids
        )
        if course_lines:
            return super(
                SaleOrder, self.with_context(course_sale_order_lines=course_lines)
            )._action_confirm()
        return super()._action_confirm()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    slide_channel_partner_id = fields.Many2one(
        comodel_name="slide.channel.partner",
    )
