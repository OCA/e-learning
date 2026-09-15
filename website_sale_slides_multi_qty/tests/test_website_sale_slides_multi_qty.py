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
        cls.channel.write(
            {
                "enroll": "payment",
                "product_id": cls.course_product.id,
            }
        )
        # Avoid loading the empty PDF from the standard test fixture.
        cls.slide_3.slide_category = "infographic"
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
            login=self.user_portal.login,
        )

    def test_multi_sale_registration_lifecycle(self):
        buyer = new_test_user(
            self.env,
            login="multi_registration_buyer",
            groups="base.group_portal",
        )
        sale_order = self._create_sale_order(buyer.partner_id, 3)
        # A quotation must not create or increase registrations.
        self.assertFalse(self._get_parent_participation(buyer.partner_id))
        sale_order.action_confirm()
        self.env.invalidate_all()
        course_access = self._get_parent_participation(buyer.partner_id)
        # A multiple purchase creates one parent participation acting as a pool.
        self.assertEqual(len(course_access), 1)
        self.assertFalse(course_access.parent_id)
        self.assertFalse(course_access.child_channel_partner_ids)
        self.assertEqual(
            course_access.sale_order_line_ids,
            sale_order.order_line,
        )
        self.assertEqual(course_access.available_registrations, 3)
        self.assertEqual(course_access.used_registrations, 0)
        self.assertEqual(course_access.remaining_registrations, 3)
        self.assertTrue(course_access.invitation_hash)
        self.assertTrue(course_access.invitation_link)
        self.assertFalse(course_access.slide_channel_partner_name)
        self.assertFalse(course_access.slide_channel_partner_email)
        self.assertFalse(course_access.slide_channel_partner_phone)
        self.assertFalse(course_access.identification_number)
        self.assertFalse(course_access.is_public_slide_channel_partner)
        # The parent participation is a registration pool, not an enrollment.
        self.assertFalse(self.channel.with_user(buyer).is_member)
        self.assertNotIn(
            self.channel,
            self.env["slide.channel"]
            .with_user(buyer)
            .search([("is_member", "in", [True])]),
        )
        # The initial confirmation email is sent exactly once.
        initial_mails = self.env["mail.mail"].search(
            [
                ("model", "=", "sale.order"),
                ("res_id", "=", sale_order.id),
                ("subject", "ilike", "Your access to"),
                ("recipient_ids", "in", [buyer.partner_id.id]),
            ]
        )
        self.assertEqual(len(initial_mails), 1)
        additional_order = self._create_sale_order(
            buyer.partner_id,
            2,
        )
        # An unconfirmed additional order must not alter the pool.
        self.env.invalidate_all()
        self.assertEqual(
            course_access.sale_order_line_ids,
            sale_order.order_line,
        )
        self.assertEqual(course_access.available_registrations, 3)
        additional_order.action_confirm()
        self.env.invalidate_all()
        current_course_access = self._get_parent_participation(buyer.partner_id)
        expected_lines = sale_order.order_line | additional_order.order_line
        # Confirming another purchase reuses the existing pool.
        self.assertEqual(current_course_access, course_access)
        self.assertCountEqual(
            course_access.sale_order_line_ids.ids,
            expected_lines.ids,
        )
        self.assertEqual(course_access.available_registrations, 5)
        self.assertEqual(course_access.used_registrations, 0)
        self.assertEqual(course_access.remaining_registrations, 5)
        # The registrations-added notification is sent exactly once.
        messages = self.env["mail.message"].search(
            [
                ("model", "=", "sale.order"),
                ("res_id", "=", additional_order.id),
                (
                    "subject",
                    "ilike",
                    "Course Registrations Added",
                ),
            ]
        )
        self.assertEqual(len(messages), 1)
        additional_order.action_cancel()
        self.env.invalidate_all()
        # Cancelling the additional order removes its available registrations.
        self.assertEqual(course_access.available_registrations, 3)
        self.assertEqual(course_access.used_registrations, 0)
        self.assertEqual(course_access.remaining_registrations, 3)

    def test_single_sale_consumption_and_additional_sale(self):
        buyer = new_test_user(
            self.env,
            login="single_registration_buyer",
            groups="base.group_portal",
        )
        single_sale_order = self._create_sale_order(
            buyer.partner_id,
            1,
        )
        single_sale_order.action_confirm()
        individual_participation = self._get_parent_participation(buyer.partner_id)
        # A single purchase is an individual enrollment, not a pool.
        self.assertEqual(len(individual_participation), 1)
        self.assertFalse(individual_participation.parent_id)
        self.assertFalse(individual_participation.child_channel_partner_ids)
        self.assertEqual(
            individual_participation.sale_order_line_ids,
            single_sale_order.order_line,
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
        self.slide.with_user(buyer).action_mark_completed()
        self.env.invalidate_all()
        slide_participation = self.env["slide.slide.partner"].search(
            [
                ("slide_id", "=", self.slide.id),
                ("partner_id", "=", buyer.partner_id.id),
            ]
        )
        self.assertEqual(len(slide_participation), 1)
        self.assertTrue(slide_participation.completed)
        self.assertEqual(
            self.channel.with_user(buyer).completion,
            33,
        )
        additional_sale_order = self._create_sale_order(
            buyer.partner_id,
            3,
        )
        # A quotation must not convert the individual enrollment into a pool.
        self.env.invalidate_all()
        self.assertFalse(individual_participation.parent_id)
        self.assertEqual(
            individual_participation.sale_order_line_ids,
            single_sale_order.order_line,
        )
        additional_sale_order.action_confirm()
        self.env.invalidate_all()
        parent_participation = self._get_parent_participation(buyer.partner_id)
        expected_lines = single_sale_order.order_line | additional_sale_order.order_line
        # The individual enrollment becomes a child of the new pool.
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
        self.assertFalse(parent_participation.identification_number)
        self.assertFalse(parent_participation.slide_channel_partner_name)
        self.assertFalse(parent_participation.slide_channel_partner_email)
        self.assertFalse(parent_participation.slide_channel_partner_phone)
        # Converting the enrollment into a pool preserves its progress.
        current_slide_participation = self.env["slide.slide.partner"].search(
            [
                ("slide_id", "=", self.slide.id),
                ("partner_id", "=", buyer.partner_id.id),
            ]
        )
        self.assertEqual(
            current_slide_participation,
            slide_participation,
        )
        self.assertTrue(current_slide_participation.completed)
        self.assertEqual(
            self.channel.with_user(buyer).completion,
            33,
        )
        self.start_tour(
            f"/slides/{self.channel.id}",
            "website_sale_slides_multi_qty_buyer_already_enrolled",
            login=buyer.login,
        )

    def test_website_sale_slides_multi_qty_join_without_user(self):
        self.channel.write(
            {
                "allow_comment": True,
                "karma_slide_vote": 0,
            }
        )
        self.sale_order.action_confirm()
        course_access = self._get_parent_participation(self.customer)
        url = self._get_invitation_url(course_access)
        # Ensure that anonymous enrollment does not create contacts or users.
        partner_count = self.env["res.partner"].search_count([])
        user_count = self.env["res.users"].search_count([])
        public_user = self.env.ref("base.public_user")
        public_karma = public_user.karma
        # Create an anonymous participation using the invitation.
        self.start_tour(
            url,
            "website_sale_slides_order_line_multi_qty_register_without_user",
        )
        # Access again with the same identification number and complete the course flow.
        self.start_tour(
            url,
            "website_sale_slides_order_line_multi_qty_join_without_user",
        )
        # Refresh records modified by the HTTP requests.
        self.env.invalidate_all()
        anonymous_participation = self.env["slide.channel.partner"].search(
            [
                ("channel_id", "=", self.channel.id),
                (
                    "identification_number",
                    "=",
                    "BE0477472701",
                ),
            ]
        )
        # The second access must reuse the existing participation.
        self.assertEqual(len(anonymous_participation), 1)
        self.assertEqual(
            anonymous_participation.parent_id,
            course_access,
        )
        self.assertEqual(
            anonymous_participation.partner_id,
            self.customer,
        )
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
        anonymous_slide_progress = self.env["slide.slide.partner"].search(
            [
                ("slide_id", "=", self.slide.id),
                ("partner_id", "=", self.customer.id),
                (
                    "identification_number",
                    "=",
                    "BE0477472701",
                ),
            ]
        )
        anonymous_quiz_progress = self.env["slide.slide.partner"].search(
            [
                ("slide_id", "=", self.slide_3.id),
                ("partner_id", "=", self.customer.id),
                (
                    "identification_number",
                    "=",
                    "BE0477472701",
                ),
            ]
        )
        # Completing and uncompleting a slide preserves its vote and final state.
        self.assertEqual(len(anonymous_slide_progress), 1)
        self.assertFalse(anonymous_slide_progress.completed)
        self.assertEqual(anonymous_slide_progress.vote, 1)
        # The quiz records both attempts and is completed by the correct answer.
        self.assertEqual(len(anonymous_quiz_progress), 1)
        self.assertTrue(anonymous_quiz_progress.completed)
        self.assertEqual(
            anonymous_quiz_progress.quiz_attempts_count,
            2,
        )
        # Only the completed quiz contributes to the participant's progress.
        self.assertEqual(
            anonymous_participation.completed_slides_count,
            1,
        )
        # Anonymous progress must never be assigned to Odoo's public partner.
        public_progress = self.env["slide.slide.partner"].search(
            [
                (
                    "slide_id",
                    "in",
                    [self.slide.id, self.slide_3.id],
                ),
                (
                    "partner_id",
                    "=",
                    public_user.partner_id.id,
                ),
            ]
        )
        self.assertFalse(public_progress)
        # Anonymous quiz completion must not grant karma to the public user.
        public_user.invalidate_recordset(["karma"])
        self.assertEqual(public_user.karma, public_karma)
        self.user_portal.partner_id.write(
            {
                "country_id": self.env.ref("base.be").id,
                "vat": "BE0477472701",
            }
        )
        # Linking a registered account reuses the anonymous participation.
        self.start_tour(
            url,
            "website_sale_slides_order_line_multi_qty_join_registered_user",
            login=self.user_portal.login,
        )
        self.env.invalidate_all()
        linked_participation = self.env["slide.channel.partner"].search(
            [
                ("channel_id", "=", self.channel.id),
                (
                    "identification_number",
                    "=",
                    "BE0477472701",
                ),
            ]
        )
        self.assertEqual(
            linked_participation,
            anonymous_participation,
        )
        self.assertEqual(
            linked_participation.partner_id,
            self.user_portal.partner_id,
        )
        self.assertFalse(linked_participation.is_public_slide_channel_partner)
        self.assertEqual(
            linked_participation.parent_id,
            course_access,
        )
        # All anonymous slide progress is transferred to the registered partner.
        linked_slide_progress = self.env["slide.slide.partner"].search(
            [
                (
                    "slide_id",
                    "in",
                    [self.slide.id, self.slide_3.id],
                ),
                (
                    "identification_number",
                    "=",
                    "BE0477472701",
                ),
            ]
        )
        self.assertEqual(
            linked_slide_progress,
            anonymous_slide_progress | anonymous_quiz_progress,
        )
        self.assertEqual(
            linked_slide_progress.partner_id,
            self.user_portal.partner_id,
        )

    def test_registered_participant_requires_login_for_anonymous_access(
        self,
    ):
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
                (
                    "partner_id",
                    "=",
                    self.user_portal.partner_id.id,
                ),
                (
                    "identification_number",
                    "=",
                    "BE0477472701",
                ),
            ]
        )
        self.assertEqual(len(registered_participation), 1)
        self.assertEqual(
            registered_participation.parent_id,
            course_access,
        )
        # The registered participant's progress belongs to the child participation.
        self.slide.with_user(self.user_portal).action_mark_completed()
        self.env.invalidate_all()
        slide_participation = self.env["slide.slide.partner"].search(
            [
                ("slide_id", "=", self.slide.id),
                (
                    "partner_id",
                    "=",
                    self.user_portal.partner_id.id,
                ),
            ]
        )
        self.assertEqual(len(slide_participation), 1)
        self.assertTrue(slide_participation.completed)
        # Trying to use the same identification anonymously must request login.
        self.start_tour(
            url,
            "website_sale_slides_order_line_multi_qty_registered_user_login",
        )
        self.env.invalidate_all()
        child_participations = self.env["slide.channel.partner"].search(
            [("parent_id", "=", course_access.id)]
        )
        # The anonymous attempt must not consume another registration.
        self.assertEqual(
            child_participations,
            registered_participation,
        )
        self.assertEqual(course_access.used_registrations, 1)
        self.assertEqual(course_access.remaining_registrations, 2)
        # The anonymous attempt must not alter the registered participant's progress.
        current_slide_participation = self.env["slide.slide.partner"].search(
            [
                ("slide_id", "=", self.slide.id),
                (
                    "partner_id",
                    "=",
                    self.user_portal.partner_id.id,
                ),
            ]
        )
        self.assertEqual(
            current_slide_participation,
            slide_participation,
        )
        self.assertTrue(current_slide_participation.completed)
