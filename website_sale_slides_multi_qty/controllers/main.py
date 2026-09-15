# Copyright 2025 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
import re

from dateutil.relativedelta import relativedelta
from markupsafe import Markup

from odoo import fields, http, tools
from odoo.http import request
from odoo.tools import consteq

from odoo.addons.website_slides.controllers.main import WebsiteSlides


class WebsiteSaleSlides(WebsiteSlides):
    def _normalize_identification_number(self, value):
        return re.sub(r"[^0-9A-Z]", "", (value or "").strip().upper())

    def _register_public_participation(self, participation, target_partner):
        previous_partner = participation.partner_id
        participation.write(
            {
                "partner_id": target_partner.id,
                "is_public_slide_channel_partner": False,
            }
        )
        slide_partners = (
            request.env["slide.slide.partner"]
            .sudo()
            .search(
                [
                    ("channel_id", "=", participation.channel_id.id),
                    ("partner_id", "=", previous_partner.id),
                    (
                        "identification_number",
                        "=",
                        participation.identification_number,
                    ),
                ]
            )
        )
        slide_partners.write({"partner_id": target_partner.id})

    def _set_viewed_slide(self, slide, quiz_attempts_inc=False):
        if slide._is_public_with_key():
            slide.action_set_viewed(quiz_attempts_inc=quiz_attempts_inc)
            return True
        return super()._set_viewed_slide(
            slide,
            quiz_attempts_inc=quiz_attempts_inc,
        )

    def _get_slide_detail(self, slide):
        values = super()._get_slide_detail(slide)
        # Prevent them from attempting to post comments if they do not have a partner_id
        if slide._is_public_with_key() and "message_post_pid" in values:
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
        values = super()._get_channel_progress(
            channel,
            include_quiz=include_quiz,
        )
        if not channel._is_public_with_key():
            return values
        slide_partners = (
            request.env["slide.slide.partner"]
            .sudo()
            .search(
                [
                    ("channel_id", "=", channel.id),
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
                    ("slide_id", "in", list(values)),
                ]
            )
        )
        for slide_partner in slide_partners:
            slide_id = slide_partner.slide_id.id
            values[slide_id].update(slide_partner.read()[0])
            if slide_partner.slide_id.sudo().question_ids:
                gains = [
                    slide_partner.slide_id.quiz_first_attempt_reward,
                    slide_partner.slide_id.quiz_second_attempt_reward,
                    slide_partner.slide_id.quiz_third_attempt_reward,
                    slide_partner.slide_id.quiz_fourth_attempt_reward,
                ]
                values[slide_id]["quiz_gain"] = (
                    gains[slide_partner.quiz_attempts_count]
                    if slide_partner.quiz_attempts_count < len(gains)
                    else gains[-1]
                )
        return values

    def _check_identification_number(self, identification_number, partner):
        # Validate ID depending on the country of the parent partner
        if not identification_number or not partner or not partner.sudo().country_id:
            return True  # Allow if insufficient data
        return request.env["res.partner"]._check_vat_number(
            partner.sudo().country_id.code.upper(),
            identification_number.strip().upper(),
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

    @http.route(
        "/slides/is_public_with_key",
        type="jsonrpc",
        auth="public",
        website=True,
    )
    def is_public_with_key(self):
        participations = request.env["slide.channel"]._get_public_key_participations()
        return {"is_public_with_key": bool(participations)}

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
        channel_rec = (
            channel or request.env["slide.channel"].browse(int(channel_id)).exists()
        )
        session_data = self._session_data()
        has_session_data = all(
            (
                session_data["identification_number"],
                session_data["invite_hash"],
                session_data["invite_partner_id"],
            )
        )
        if (
            has_session_data
            and not request.env["slide.channel"]._get_public_key_participations()
        ):
            # Delete the session only when it no longer identifies a participation.
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
        if not getattr(res, "qcontext", None):
            return res
        res.qcontext["can_enroll"] = self._can_user_register(
            channel_rec,
            request.env.user,
        ) or bool(kw.get("is_invite", False))
        channel_error = request.session.pop("channel_error", None)
        if channel_error:
            res.qcontext["channel_error"] = Markup(channel_error)
        show_modal_to_join = request.session.pop("show_modal_to_join", None)
        if show_modal_to_join:
            res.qcontext["show_modal_to_join"] = show_modal_to_join
        show_identification_form = request.session.pop(
            "show_identification_form",
            None,
        )
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
        invite_partner_id = int(kwargs.get("invite_partner_id"))
        invite_hash = kwargs.get("invite_hash")
        redirect_url = (
            f"/slides/{channel_id}"
            f"/invite?invite_partner_id={invite_partner_id}"
            f"&invite_hash={invite_hash}"
        )
        invite_values = self._get_channel_values_from_invite(
            channel_id,
            invite_hash,
            invite_partner_id,
        )
        if not invite_values.get("invite_preview"):
            return request.redirect(redirect_url)
        channel = invite_values["invite_channel"]
        target_partner = request.env.user.partner_id
        identification_number = kwargs.get(
            "identification_number",
            False,
        )
        if not self._check_identification_number(
            identification_number,
            target_partner,
        ):
            request.session["channel_error"] = request.env._(
                "Invalid identification number."
            )
            return request.redirect(redirect_url)
        identification_number_norm = self._normalize_identification_number(
            identification_number
        )
        existing_enroll = channel.sudo().channel_partner_ids.filtered(
            lambda participation: (
                participation.parent_id
                and participation.is_public_slide_channel_partner
                and self._normalize_identification_number(
                    participation.identification_number
                )
                == identification_number_norm
            )
        )[:1]
        # Save VAT in user contact
        target_partner.sudo().write(
            {
                "vat": identification_number,
            }
        )
        if existing_enroll:
            self._register_public_participation(
                existing_enroll,
                target_partner,
            )
            request.session.pop("show_identification_form", None)
            return request.redirect(f"/slides/{channel_id}")
        request.session.pop("show_identification_form", None)
        join_url = (
            f"/slides/{channel.id}/join"
            f"?invite_partner_id={invite_partner_id}"
            f"&invite_hash={invite_hash}"
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
        identification_number = kw.get("identification_number")
        channel_id = int(kw.get("channel_id"))
        invite_partner_id = int(kw.get("invite_partner_id"))
        invite_hash = kw.get("invite_hash")
        redirect_url = (
            f"/slides/{channel_id}"
            f"/invite?invite_partner_id={invite_partner_id}"
            f"&invite_hash={invite_hash}"
        )
        invite_values = self._get_channel_values_from_invite(
            channel_id,
            invite_hash,
            invite_partner_id,
        )
        if not invite_values.get("invite_preview"):
            return request.redirect(redirect_url)
        channel = invite_values["invite_channel"]
        target_partner = invite_values["invite_partner"]
        parent_channel_partner = invite_values["invite_channel_partner"]
        identification_number_norm = self._normalize_identification_number(
            identification_number
        )

        def _find_participation():
            return channel.sudo().channel_partner_ids.filtered(
                lambda participation: (
                    participation.parent_id == parent_channel_partner
                    and self._normalize_identification_number(
                        participation.identification_number
                    )
                    == identification_number_norm
                )
            )[:1]

        slide_channel_partner = _find_participation()
        if slide_channel_partner and slide_channel_partner.partner_id.user_ids:
            login_url = f"/web/login?redirect=/slides/{channel_id}"
            request.session["channel_error"] = request.env._(
                "This identification number is already linked to a "
                "registered account. Please <a href='%s'>log in</a> "
                "to access the course.",
                login_url,
            )
            return request.redirect(redirect_url)
        if not slide_channel_partner:
            slide_channel_partner_name = (
                (kw.get("slide_channel_partner_name") or "").strip().upper()
            )
            slide_channel_partner_email = kw.get("slide_channel_partner_email")
            slide_channel_partner_phone = kw.get("slide_channel_partner_phone")
            if (
                not slide_channel_partner_name
                or not slide_channel_partner_email
                or not slide_channel_partner_phone
            ):
                request.session["channel_error"] = request.env._(
                    "There is no participation for this key"
                )
                return request.redirect(redirect_url)
            if not self._check_identification_number(
                identification_number,
                target_partner,
            ):
                request.session["channel_error"] = request.env._(
                    "Invalid identification number."
                )
                return request.redirect(redirect_url)
            if parent_channel_partner.remaining_registrations <= 0:
                request.session["channel_error"] = request.env._(
                    "No registrations available for this course."
                )
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
            slide_channel_partner = _find_participation()
        if not slide_channel_partner:
            request.session["channel_error"] = request.env._(
                "There is no participation for this key"
            )
            return request.redirect(redirect_url)
        self._set_session_data(
            slide_channel_partner.identification_number,
            invite_partner_id,
            invite_hash,
        )
        return request.redirect(f"/slides/{channel_id}")

    @http.route("/slides/<int:channel_id>/join", type="http", auth="user", website=True)
    def slide_channel_join_course(self, channel_id, **kwargs):
        channel = request.env["slide.channel"].browse(channel_id).exists()
        if not channel:
            return self._redirect_to_slides_main("no_channel")
        target_partner = request.env.user.partner_id
        channel_partners = channel.sudo().channel_partner_ids
        # Convert an existing public participation into a registered one.
        if target_partner.vat:
            identification_number_norm = self._normalize_identification_number(
                target_partner.vat
            )
            public_participation = channel_partners.filtered(
                lambda participation: (
                    participation.parent_id
                    and participation.is_public_slide_channel_partner
                    and self._normalize_identification_number(
                        participation.identification_number
                    )
                    == identification_number_norm
                )
            )[:1]
            if public_participation:
                self._register_public_participation(
                    public_participation,
                    target_partner,
                )
                return request.redirect(f"/slides/{channel_id}")
        # Do not consume another registration if the user is already enrolled.
        existing_participation = channel_partners.filtered(
            lambda participation: (
                participation.partner_id == target_partner
                and not participation.is_public_slide_channel_partner
                and (
                    participation.parent_id
                    or participation._is_individual_course_registration()
                )
            )
        )[:1]
        if existing_participation:
            return request.redirect(f"/slides/{channel_id}")
        invite_partner_id = kwargs.get("invite_partner_id")
        if invite_partner_id:
            parent_participation = channel_partners.filtered(
                lambda participation: (
                    not participation.parent_id
                    and participation.partner_id.id == int(invite_partner_id)
                    and participation.sale_order_line_ids
                    and participation.remaining_registrations > 0
                )
            )[:1]
        else:
            # The buyer or one of their contacts can consume a registration.
            parent_participation = channel_partners.filtered(
                lambda participation: (
                    not participation.parent_id
                    and participation.sale_order_line_ids
                    and participation.remaining_registrations > 0
                    and participation.partner_id.commercial_partner_id
                    == target_partner.commercial_partner_id
                )
            )[:1]
        if parent_participation:
            self._add_new_member(channel, target_partner, parent_participation)
        return request.redirect(f"/slides/{channel_id}")

    @http.route()
    def slide_channel_invite(self, channel_id, invite_partner_id, invite_hash):
        res = super().slide_channel_invite(channel_id, invite_partner_id, invite_hash)
        self._delete_session_data()
        invite_values = self._get_channel_values_from_invite(
            int(channel_id),
            invite_hash,
            int(invite_partner_id),
        )
        if not invite_values.get("invite_preview"):
            return res
        redirect_url = (
            f"/slides/{channel_id}"
            f"?is_invite=1"
            f"&invite_partner_id={invite_partner_id}"
            f"&invite_hash={invite_hash}"
        )
        # No user is logged.
        if request.website.is_public_user():
            request.session["invite_partner_id"] = int(invite_partner_id)
            request.session["invite_hash"] = invite_hash
            request.session["show_modal_to_join"] = True
            return request.redirect(redirect_url)
        channel = invite_values["invite_channel"]
        enroll = channel.sudo().channel_partner_ids.filtered(
            lambda participation: participation.partner_id
            == request.env.user.partner_id
        )
        if request.env.user.partner_id.id != int(invite_partner_id) and not enroll:
            if not request.env.user.partner_id.vat:
                request.session["show_identification_form"] = True
            return request.redirect(redirect_url)
        return res

    def _can_user_register(self, channel, user):
        # Check if the user meets the conditions to register for the course.
        partner = user.partner_id
        channel_partners = channel.sudo().channel_partner_ids
        already_enrolled = channel_partners.filtered(
            lambda registration: (
                registration.partner_id == partner
                and not registration.is_public_slide_channel_partner
                and (
                    registration.parent_id
                    or registration._is_individual_course_registration()
                )
            )
        )[:1]
        if already_enrolled:
            return False
        partner_registrations = channel_partners.filtered(
            lambda registration: (
                registration.partner_id == partner
                and not registration.parent_id
                and not registration.is_public_slide_channel_partner
            )
        )
        # The buyer can consume one of the available registrations.
        if any(
            registration.available_registrations > 1
            and registration.remaining_registrations > 0
            for registration in partner_registrations
        ):
            return True
        company_registrations = channel_partners.filtered(
            lambda registration: (
                not registration.parent_id
                and registration.sale_order_line_ids
                and registration.partner_id.commercial_partner_id
                == partner.commercial_partner_id
            )
        )
        # A contact of the buyer can consume one of the available registrations.
        return partner not in channel_partners.partner_id and any(
            registration.remaining_registrations > 0
            for registration in company_registrations
        )

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
            lambda participation: (
                participation.partner_id.id == invite_partner_id
                and not participation.parent_id
                and participation.active
            )
        )[:1]
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
        if not request.env["slide.channel"]._has_key_session():
            return super().slide_set_completed(slide_id)
        fetch_res = self._fetch_slide(slide_id)
        if fetch_res.get("error"):
            return fetch_res
        slide = fetch_res["slide"]
        if not slide._is_public_with_key():
            return {"error": "slide_access"}
        self._slide_mark_completed(slide)
        next_category = slide._get_next_category()
        return {
            "channel_completion": slide.channel_id.completion,
            "next_category_id": next_category.id if next_category else False,
        }

    @http.route()
    def slide_set_uncompleted(self, slide_id):
        if not request.env["slide.channel"]._has_key_session():
            return super().slide_set_uncompleted(slide_id)
        fetch_res = self._fetch_slide(slide_id)
        if fetch_res.get("error"):
            return fetch_res
        slide = fetch_res["slide"]
        if not slide._is_public_with_key():
            return {"error": "slide_access"}
        self._slide_mark_uncompleted(slide)
        return {
            "channel_completion": slide.channel_id.completion,
            "next_category_id": False,
        }

    @http.route()
    def slide_like(self, slide_id, upvote):
        if not request.env["slide.channel"]._has_key_session():
            return super().slide_like(slide_id, upvote)
        fetch_res = self._fetch_slide(slide_id)
        if fetch_res.get("error"):
            return fetch_res
        slide = fetch_res["slide"]
        if not slide._is_public_with_key():
            return {"error": "slide_access"}
        if not slide.channel_id.allow_comment:
            return {"error": "channel_comment_disabled"}
        if not slide.channel_id.can_vote:
            return {"error": "channel_karma_required"}
        if upvote:
            slide.action_like()
        else:
            slide.action_dislike()
        return {
            "user_vote": slide.user_vote,
            "likes": tools.misc.format_decimalized_number(slide.likes),
            "dislikes": tools.misc.format_decimalized_number(slide.dislikes),
        }

    # QUIZ SECTION

    @http.route()
    def slide_quiz_submit(self, slide_id, answer_ids):
        if not request.env["slide.channel"]._has_key_session():
            return super().slide_quiz_submit(slide_id, answer_ids)
        fetch_res = self._fetch_slide(slide_id)
        if fetch_res.get("error"):
            return fetch_res
        slide = fetch_res["slide"]
        if not slide._is_public_with_key():
            return {"error": "slide_access"}
        if slide.user_has_completed:
            self._channel_remove_session_answers(slide.channel_id, slide)
            return {"error": "slide_quiz_done"}
        all_questions = (
            request.env["slide.question"].sudo().search([("slide_id", "=", slide.id)])
        )
        user_answers = (
            request.env["slide.answer"].sudo().search([("id", "in", answer_ids)])
        )
        if user_answers.mapped("question_id") != all_questions:
            return {"error": "slide_quiz_incomplete"}
        user_bad_answers = user_answers.filtered(lambda answer: not answer.is_correct)
        self._set_viewed_slide(slide, quiz_attempts_inc=True)
        quiz_info = self._get_slide_quiz_partner_info(
            slide,
            quiz_done=True,
        )
        rank_progress = {}
        if not user_bad_answers:
            rank_progress["previous_rank"] = self._get_rank_values(request.env.user)
            slide._action_mark_completed()
            rank_progress["new_rank"] = self._get_rank_values(request.env.user)
            rank_progress.update(
                {
                    "description": request.env.user.rank_id.description,
                    "last_rank": not request.env.user._get_next_rank(),
                    "level_up": (
                        rank_progress["previous_rank"]["lower_bound"]
                        != rank_progress["new_rank"]["lower_bound"]
                    ),
                }
            )
        self._channel_remove_session_answers(slide.channel_id, slide)
        return {
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

    # PROFILE

    def _prepare_user_slides_profile(self, user):
        values = super()._prepare_user_slides_profile(user)
        participations = request.env["slide.channel"]._get_public_key_participations()
        if not participations:
            return values
        courses_completed = participations.filtered(
            lambda participation: participation.member_status == "completed"
        )
        courses_ongoing = participations - courses_completed
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
