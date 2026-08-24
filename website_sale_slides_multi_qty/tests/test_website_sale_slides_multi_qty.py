# Copyright 2025 Tecnativa - Pilar Vargas

from odoo import Command
from odoo.tests import HttpCase, new_test_user, tagged

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
                "service_tracking": "course",
                "invoice_policy": "order",
                "is_published": True,
            }
        )
        cls.channel.write({"enroll": "payment", "product_id": cls.course_product.id})
        cls.sale_order = cls._create_sale_order(cls.customer, 3)

    @classmethod
    def _create_sale_order(cls, partner, quantity):
        return cls.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "order_line": [
                    Command.create(
                        {
                            "name": cls.course_product.name,
                            "product_id": cls.course_product.id,
                            "product_uom_qty": quantity,
                            "price_unit": cls.course_product.list_price,
                        }
                    )
                ],
            }
        )

    def _get_parent_participation(self, partner):
        return (
            self.env["slide.channel.partner"]
            .sudo()
            .search(
                [
                    ("channel_id", "=", self.channel.id),
                    ("partner_id", "=", partner.id),
                    ("parent_id", "=", False),
                    ("sale_order_line_ids", "!=", False),
                ]
            )
        )

    def _get_invitation_url(self, participation):
        return (
            f"/slides/{self.channel.id}/invite"
            f"?invite_partner_id={participation.partner_id.id}"
            f"&invite_hash={participation._get_invitation_hash()}"
        )

    def test_verify_updated_course_quantity(self):
        # Allow course quantities greater than core's limit of one.
        quantity, warning = self.sale_order._verify_updated_quantity(
            self.sale_order.order_line,
            self.course_product.id,
            3,
            self.course_product.uom_id.id,
        )
        self.assertEqual(quantity, 3)
        self.assertFalse(warning)

    def test_website_sale_slides_order_line_multi_qty(self):
        self.start_tour(
            "/slides",
            "website_sale_slides_order_line_multi_qty",
            login="portal",
        )

    def test_website_sale_slides_multi_qty_send_mail(self):
        self.sale_order.action_confirm()
        mail = self.env["mail.mail"].search(
            [
                ("model", "=", "sale.order"),
                ("res_id", "=", self.sale_order.id),
                ("subject", "ilike", "Your access to"),
                ("recipient_ids", "in", [self.customer.id]),
            ]
        )
        self.assertEqual(len(mail), 1)

    def test_website_sale_slides_multi_qty_participation(self):
        self.sale_order.action_confirm()
        course_access = self._get_parent_participation(self.customer)
        self.assertEqual(len(course_access), 1)
        self.assertFalse(course_access.parent_id)
        self.assertFalse(course_access.child_channel_partner_ids)
        self.assertEqual(course_access.available_registrations, 3)
        self.assertEqual(course_access.used_registrations, 0)
        self.assertEqual(course_access.remaining_registrations, 3)
        self.assertTrue(course_access.invitation_hash)
        self.assertTrue(course_access.invitation_link)
        self.assertEqual(course_access.slide_channel_partner_name, self.customer.name)
        self.assertEqual(course_access.slide_channel_partner_email, self.customer.email)
        self.assertEqual(course_access.slide_channel_partner_phone, self.customer.phone)
        self.assertFalse(course_access.identification_number)
        self.assertFalse(course_access.is_public_slide_channel_partner)

    def test_additional_purchase_updates_parent_participation(self):
        # Reuse the parent participation when buying more registrations.
        self.sale_order.action_confirm()
        additional_order = self._create_sale_order(self.customer, 2)
        additional_order.action_confirm()
        course_access = self._get_parent_participation(self.customer)
        expected_lines = self.sale_order.order_line | additional_order.order_line
        self.assertEqual(len(course_access), 1)
        self.assertCountEqual(
            course_access.sale_order_line_ids.ids,
            expected_lines.ids,
        )
        self.assertEqual(course_access.available_registrations, 5)
        self.assertEqual(course_access.used_registrations, 0)
        self.assertEqual(course_access.remaining_registrations, 5)
        message = self.env["mail.message"].search(
            [
                ("model", "=", "sale.order"),
                ("res_id", "=", additional_order.id),
                ("subject", "ilike", "Course Registrations Added"),
            ]
        )
        self.assertEqual(len(message), 1)

    def test_single_purchase_consumption_and_additional_purchase(self):
        buyer = new_test_user(
            self.env,
            login="single_registration_buyer",
            groups="base.group_portal",
        )
        single_order = self._create_sale_order(
            buyer.partner_id,
            1,
        )
        single_order.action_confirm()
        individual_participation = self._get_parent_participation(buyer.partner_id)
        self.assertEqual(len(individual_participation), 1)
        self.assertFalse(individual_participation.parent_id)
        self.assertFalse(individual_participation.child_channel_partner_ids)
        self.assertEqual(
            individual_participation.sale_order_line_ids,
            single_order.order_line,
        )
        self.assertEqual(
            individual_participation.available_registrations,
            1,
        )
        self.assertEqual(
            individual_participation.used_registrations,
            1,
        )
        self.assertEqual(
            individual_participation.remaining_registrations,
            0,
        )
        self.assertTrue(self.channel.with_user(buyer).is_member)
        additional_order = self._create_sale_order(
            buyer.partner_id,
            3,
        )
        additional_order.action_confirm()
        self.env.invalidate_all()
        parent_participation = self._get_parent_participation(buyer.partner_id)
        expected_lines = single_order.order_line | additional_order.order_line
        self.assertEqual(len(parent_participation), 1)
        self.assertNotEqual(
            parent_participation,
            individual_participation,
        )
        self.assertCountEqual(
            parent_participation.sale_order_line_ids.ids,
            expected_lines.ids,
        )
        self.assertEqual(
            parent_participation.child_channel_partner_ids,
            individual_participation,
        )
        self.assertEqual(
            individual_participation.parent_id,
            parent_participation,
        )
        self.assertFalse(individual_participation.sale_order_line_ids)
        self.assertEqual(
            parent_participation.available_registrations,
            4,
        )
        self.assertEqual(
            parent_participation.used_registrations,
            1,
        )
        self.assertEqual(
            parent_participation.remaining_registrations,
            3,
        )
        self.assertTrue(self.channel.with_user(buyer).is_member)

    def test_website_sale_slides_multi_qty_join_without_user(self):
        self.sale_order.action_confirm()
        course_access = self._get_parent_participation(self.customer)
        url = self._get_invitation_url(course_access)
        # Ensure that anonymous enrollment does not create contacts or users.
        partner_count = self.env["res.partner"].search_count([])
        user_count = self.env["res.users"].search_count([])
        # Create an anonymous participation using the invitation.
        self.start_tour(
            url,
            "website_sale_slides_order_line_multi_qty_register_without_user",
        )
        # Access again with the same identification number.
        self.start_tour(
            url,
            "website_sale_slides_order_line_multi_qty_join_without_user",
        )
        # Refresh records modified by the HTTP requests.
        self.env.invalidate_all()
        anonymous_participation = self.env["slide.channel.partner"].search(
            [
                ("channel_id", "=", self.channel.id),
                ("identification_number", "=", "BE0477472701"),
            ]
        )
        # The second access must reuse the existing participation.
        self.assertEqual(len(anonymous_participation), 1)
        self.assertEqual(anonymous_participation.parent_id, course_access)
        self.assertEqual(anonymous_participation.partner_id, self.customer)
        self.assertEqual(
            anonymous_participation.slide_channel_partner_name,
            "MY TEST USER",
        )
        self.assertEqual(
            anonymous_participation.slide_channel_partner_email,
            "testuser@example.com",
        )
        self.assertEqual(
            anonymous_participation.slide_channel_partner_phone,
            "123456789",
        )
        self.assertTrue(anonymous_participation.is_public_slide_channel_partner)
        # The anonymous participation consumes exactly one purchased registration.
        self.assertEqual(
            course_access.child_channel_partner_ids,
            anonymous_participation,
        )
        self.assertEqual(course_access.used_registrations, 1)
        self.assertEqual(course_access.remaining_registrations, 2)
        # No contact or user must be created for the anonymous participant.
        self.assertEqual(
            self.env["res.partner"].search_count([]),
            partner_count,
        )
        self.assertEqual(
            self.env["res.users"].search_count([]),
            user_count,
        )

    def test_registered_participant_requires_login_for_anonymous_access(self):
        # Purchase three registrations.
        self.sale_order.action_confirm()
        course_access = self._get_parent_participation(self.customer)
        # Use an existing portal user as the registered participant.
        self.user_portal.partner_id.write(
            {
                "country_id": self.env.ref("base.be").id,
                "vat": "BE0477472701",
            }
        )
        url = self._get_invitation_url(course_access)
        # The registered user joins through the invitation.
        self.start_tour(
            url,
            "website_sale_slides_order_line_multi_qty_join_registered_user",
            login=self.user_portal.login,
        )
        self.env.invalidate_all()
        registered_participation = self.env["slide.channel.partner"].search(
            [
                ("channel_id", "=", self.channel.id),
                ("partner_id", "=", self.user_portal.partner_id.id),
                ("identification_number", "=", "BE0477472701"),
            ]
        )
        self.assertEqual(len(registered_participation), 1)
        self.assertEqual(registered_participation.parent_id, course_access)
        self.assertEqual(course_access.used_registrations, 1)
        self.assertEqual(course_access.remaining_registrations, 2)
        # Trying to use the same identification anonymously must request login.
        self.start_tour(
            url,
            "website_sale_slides_order_line_multi_qty_registered_user_login",
        )
        self.env.invalidate_all()
        child_participations = self.env["slide.channel.partner"].search(
            [("parent_id", "=", course_access.id)]
        )
        self.assertEqual(child_participations, registered_participation)
        self.assertEqual(course_access.used_registrations, 1)
        self.assertEqual(course_access.remaining_registrations, 2)
