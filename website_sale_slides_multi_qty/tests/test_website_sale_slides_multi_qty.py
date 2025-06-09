# Copyright 2025 Tecnativa - Pilar Vargas

from odoo import Command
from odoo.tests import HttpCase, tagged

from odoo.addons.website_slides.tests import common


@tagged("post_install", "-at_install")
class TestWebsiteSaleSlidesMultiQty(common.SlidesCase, HttpCase):
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
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.customer.id,
                "order_line": [
                    Command.create(
                        {
                            "name": cls.course_product.name,
                            "product_id": cls.course_product.id,
                            "product_uom_qty": 3,
                            "price_unit": cls.course_product.list_price,
                        },
                    )
                ],
            }
        )

    def test_website_sale_slides_order_line_multi_qty(self):
        self.start_tour(
            "/slides",
            "website_sale_slides_order_line_multi_qty",
            login="portal",
            step_delay=1000,
        )

    def test_website_sale_slides_multi_qty_send_mail(self):
        self.sale_order.action_confirm()
        mail = self.env["mail.mail"].search(
            [
                ("model", "=", "slide.channel.partner"),
                ("res_id", "!=", False),
                ("subject", "ilike", "Your access to"),
                ("recipient_ids", "in", [self.customer.id]),
            ]
        )
        self.assertTrue(mail)

    def test_website_sale_slides_multi_qty_participation(self):
        self.sale_order.action_confirm()
        course_access = self.channel.channel_partner_ids.filtered(
            lambda x: x.partner_id == self.customer
        )
        self.assertFalse(course_access.parent_id)
        self.assertFalse(course_access.child_channel_partner_ids)
        self.assertEqual(course_access.available_registrations, 3)
        self.assertEqual(course_access.used_registrations, 0)
        self.assertTrue(course_access.invitation_hash)
        self.assertTrue(course_access.invitation_link)
        self.assertEqual(course_access.slide_channel_partner_name, self.customer.name)
        self.assertEqual(course_access.slide_channel_partner_email, self.customer.email)
        self.assertEqual(
            course_access.slide_channel_partner_phone, self.customer.mobile
        )
        self.assertFalse(course_access.identification_number)
        self.assertFalse(course_access.is_public_slide_channel_partner)

    def test_website_sale_slides_multi_qty_join_without_user(self):
        self.sale_order.action_confirm()
        course_access = self.channel.channel_partner_ids.filtered(
            lambda x: x.partner_id == self.customer
        )
        url = (
            f"/slides/{self.channel.id}/invite"
            f"?invite_partner_id={self.customer.id}"
            f"&invite_hash={course_access._get_invitation_hash()}"
        )
        self.start_tour(
            url,
            "website_sale_slides_order_line_multi_qty_register_without_user",
            step_delay=1000,
        )
        self.start_tour(
            url,
            "website_sale_slides_order_line_multi_qty_join_without_user",
            step_delay=1000,
        )
