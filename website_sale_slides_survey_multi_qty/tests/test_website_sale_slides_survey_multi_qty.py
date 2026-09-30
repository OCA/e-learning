# Copyright 2026 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import new_test_user

from odoo.addons.base.tests.common import BaseCommon


class TestWebsiteSaleSlidesSurveyMultiQty(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.identification_number = "BE0477472701"
        cls.certification_user = new_test_user(
            cls.env,
            login="certification_participant",
            groups="base.group_portal",
        )
        cls.certification_user.partner_id.write(
            {
                "name": "Participant",
                "email": "participant@example.com",
                "phone": "123456789",
                "country_id": cls.env.ref("base.be").id,
                "vat": cls.identification_number,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Product Certification Channel",
                "standard_price": 100,
                "list_price": 150,
                "type": "service",
                "service_tracking": "course",
                "invoice_policy": "order",
                "is_published": True,
            }
        )
        cls.certification_channel = cls.env["slide.channel"].create(
            {
                "name": "Test Certification Channel",
                "channel_type": "training",
                "enroll": "payment",
                "product_id": cls.product.id,
                "visibility": "public",
                "is_published": True,
            }
        )
        cls.survey = cls.env["survey.survey"].create(
            {
                "title": "Certification",
            }
        )
        cls.certification_slide = cls.env["slide.slide"].create(
            {
                "name": "Certification",
                "channel_id": cls.certification_channel.id,
                "slide_category": "certification",
                "survey_id": cls.survey.id,
                "is_published": True,
            }
        )
        cls.channel_partner = cls.env["slide.channel.partner"].create(
            {
                "channel_id": cls.certification_channel.id,
                "partner_id": cls.certification_user.partner_id.id,
                "slide_channel_partner_name": "Course participant",
                "slide_channel_partner_email": "course@example.com",
                "slide_channel_partner_phone": "987654321",
                "identification_number": cls.identification_number,
            }
        )
        cls.slide_partner = cls.env["slide.slide.partner"].create(
            {
                "slide_id": cls.certification_slide.id,
                "channel_id": cls.certification_channel.id,
                "partner_id": cls.certification_user.partner_id.id,
                "identification_number": cls.identification_number,
            }
        )

    def test_generate_certification_for_participant(self):
        self.certification_slide.with_user(
            self.certification_user
        )._generate_certification_url()
        user_input = self.env["survey.user_input"].search(
            [
                ("slide_id", "=", self.certification_slide.id),
                ("channel_partner_id", "=", self.channel_partner.id),
            ]
        )
        self.assertEqual(len(user_input), 1)
        self.assertEqual(user_input.channel_partner_id, self.channel_partner)
        self.assertEqual(
            (
                user_input.slide_channel_partner_name,
                user_input.slide_channel_partner_email,
                user_input.slide_channel_partner_phone,
            ),
            (
                "Course participant",
                "course@example.com",
                "987654321",
            ),
        )

    def test_reuse_existing_certification(self):
        self.certification_slide.with_user(
            self.certification_user
        )._generate_certification_url()
        user_input = self.slide_partner.user_input_ids
        certification_url = self.certification_slide.with_user(
            self.certification_user
        )._generate_certification_url()
        self.assertEqual(self.slide_partner.user_input_ids, user_input)
        self.assertEqual(
            certification_url[self.certification_slide.id],
            user_input.get_start_url(),
        )
