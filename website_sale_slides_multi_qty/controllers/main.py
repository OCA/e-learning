# Copyright 2025 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
import re

from dateutil.relativedelta import relativedelta

from odoo import _, fields, http
from odoo.http import request
from odoo.tools import consteq

from odoo.addons.website_slides.controllers.main import WebsiteSlides


class WebsiteSaleSlides(WebsiteSlides):
    def _normalize_identification_number(self, value):
        return re.sub(r"[^0-9A-Z]", "", (value or "").strip().upper())

    def _set_viewed_slide(self, slide, quiz_attempts_inc=False):
        identification_number = request.session.get("identification_number", False)
        if (
            request.env.user._is_public()
            and slide.channel_id.is_member
            and identification_number
        ):
            slide.action_set_viewed(quiz_attempts_inc=quiz_attempts_inc)
            return True
        return super()._set_viewed_slide(slide, quiz_attempts_inc=quiz_attempts_inc)

    def _get_slide_detail(self, slide):
        values = super()._get_slide_detail(slide)
        identification_number = request.session.get("identification_number", False)
        # Prevent them from attempting to post comments if they do not have a partner_id
        if identification_number and "message_post_pid" in values:
            values["message_post_pid"] = False
        return values

    def _get_slide_quiz_data(self, slide):
        if not slide._is_public_with_key():
            return super()._get_slide_quiz_data(slide)
        is_designer = request.env.user.has_group("website.group_website_designer")
        slides_resources = (
            slide.sudo().slide_resource_ids if slide.channel_id.is_member else []
        )
        values = {
            "slide_description": slide.description,
            "slide_questions": [
                {
                    "answer_ids": [
                        {
                            "comment": answer.comment if is_designer else None,
                            "id": answer.id,
                            "is_correct": answer.is_correct
                            if slide.user_has_completed or is_designer
                            else None,
                            "text_value": answer.text_value,
                        }
                        for answer in question.sudo().answer_ids
                    ],
                    "id": question.id,
                    "question": question.question,
                }
                for question in slide.question_ids
            ],
            "slide_resource_ids": [
                {
                    "display_name": resource.display_name,
                    "download_url": resource.download_url,
                    "id": resource.id,
                    "link": resource.link,
                    "resource_type": resource.resource_type,
                }
                for resource in slides_resources
            ],
        }
        if "slide_answer_quiz" in request.session:
            slide_answer_quiz = json.loads(request.session["slide_answer_quiz"])
            if str(slide.id) in slide_answer_quiz:
                values["session_answers"] = slide_answer_quiz[str(slide.id)]
        values.update(self._get_slide_quiz_partner_info(slide))
        return values

    def _get_channel_progress(self, channel, include_quiz=False):
        values = super()._get_channel_progress(channel, include_quiz=include_quiz)
        identification_number = request.session.get("identification_number", False)
        if request.website.is_public_user() and identification_number:
            slides = (
                request.env["slide.slide"]
                .sudo()
                .search([("channel_id", "=", channel.id)])
            )
            slide_partners = (
                request.env["slide.slide.partner"]
                .sudo()
                .search(
                    [
                        ("channel_id", "=", channel.id),
                        (
                            "partner_id",
                            "=",
                            int(request.session.get("invite_partner_id")),
                        ),
                        ("identification_number", "=", identification_number),
                        ("slide_id", "in", slides.ids),
                    ]
                )
            )
            for slide_partner in slide_partners:
                values[slide_partner.slide_id.id].update(slide_partner.read()[0])
                if slide_partner.slide_id in values:
                    values[slide_partner.slide_id].update(slide_partner.read()[0])
                    if slide_partner.slide_id.sudo().question_ids:
                        gains = [
                            slide_partner.slide_id.quiz_first_attempt_reward,
                            slide_partner.slide_id.quiz_second_attempt_reward,
                            slide_partner.slide_id.quiz_third_attempt_reward,
                            slide_partner.slide_id.quiz_fourth_attempt_reward,
                        ]
                        values[slide_partner.slide_id.id]["quiz_gain"] = (
                            gains[slide_partner.quiz_attempts_count]
                            if slide_partner.quiz_attempts_count < len(gains)
                            else gains[-1]
                        )
        return values

    def _check_identification_number(self, identification_number, partner):
        # Validate ID depending on the country of the parent partner
        if not identification_number or not partner or not partner.sudo().country_id:
            return True  # Allow if insufficient data
        return request.env["res.partner"].simple_vat_check(
            partner.country_id.code.upper(), identification_number.strip().upper()
        )

    def _session_data(self):
        return {
            "invite_hash": request.session.get("invite_hash", False),
            "identification_number": request.session.get(
                "identification_number", False
            ),
            "invite_partner_id": int(request.session.get("invite_partner_id", False)),
        }

    def _delete_session_data(self):
        request.session.pop("invite_hash", None)
        request.session.pop("identification_number", None)
        request.session.pop("invite_partner_id", None)

    def _set_session_data(self, identification_number, invite_partner_id, invite_hash):
        request.session["identification_number"] = identification_number
        request.session["invite_partner_id"] = invite_partner_id
        request.session["invite_hash"] = invite_hash

    @http.route("/slides/is_public_with_key", type="json", auth="public", website=True)
    def session_data(self):
        return self._session_data()

    @http.route()
    def channel(
        self,
        channel=False,
        channel_id=False,
        category=None,
        category_id=False,
        tag=None,
        page=1,
        slide_category=None,
        uncategorized=False,
        sorting=None,
        search=None,
        **kw,
    ):
        session_data = self._session_data()
        participation = False
        if session_data["invite_hash"]:
            participation = (
                request.env["slide.channel.partner"]
                .sudo()
                .search(
                    [
                        ("invitation_hash", "=", session_data["invite_hash"]),
                        (
                            "identification_number",
                            "=",
                            session_data["identification_number"],
                        ),
                        ("channel_id", "=", channel_id),
                    ],
                    limit=1,
                )
            )
        if participation and participation.channel_id.id != channel_id:
            # If there is no valid participation, we delete the session data.
            self._delete_session_data()
        res = super().channel(
            channel=channel,
            channel_id=channel_id,
            category=category,
            category_id=category_id,
            tag=tag,
            page=page,
            slide_category=slide_category,
            uncategorized=uncategorized,
            sorting=sorting,
            search=search,
            **kw,
        )
        channel_rec = channel or request.env["slide.channel"].browse(int(channel_id))
        res.qcontext["can_enroll"] = self._can_user_register(
            (participation.channel_id if participation else channel_rec),
            request.env.user,
        ) or bool(kw.get("is_invite", False))
        channel_error = request.session.pop("channel_error", None)
        if channel_error:
            res.qcontext["channel_error"] = channel_error
        show_modal_to_join = request.session.pop("show_modal_to_join", None)
        if show_modal_to_join:
            res.qcontext["show_modal_to_join"] = show_modal_to_join
        show_identification_form = request.session.pop("show_identification_form", None)
        if show_identification_form:
            res.qcontext["show_identification_form"] = show_identification_form
        return res

    @http.route(
        "/slides/channel/join_with_vat",
        type="http",
        auth="user",
        methods=["POST"],
        website=True,
    )
    def join_with_vat(self, **kwargs):
        # Registered user enters VAT before accessing the course.
        channel_id = int(kwargs.get("channel_id"))
        invite_partner_id = kwargs.get("invite_partner_id")
        invite_hash = kwargs.get("invite_hash")
        redirect_url = (
            f"/slides/{channel_id}"
            f"/invite?invite_partner_id={invite_partner_id}"
            f"&invite_hash={invite_hash}"
        )
        channel = request.env["slide.channel"].browse(channel_id).exists()
        if not channel:
            return self._redirect_to_slides_main("no_channel")
        target_partner = request.env.user.partner_id
        identification_number = kwargs.get("identification_number", False)
        if not self._check_identification_number(identification_number, target_partner):
            request.session["channel_error"] = _("Invalid identification number.")
            return request.redirect(redirect_url)
        identification_number_norm = self._normalize_identification_number(
            identification_number
        )
        existing_enroll = channel.sudo().channel_partner_ids.filtered(
            lambda r: self._normalize_identification_number(r.identification_number)
            == identification_number_norm
        )[:1]
        # Save VAT in user contact
        target_partner.sudo().write(
            {
                "vat": identification_number,
            }
        )
        if existing_enroll:
            existing_enroll.write(
                {
                    "partner_id": target_partner.id,
                }
            )
            return request.redirect(f"/slides/{channel_id}")
        request.session.pop("show_identification_form", None)
        join_url = f"/slides/{channel.id}/join" + (
            f"?invite_partner_id={invite_partner_id}" if invite_partner_id else ""
        )
        return request.redirect(join_url)

    @http.route(
        "/slides/channel/join_with_id",
        type="http",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def slide_channel_join_with_id(self, **kw):
        identification_number = kw.get("identification_number", False)
        channel_id = int(kw.get("channel_id"))
        invite_partner_id = int(kw.get("invite_partner_id"))
        invite_hash = kw.get("invite_hash")
        redirect_url = (
            f"/slides/{channel_id}"
            f"/invite?invite_partner_id={invite_partner_id}"
            f"&invite_hash={invite_hash}"
        )
        channel = request.env["slide.channel"].browse(channel_id).exists()
        if not channel:
            return self._redirect_to_slides_main("no_channel")
        identification_number_norm = self._normalize_identification_number(
            identification_number
        )
        slide_channel_partner = channel.sudo().channel_partner_ids.filtered(
            lambda r: self._normalize_identification_number(r.identification_number)
            == identification_number_norm
        )[:1]
        if slide_channel_partner and slide_channel_partner.partner_id.user_ids:
            login_url = f"/web/login?redirect=/slides/{channel_id}"
            request.session["channel_error"] = (
                _(
                    "This identification number is already linked to a registered "
                    "account. Please <a href='%s'>log in</a> to access the course."
                )
                % login_url
            )
            return request.redirect(redirect_url)
        slide_channel_partner_name = (
            (kw.get("slide_channel_partner_name") or "").strip().upper()
        )
        slide_channel_partner_email = kw.get("slide_channel_partner_email")
        slide_channel_partner_phone = kw.get("slide_channel_partner_phone")
        target_partner = request.env["res.partner"].browse(invite_partner_id)
        parent_channel_partner = channel.sudo().channel_partner_ids.filtered(
            lambda x: x.sale_order_line_ids and x.invitation_hash == invite_hash
        )
        if not slide_channel_partner:
            if (
                not slide_channel_partner_name
                or not slide_channel_partner_email
                or not slide_channel_partner_phone
            ):
                request.session["channel_error"] = _(
                    "There is no participation for this key"
                )
                return request.redirect(redirect_url)
            if not self._check_identification_number(
                identification_number, target_partner
            ):
                request.session["channel_error"] = _("Invalid identification number.")
                return request.redirect(redirect_url)
            self._add_new_member(
                channel,
                target_partner,
                parent_channel_partner,
                slide_channel_partner_name=slide_channel_partner_name,
                slide_channel_partner_email=slide_channel_partner_email,
                slide_channel_partner_phone=slide_channel_partner_phone,
                identification_number=identification_number,
                is_public_slide_channel_partner=True,
            )
        self._set_session_data(identification_number, invite_partner_id, invite_hash)
        return request.redirect(f"/slides/{channel_id}")

    @http.route("/slides/<int:channel_id>/join", type="http", auth="user", website=True)
    def slide_channel_join_course(self, channel_id, **kwargs):
        channel = request.env["slide.channel"].browse(channel_id).exists()
        if not channel:
            return self._redirect_to_slides_main("no_channel")
        target_partner = request.env.user.partner_id
        if target_partner.vat:
            identification_number_norm = self._normalize_identification_number(
                target_partner.vat
            )
            existing_enroll = channel.sudo().channel_partner_ids.filtered(
                lambda r: self._normalize_identification_number(r.identification_number)
                == identification_number_norm
            )[:1]
            if existing_enroll and existing_enroll.partner_id != target_partner:
                existing_enroll.write({"partner_id": target_partner.id})
                return request.redirect(f"/slides/{channel_id}")
        parent_channel_partners = channel.sudo().channel_partner_ids.filtered(
            lambda x: x.available_registrations > 1
        )
        invite_partner_id = kwargs.get("invite_partner_id", False)
        for parent_channel_partner in parent_channel_partners:
            if parent_channel_partner.partner_id == target_partner:
                self._add_new_member(channel, target_partner, parent_channel_partner)
            else:
                if (
                    parent_channel_partner.partner_id.commercial_partner_id
                    == target_partner.commercial_partner_id
                ):
                    self._add_new_member(
                        channel, target_partner, parent_channel_partner
                    )
        if invite_partner_id:
            parent_channel_partner = parent_channel_partners.filtered(
                lambda x: x.partner_id.id == int(invite_partner_id) and not x.parent_id
            )
            self._add_new_member(channel, target_partner, parent_channel_partner)
        return request.redirect(f"/slides/{channel_id}")

    @http.route()
    def slide_channel_invite(self, channel_id, invite_partner_id, invite_hash):
        res = super().slide_channel_invite(channel_id, invite_partner_id, invite_hash)
        self._delete_session_data()
        redirect_url = (
            f"/slides/{channel_id}?is_invite=1&invite_partner_id={invite_partner_id}"
        )
        # No user is logged.
        if request.website.is_public_user():
            request.session["invite_partner_id"] = int(invite_partner_id)
            request.session["invite_hash"] = invite_hash
            request.session["show_modal_to_join"] = True
            return request.redirect(redirect_url)
        # A user is logged
        channel = request.env["slide.channel"].browse(int(channel_id)).exists()
        enroll = channel.sudo().channel_partner_ids.filtered(
            lambda x: x.partner_id == request.env.user.partner_id
        )
        if not request.env.user.partner_id.id == int(invite_partner_id) and not enroll:
            if not request.env.user.partner_id.vat:
                request.session["show_identification_form"] = True
            return request.redirect(redirect_url)
        return res

    def _can_user_register(self, channel, user):
        # Check if the user meets the conditions to register for the course.
        partner = user.partner_id
        enroll = channel.sudo().channel_partner_ids.filtered(
            lambda x: x.partner_id == partner and not x.is_public_slide_channel_partner
        )
        # If the accessing user is the one who has acquired and does not have a
        # sub-participation
        if (
            len(enroll) == 1
            and enroll.available_registrations > 1
            and enroll.available_registrations > enroll.used_registrations
        ):
            return True
        # If the accessing user is a contact of the company or of the partner who has
        # acquired the shareholding
        enroll_comercial = channel.sudo().channel_partner_ids.filtered(
            lambda x: x.partner_id.commercial_partner_id
            == partner.commercial_partner_id
        )
        enroll_comercial_parent = enroll_comercial.filtered("child_channel_partner_ids")
        if (
            partner.id not in enroll_comercial.partner_id.ids
            and enroll_comercial_parent.available_registrations
            > enroll_comercial_parent.used_registrations
        ):
            return True
        return False

    def _add_new_member(
        self, channel, target_partner, parent_channel_partner, **kwargs
    ):
        channel._action_add_members(
            target_partners=target_partner,
            parent_channel_partner=parent_channel_partner,
            identification_number=(
                kwargs.get("identification_number") or target_partner.vat
            ),
            slide_channel_partner_name=kwargs.get("slide_channel_partner_name", False),
            slide_channel_partner_email=kwargs.get(
                "slide_channel_partner_email", False
            ),
            slide_channel_partner_phone=kwargs.get(
                "slide_channel_partner_phone", False
            ),
            is_public_slide_channel_partner=kwargs.get(
                "is_public_slide_channel_partner", False
            ),
        )

    @staticmethod
    def _get_channel_values_from_invite(channel_id, invite_hash, invite_partner_id):
        # Static method overridden to handle sub-participations:
        # when multiple participations exist for the same partner,
        # only participations without parent_id (main participations) are considered.
        channel_sudo = request.env["slide.channel"].browse(channel_id).exists().sudo()
        partner_sudo = (
            request.env["res.partner"].browse(invite_partner_id).exists().sudo()
        )
        if not partner_sudo or not channel_sudo.is_published:
            return {
                "invite_error": "no_partner"
                if not partner_sudo
                else "no_channel"
                if not channel_sudo
                else "no_rights"
            }
        # Apply custom logic to consider only participations without a parent_id
        # (main participations).
        channel_partner_sudo = channel_sudo.channel_partner_all_ids.filtered(
            lambda cp: cp.partner_id.id == invite_partner_id and not cp.parent_id
        )
        if not channel_partner_sudo:
            return {"invite_error": "expired"}
        if not consteq(channel_partner_sudo._get_invitation_hash(), invite_hash):
            return {"invite_error": "hash_fail"}
        if channel_partner_sudo.member_status == "invited":
            if (
                not channel_partner_sudo.last_invitation_date
                or channel_partner_sudo.last_invitation_date + relativedelta(months=3)
                < fields.Datetime.now()
            ):
                return {"invite_error": "expired"}
        return {
            "invite_channel": channel_sudo,
            "invite_channel_partner": channel_partner_sudo,
            "invite_preview": True,
            "is_partner_without_user": not partner_sudo.user_ids,
            "invite_partner": partner_sudo,
        }

    # SLIDE.SLIDE UTILS

    @http.route()
    def slide_set_completed(self, slide_id):
        session_data = self._session_data() or {}
        invite_hash = session_data.get("invite_hash", False)
        identification_number = session_data.get("identification_number", False)
        invite_partner_id = session_data.get("invite_partner_id", False)
        if (
            request.website.is_public_user()
            and identification_number
            and invite_partner_id
            and invite_hash
        ):
            fetch_res = self._fetch_slide(slide_id)
            if fetch_res.get("error"):
                return fetch_res
            self._slide_mark_completed(fetch_res["slide"])
            next_category = fetch_res["slide"]._get_next_category()
            return {
                "channel_completion": fetch_res["slide"].channel_id.completion,
                "next_category_id": next_category.id if next_category else False,
            }
        return super().slide_set_completed(slide_id)

    # QUIZ SECTION

    @http.route()
    def slide_quiz_submit(self, slide_id, answer_ids):
        session_data = self._session_data() or {}
        invite_hash = session_data.get("invite_hash", False)
        identification_number = session_data.get("identification_number", False)
        invite_partner_id = session_data.get("invite_partner_id", False)
        values = super().slide_quiz_submit(slide_id, answer_ids)
        if (
            request.website.is_public_user()
            and identification_number
            and invite_partner_id
            and invite_hash
        ):
            values = {}
            fetch_res = self._fetch_slide(slide_id)
            if fetch_res.get("error"):
                return fetch_res
            slide = fetch_res["slide"]
            if slide.user_has_completed:
                self._channel_remove_session_answers(slide.channel_id, slide)
                return {"error": "slide_quiz_done"}
            all_questions = (
                request.env["slide.question"]
                .sudo()
                .search([("slide_id", "=", slide.id)])
            )
            user_answers = (
                request.env["slide.answer"].sudo().search([("id", "in", answer_ids)])
            )
            if user_answers.mapped("question_id") != all_questions:
                return {"error": "slide_quiz_incomplete"}
            user_bad_answers = user_answers.filtered(
                lambda answer: not answer.is_correct
            )
            self._set_viewed_slide(slide, quiz_attempts_inc=True)
            quiz_info = self._get_slide_quiz_partner_info(slide, quiz_done=True)
            rank_progress = {}
            if not user_bad_answers:
                rank_progress["previous_rank"] = self._get_rank_values(request.env.user)
                slide._action_mark_completed()
                rank_progress["new_rank"] = self._get_rank_values(request.env.user)
                rank_progress.update(
                    {
                        "description": request.env.user.rank_id.description,
                        "last_rank": not request.env.user._get_next_rank(),
                        "level_up": rank_progress["previous_rank"]["lower_bound"]
                        != rank_progress["new_rank"]["lower_bound"],
                    }
                )
            self._channel_remove_session_answers(slide.channel_id, slide)
            values.update(
                {
                    "answers": {
                        answer.question_id.id: {
                            "is_correct": answer.is_correct,
                            "comment": answer.comment,
                        }
                        for answer in user_answers
                    },
                    "completed": slide.user_has_completed,
                    "channel_completion": slide.channel_id.completion,
                    "quizKarmaWon": quiz_info["quiz_karma_won"],
                    "quizKarmaGain": quiz_info["quiz_karma_gain"],
                    "quizAttemptsCount": quiz_info["quiz_attempts_count"],
                    "rankProgress": rank_progress,
                }
            )
        return values

    # PROFILE

    def _prepare_user_slides_profile(self, user):
        invite_hash = request.session.get("invite_hash", False)
        identification_number = request.session.get("identification_number", False)
        invite_partner_id = request.session.get("invite_partner_id", False)
        values = super()._prepare_user_slides_profile(user)
        if (
            request.website.is_public_user()
            and identification_number
            and invite_partner_id
            and invite_hash
        ):
            courses = (
                request.env["slide.channel.partner"]
                .sudo()
                .search(
                    [
                        (
                            "partner_id",
                            "=",
                            int(invite_partner_id),
                            ("identification_number", "=", identification_number),
                        )
                    ]
                )
            )
            courses_completed = courses.filtered(
                lambda c: c.member_status == "completed"
            )
            courses_ongoing = courses - courses_completed
            values.update(
                {
                    "uid": request.env.user.id,
                    "user": user,
                    "main_object": user,
                    "courses_completed": courses_completed,
                    "courses_ongoing": courses_ongoing,
                    "is_profile_page": True,
                    "my_profile": True,
                }
            )
        return values
