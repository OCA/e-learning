# Copyright 2025 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models
from odoo.http import request
from odoo.tools import sql


class SlideSlidePartner(models.Model):
    _inherit = "slide.slide.partner"

    identification_number = fields.Char()

    _sql_constraints = [
        (
            "slide_partner_uniq",
            "CHECK (true)",
            "Constraint disabled: allowing repeated partner on the same slide.",
        ),
        (
            "unique_slide_identification",
            "unique(slide_id, identification_number)",
            "The identification number must be unique!",
        ),
    ]


class SlideSlide(models.Model):
    _inherit = "slide.slide"

    def _is_public_with_key(self):
        if request:
            identification_number = request.session.get("identification_number", False)
            invite_hash = request.session.get("invite_hash", False)
            invite_partner_id = request.session.get("invite_partner_id", False)
            return bool(
                self.env.user._is_public()
                and identification_number
                and invite_hash
                and invite_partner_id
            )
        return False

    def _compute_user_membership_id(self):
        res = super()._compute_user_membership_id()
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
            for record in self:
                record.user_membership_id = next(
                    (
                        slide_partner
                        for slide_partner in slide_partners
                        if slide_partner.slide_id == record
                    ),
                    self.env["slide.slide.partner"],
                )
                record.user_vote = record.user_membership_id.vote
        return res

    def _action_vote(self, upvote=True):
        karma_before = self.env.user.karma
        res = super()._action_vote(upvote)
        # If the user is public with password, resets the points to the previous value.
        if self.env.user._is_public() and any(
            slide.user_membership_id.identification_number for slide in self
        ):
            self.env.user.sudo().write({"karma": karma_before})
        return res

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
            existing_sudo.write({"completed": True})
            new_slides = self_sudo - existing_sudo.mapped("slide_id")
            SlidePartnerSudo.create(
                [
                    {
                        "slide_id": new_slide.id,
                        "channel_id": new_slide.channel_id.id,
                        "partner_id": int(invite_partner_id),
                        "vote": 0,
                        "completed": True,
                        "identification_number": identification_number,
                    }
                    for new_slide in new_slides
                ]
            )
            return True
        return super()._action_mark_completed()

    def _action_set_quiz_done(self, completed=True):
        points_before = self.env.user.karma
        res = super()._action_set_quiz_done(completed=completed)
        # If the user is public with password, resets the points to the previous value.
        if self.env.user._is_public() and any(
            slide.user_membership_id.identification_number for slide in self
        ):
            self.env.user.sudo().write({"karma": points_before})
        return res

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

    def _apply_ir_rules(self, query, mode="read"):
        if self._is_public_with_key():
            return
        return super()._apply_ir_rules(query, mode="read")

    def check_access_rule(self, operation):
        if self._is_public_with_key():
            return
        return super().check_access_rule(operation)
