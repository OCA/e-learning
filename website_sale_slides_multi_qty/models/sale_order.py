# Copyright 2025 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _verify_updated_quantity(self, order_line, product_id, new_qty, **kwargs):
        # Allow adding more than 1 quantity of a course to the cart
        res = super()._verify_updated_quantity(
            order_line, product_id, new_qty, **kwargs
        )
        product = self.env["product.product"].browse(product_id)
        if product.detailed_type == "course" and new_qty > 1:
            return new_qty, ""
        return res
