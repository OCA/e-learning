# Copyright 2026 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.website_slides.tests import common


class TestWebsiteSaleSlidesSurveyMultiQty(common.SlidesCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.identification_number = "BE0477472701"
        cls.user_portal.partner_id.write(
            {
                "name": "Participant",
                "email": "participant@example.com",
                "phone": "123456789",
                "country_id": cls.env.ref("base.be").id,
                "vat": cls.identification_number,
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
                "channel_id": cls.channel.id,
                "slide_category": "certification",
                "survey_id": cls.survey.id,
                "is_published": True,
            }
        )
        cls.channel_partner = cls.env["slide.channel.partner"].create(
            {
                "channel_id": cls.channel.id,
                "partner_id": cls.user_portal.partner_id.id,
                "slide_channel_partner_name": "Course participant",
                "slide_channel_partner_email": "course@example.com",
                "slide_channel_partner_phone": "987654321",
                "identification_number": cls.identification_number,
            }
        )
        cls.slide_partner = cls.env["slide.slide.partner"].create(
            {
                "slide_id": cls.certification_slide.id,
                "channel_id": cls.channel.id,
                "partner_id": cls.user_portal.partner_id.id,
                "identification_number": cls.identification_number,
            }
        )

    def test_generate_certification_for_participant(self):
        self.certification_slide.with_user(
            self.user_portal
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
            self.user_portal
        )._generate_certification_url()
        user_input = self.slide_partner.user_input_ids
        certification_url = self.certification_slide.with_user(
            self.user_portal
        )._generate_certification_url()
        self.assertEqual(self.slide_partner.user_input_ids, user_input)
        self.assertEqual(
            certification_url[self.certification_slide.id],
            user_input.get_start_url(),
        )
