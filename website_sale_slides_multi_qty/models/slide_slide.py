# Copyright 2025 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.fields import Domain
from odoo.http import request
from odoo.tools import sql


class SlideSlidePartner(models.Model):
    _inherit = "slide.slide.partner"

    identification_number = fields.Char()

    _slide_partner_uniq = models.Constraint(
        "CHECK (true)",
        "Constraint disabled: allowing repeated partner on the same slide.",
    )

    _unique_slide_identification = models.Constraint(
        "unique(slide_id, identification_number)",
        "The identification number must be unique!",
    )


class SlideSlide(models.Model):
    _inherit = "slide.slide"

    def _is_public_with_key(self):
        return bool(self) and self.channel_id._is_public_with_key()

    def _compute_user_membership_id(self):
        res = super()._compute_user_membership_id()
        if not self.channel_id._has_key_session():
            return res
        participations = self.channel_id._get_public_key_participations()
        authorized_slides = self.filtered(
            lambda slide: slide.channel_id in participations.channel_id
        )
        if not authorized_slides:
            return res
        slide_partners = (
            self.env["slide.slide.partner"]
            .sudo()
            .search(
                [
                    ("slide_id", "in", authorized_slides.ids),
                    (
                        "partner_id",
                        "=",
                        int(request.session["invite_partner_id"]),
                    ),
                    (
                        "identification_number",
                        "=",
                        request.session["identification_number"],
                    ),
                ]
            )
        )
        memberships_by_slide = {
            slide_partner.slide_id.id: slide_partner for slide_partner in slide_partners
        }
        for slide in authorized_slides:
            membership = memberships_by_slide.get(
                slide.id,
                self.env["slide.slide.partner"],
            )
            slide.user_membership_id = membership
            slide.user_vote = membership.vote
            slide.user_has_completed = membership.completed
        return res

    def _action_vote(self, upvote=True):
        if not self._is_public_with_key():
            return super()._action_vote(upvote)
        partner_id = int(request.session["invite_partner_id"])
        identification_number = request.session["identification_number"]
        slide_partners = (
            self.env["slide.slide.partner"]
            .sudo()
            .search(
                [
                    ("slide_id", "in", self.ids),
                    ("partner_id", "=", partner_id),
                    ("identification_number", "=", identification_number),
                ]
            )
        )
        existing_slides = slide_partners.slide_id
        for slide_partner in slide_partners:
            expected_vote = 1 if upvote else -1
            slide_partner.vote = (
                0 if slide_partner.vote == expected_vote else expected_vote
            )
        new_vote = 1 if upvote else -1
        self.env["slide.slide.partner"].sudo().create(
            [
                {
                    "slide_id": slide.id,
                    "channel_id": slide.channel_id.id,
                    "partner_id": partner_id,
                    "identification_number": identification_number,
                    "vote": new_vote,
                }
                for slide in self - existing_slides
            ]
        )

    def _action_set_viewed(self, target_partner, quiz_attempts_inc=False):
        if self._is_public_with_key():
            invite_partner_id = request.session.get("invite_partner_id")
            identification_number = request.session.get("identification_number")
            self_sudo = self.sudo()
            SlidePartnerSudo = self.env["slide.slide.partner"].sudo()
            existing_sudo = SlidePartnerSudo.search(
                [
                    ("slide_id", "in", self.ids),
                    ("partner_id", "=", int(invite_partner_id)),
                    (
                        "identification_number",
                        "=",
                        identification_number,
                    ),
                ]
            )
            if quiz_attempts_inc and existing_sudo:
                sql.increment_fields_skiplock(existing_sudo, "quiz_attempts_count")
                existing_sudo.invalidate_recordset(["quiz_attempts_count"])
            new_slides = self_sudo - existing_sudo.mapped("slide_id")
            return SlidePartnerSudo.create(
                [
                    {
                        "slide_id": new_slide.id,
                        "channel_id": new_slide.channel_id.id,
                        "partner_id": int(invite_partner_id),
                        "quiz_attempts_count": 1 if quiz_attempts_inc else 0,
                        "vote": 0,
                        "identification_number": identification_number,
                    }
                    for new_slide in new_slides
                ]
            )
        return super()._action_set_viewed(
            target_partner, quiz_attempts_inc=quiz_attempts_inc
        )

    def _action_mark_completed(self):
        if not self._is_public_with_key():
            return super()._action_mark_completed()
        uncompleted_slides = self.filtered(lambda slide: not slide.user_has_completed)
        uncompleted_slides._action_set_quiz_done()
        partner_id = int(request.session["invite_partner_id"])
        identification_number = request.session["identification_number"]
        slide_partners = (
            self.env["slide.slide.partner"]
            .sudo()
            .search(
                [
                    ("slide_id", "in", uncompleted_slides.ids),
                    ("partner_id", "=", partner_id),
                    ("identification_number", "=", identification_number),
                ]
            )
        )
        slide_partners.write({"completed": True})
        existing_slides = slide_partners.slide_id
        self.env["slide.slide.partner"].sudo().create(
            [
                {
                    "slide_id": slide.id,
                    "channel_id": slide.channel_id.id,
                    "partner_id": partner_id,
                    "identification_number": identification_number,
                    "vote": 0,
                    "completed": True,
                }
                for slide in uncompleted_slides - existing_slides
            ]
        )
        return True

    def action_mark_uncompleted(self):
        if not self._is_public_with_key():
            return super().action_mark_uncompleted()
        completed_slides = self.filtered(lambda slide: slide.user_has_completed)
        completed_slides._action_set_quiz_done(completed=False)
        self.env["slide.slide.partner"].sudo().search(
            [
                ("slide_id", "in", completed_slides.ids),
                (
                    "partner_id",
                    "=",
                    int(request.session["invite_partner_id"]),
                ),
                (
                    "identification_number",
                    "=",
                    request.session["identification_number"],
                ),
            ]
        ).write({"completed": False})
        return True

    def _action_set_quiz_done(self, completed=True):
        if self._is_public_with_key():
            return True
        return super()._action_set_quiz_done(completed=completed)

    def _compute_quiz_info(self, target_partner, quiz_done=False):
        result = super()._compute_quiz_info(target_partner, quiz_done=quiz_done)
        if self._is_public_with_key():
            slide_partners = (
                self.env["slide.slide.partner"]
                .sudo()
                .search(
                    [
                        ("slide_id", "in", self.ids),
                        (
                            "partner_id",
                            "=",
                            int(request.session.get("invite_partner_id")),
                        ),
                        (
                            "identification_number",
                            "=",
                            request.session.get("identification_number"),
                        ),
                    ]
                )
            )
            slide_partners_map = {sp.slide_id.id: sp for sp in slide_partners}
            for slide in self:
                if not slide.question_ids:
                    gains = [0]
                else:
                    gains = [
                        slide.quiz_first_attempt_reward,
                        slide.quiz_second_attempt_reward,
                        slide.quiz_third_attempt_reward,
                        slide.quiz_fourth_attempt_reward,
                    ]
                result[slide.id] = {
                    "quiz_karma_max": gains[
                        0
                    ],  # what could be gained if succeed at first try
                    "quiz_karma_gain": gains[0],  # what would be gained at next test
                    "quiz_karma_won": 0,  # what has been gained
                    "quiz_attempts_count": 0,  # number of attempts
                }
                slide_partner = slide_partners_map.get(slide.id)
                if (
                    slide.question_ids
                    and slide_partner
                    and slide_partner.quiz_attempts_count
                ):
                    result[slide.id]["quiz_karma_gain"] = (
                        gains[slide_partner.quiz_attempts_count]
                        if slide_partner.quiz_attempts_count < len(gains)
                        else gains[-1]
                    )
                    result[slide.id]["quiz_attempts_count"] = (
                        slide_partner.quiz_attempts_count
                    )
                    if quiz_done or slide_partner.completed:
                        result[slide.id]["quiz_karma_won"] = (
                            gains[slide_partner.quiz_attempts_count - 1]
                            if slide_partner.quiz_attempts_count < len(gains)
                            else gains[-1]
                        )
        return result

    @api.model
    def _search(
        self,
        domain,
        offset=0,
        limit=None,
        order=None,
        bypass_access=False,
        **kwargs,
    ):
        participations = self.env["slide.channel"]._get_public_key_participations()
        if participations:
            public_domain = (
                Domain("channel_id.website_published", "=", True)
                & Domain("website_published", "=", True)
                & (
                    (
                        Domain(
                            "channel_id.visibility",
                            "in",
                            ["public", "link"],
                        )
                        & (
                            Domain("is_category", "=", True)
                            | Domain("is_preview", "=", True)
                        )
                    )
                    | Domain(
                        "channel_id",
                        "in",
                        participations.channel_id.ids,
                    )
                )
            )
            domain = Domain(domain) & public_domain
            bypass_access = True
        return super()._search(
            domain,
            offset=offset,
            limit=limit,
            order=order,
            bypass_access=bypass_access,
            **kwargs,
        )

    def _check_access(self, operation):
        if operation == "read" and self._is_public_with_key():
            return None
        return super()._check_access(operation)
