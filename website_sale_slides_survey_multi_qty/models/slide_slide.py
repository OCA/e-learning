# Copyright 2025 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class Slide(models.Model):
    _inherit = "slide.slide"

    def _generate_certification_url(self):
        self = self.sudo()
        certifications_with_key = self.filtered(
            lambda slide: slide.slide_category == "certification"
            and slide.survey_id
            and slide.user_membership_id
            and slide.user_membership_id.identification_number
        )
        certifications = self - certifications_with_key
        certification_urls = {}
        if certifications:
            certification_urls.update(
                super(Slide, certifications)._generate_certification_url()
            )
        for slide in certifications_with_key:
            if slide.channel_id.is_member:
                user_membership_id_sudo = slide.user_membership_id.sudo()
                channel_partner = slide.channel_id.channel_partner_ids.filtered(
                    lambda cp,
                    user_membership_id_sudo=user_membership_id_sudo,
                    slide=slide: cp.partner_id.id
                    == user_membership_id_sudo.partner_id.id
                    and cp.identification_number
                    == slide.user_membership_id.identification_number
                )[:1]
                if user_membership_id_sudo.user_input_ids:
                    last_user_input = next(
                        user_input
                        for user_input in user_membership_id_sudo.user_input_ids.sorted(
                            lambda user_input: user_input.create_date, reverse=True
                        )
                    )
                    certification_urls[slide.id] = last_user_input.get_start_url()
                else:
                    user_input = slide.survey_id.sudo()._create_answer(
                        partner=user_membership_id_sudo.partner_id,
                        check_attempts=False,
                        **{
                            "slide_id": slide.id,
                            "slide_partner_id": user_membership_id_sudo.id,
                            "channel_partner_id": channel_partner.id,
                        },
                        invite_token=self.env[
                            "survey.user_input"
                        ]._generate_invite_token(),
                    )
                    certification_urls[slide.id] = user_input.get_start_url()
            else:
                user_input = slide.survey_id.sudo()._create_answer(
                    partner=self.env.user.partner_id,
                    check_attempts=False,
                    test_entry=True,
                    **{"slide_id": slide.id},
                )
                certification_urls[slide.id] = user_input.get_start_url()
        return certification_urls
