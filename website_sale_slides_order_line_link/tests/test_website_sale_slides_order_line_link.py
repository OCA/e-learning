# Copyright 2025 Tecnativa - Pilar Vargas

from odoo.addons.website_slides.tests import common


class TestWebsiteSaleSlidesOrderLineLink(common.SlidesCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course_product = cls.env["product.product"].create(
            {
                "name": "Course Product",
                "standard_price": 100,
                "list_price": 150,
                "type": "service",
                "invoice_policy": "order",
                "is_published": True,
            }
        )

        cls.channel.write({"enroll": "payment", "product_id": cls.course_product.id})

    def test_order_line_link(self):
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.course_product.name,
                            "product_id": self.course_product.id,
                            "product_uom_qty": 1,
                            "price_unit": self.course_product.list_price,
                        },
                    )
                ],
            }
        )
        sale_order.action_confirm()
        self.assertIn(self.customer.id, self.channel.channel_partner_ids.partner_id.ids)
        sale_line = sale_order.order_line
        course_access = self.channel.channel_partner_ids.filtered(
            lambda x: x.partner_id == self.customer
        )
        self.assertIn(sale_line, course_access.sale_order_line_ids)
