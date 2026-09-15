# Copyright 2025-2026 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.http import request


class SlideChannel(models.Model):
    _inherit = "slide.channel"

    def _has_key_session(self):
        return bool(
            request
            and self.env.user._is_public()
            and request.session.get("identification_number")
            and request.session.get("invite_hash")
            and request.session.get("invite_partner_id")
        )

    def _get_public_key_participations(self):
        if not self._has_key_session():
            return self.env["slide.channel.partner"]
        domain = [
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
            (
                "invitation_hash",
                "=",
                request.session["invite_hash"],
            ),
            ("active", "=", True),
        ]
        if self:
            domain.append(("channel_id", "in", self.ids))
        return self.env["slide.channel.partner"].sudo().search(domain)

    def _is_public_with_key(self):
        if not self:
            return False
        authorized_channels = self._get_public_key_participations().channel_id
        return not (self - authorized_channels)

    @api.depends(
        "channel_partner_all_ids.parent_id",
        "channel_partner_all_ids.sale_order_line_ids.product_uom_qty",
        "channel_partner_all_ids.sale_order_line_ids.order_id.state",
    )
    def _compute_membership_values(self):
        res = super()._compute_membership_values()
        if self.env.user._is_public():
            member_channel_ids = set(
                self._get_public_key_participations().channel_id.ids
            )
            for channel in self:
                if channel.id in member_channel_ids:
                    channel.is_member = True
            return res
        participations = (
            self.env["slide.channel.partner"]
            .sudo()
            .search(
                [
                    ("channel_id", "in", self.ids),
                    ("partner_id", "=", self.env.user.partner_id.id),
                    ("member_status", "in", ["joined", "ongoing", "completed"]),
                    ("active", "=", True),
                ]
            )
        )
        member_channel_ids = {
            participation.channel_id.id
            for participation in participations
            if (
                participation.parent_id
                or not participation.sale_order_line_ids
                or participation._is_individual_course_registration()
            )
        }
        for channel in self:
            channel.is_member = channel.id in member_channel_ids
        return res

    def _search_is_member_channel_ids(self, invited=False):
        if invited:
            return super()._search_is_member_channel_ids(invited=True)
        if self.env.user._is_public():
            return self._get_public_key_participations().channel_id.ids
        participations = (
            self.env["slide.channel.partner"]
            .sudo()
            .search(
                [
                    ("partner_id", "=", self.env.user.partner_id.id),
                    ("member_status", "!=", "invited"),
                    ("active", "=", True),
                ]
            )
        )
        return participations.filtered(
            lambda participation: (
                participation.parent_id
                or not participation.sale_order_line_ids
                or participation._is_individual_course_registration()
            )
        ).channel_id.ids

    def _compute_user_statistics(self):
        res = super()._compute_user_statistics()
        if self._has_key_session():
            participations = self._get_public_key_participations()
        else:
            participations = (
                self.env["slide.channel.partner"]
                .sudo()
                .search(
                    [
                        ("channel_id", "in", self.ids),
                        ("partner_id", "=", self.env.user.partner_id.id),
                        ("parent_id", "!=", False),
                        ("active", "=", True),
                    ]
                )
            )
        statistics_by_channel = {
            participation.channel_id.id: (
                participation.member_status == "completed",
                participation.completed_slides_count,
            )
            for participation in participations
        }
        for channel in self:
            if channel.id not in statistics_by_channel:
                continue
            completed, completed_slides_count = statistics_by_channel[channel.id]
            channel.completed = completed
            channel.completion = (
                100.0
                if completed
                else round(100.0 * completed_slides_count / (channel.total_slides or 1))
            )
        return res

    def _action_add_members(
        self,
        target_partners,
        member_status="joined",
        raise_on_access=False,
        **member_values,
    ):
        # Create sub-participations
        parent_channel_partner = member_values.get("parent_channel_partner", False)
        to_create_values = {}
        if (
            parent_channel_partner
            and parent_channel_partner.available_registrations
            > parent_channel_partner.used_registrations
        ):
            to_create_values = {
                "channel_id": self.id,
                "partner_id": target_partners.id,
                "parent_id": parent_channel_partner.id,
            }
            # Dynamically add the values from member_values
            to_create_values.update(
                {
                    key: value
                    for key, value in member_values.items()
                    if key != "parent_channel_partner"
                }
            )
            self.env["slide.channel.partner"].sudo().create(to_create_values)
        if (
            parent_channel_partner
            and not to_create_values
            and parent_channel_partner.available_registrations
            <= parent_channel_partner.used_registrations
        ):
            request.session["channel_error"] = self.env._(
                "No registrations available for this course."
            )
            return self.env["slide.channel.partner"].sudo()
        # After buy a course, send email with token only when confirming the order.
        new_target_partners = self.env["res.partner"]
        sale_order_line = self.env.context.get("course_sale_order_lines", False)
        if sale_order_line:
            new_target_partners = target_partners.filtered(
                lambda x: x.id not in self.channel_partner_ids.partner_id.ids
            )
        res = super()._action_add_members(
            target_partners,
            member_status=member_status,
            raise_on_access=raise_on_access,
        )
        if new_target_partners:
            sale_order = sale_order_line.order_id
            for target in self.channel_partner_ids.filtered(
                lambda x: x.partner_id.id in new_target_partners.ids
            ):
                target._send_confirm_mail(sale_order)
        return res


class SlideChannelPartner(models.Model):
    _inherit = "slide.channel.partner"

    parent_id = fields.Many2one(
        comodel_name="slide.channel.partner",
        string="Parent Participation",
        ondelete="cascade",
        index=True,
    )
    child_channel_partner_ids = fields.One2many(
        comodel_name="slide.channel.partner",
        inverse_name="parent_id",
        string="Child Participation",
    )
    available_registrations = fields.Integer(
        compute="_compute_available_registrations", store=True
    )
    used_registrations = fields.Integer(
        compute="_compute_used_registrations", store=True
    )
    remaining_registrations = fields.Integer(
        compute="_compute_remaining_registrations", store=True
    )
    invitation_hash = fields.Char(compute="_compute_invitation_link", store=True)
    invitation_link = fields.Char(store=True)
    slide_channel_partner_name = fields.Char(string="Name")
    slide_channel_partner_email = fields.Char(string="Participation Email")
    slide_channel_partner_phone = fields.Char(string="Phone")
    identification_number = fields.Char(
        help="User's personal identification number",
    )
    is_public_slide_channel_partner = fields.Boolean(default=False)

    _channel_partner_uniq = models.Constraint(
        "CHECK (true)",
        "Temporal constraint disabled",
    )

    _unique_channel_identification = models.Constraint(
        "unique(channel_id, identification_number)",
        "The identification number must be unique per course!",
    )

    @api.depends(
        "sale_order_line_ids.product_uom_qty",
        "sale_order_line_ids.order_id.state",
    )
    def _compute_available_registrations(self):
        for record in self:
            confirmed_lines = record.sale_order_line_ids.filtered(
                lambda line: line.order_id.state == "sale"
            )
            confirmed_qty = sum(confirmed_lines.mapped("product_uom_qty"))
            record.available_registrations = (
                confirmed_qty if record.sale_order_line_ids else 1
            )

    @api.depends("available_registrations", "used_registrations")
    def _compute_remaining_registrations(self):
        for rec in self:
            rec.remaining_registrations = (rec.available_registrations or 0) - (
                rec.used_registrations or 0
            )

    @api.depends(
        "child_channel_partner_ids",
        "sale_order_line_ids.product_uom_qty",
        "sale_order_line_ids.order_id.state",
    )
    def _compute_used_registrations(self):
        for record in self:
            record.used_registrations = (
                len(record.child_channel_partner_ids)
                + int(record._is_individual_course_registration())
                if record.sale_order_line_ids
                else 1
            )

    @api.depends("channel_id", "partner_id")
    def _compute_invitation_link(self):
        res = super()._compute_invitation_link()
        for record in self:
            record.invitation_hash = record._get_invitation_hash()
        return res

    def _is_individual_course_registration(self):
        self.ensure_one()
        confirmed_lines = self.sale_order_line_ids.filtered(
            lambda line: line.order_id.state == "sale"
        )
        ordered_qty = sum(confirmed_lines.mapped("product_uom_qty"))
        return ordered_qty == 1

    def _create_registration_parent(self, additional_line):
        self.ensure_one()
        order_lines = self.sale_order_line_ids | additional_line
        parent = self.with_context(course_sale_order_lines=order_lines).create(
            {
                "channel_id": self.channel_id.id,
                "partner_id": self.partner_id.id,
            }
        )
        self.parent_id = parent
        return parent

    @api.model_create_multi
    def create(self, vals_list):
        sale_order_lines = self.env.context.get(
            "course_sale_order_lines", self.env["sale.order.line"]
        )
        participant_fields = (
            "slide_channel_partner_name",
            "slide_channel_partner_email",
            "slide_channel_partner_phone",
            "identification_number",
        )
        for vals in vals_list:
            partner = self.env["res.partner"].browse(vals.get("partner_id"))
            if not partner:
                continue
            channel = self.env["slide.channel"].browse(vals.get("channel_id"))
            channel_sale_lines = sale_order_lines.filtered(
                lambda line, channel=channel: line.product_id == channel.product_id
            )
            is_registration_pool = (
                not vals.get("parent_id")
                and sum(channel_sale_lines.mapped("product_uom_qty")) > 1
            )
            if is_registration_pool:
                vals.update({field_name: False for field_name in participant_fields})
                continue
            partner_values = {
                "slide_channel_partner_name": partner.name,
                "slide_channel_partner_email": partner.email,
                "slide_channel_partner_phone": partner.phone,
                "identification_number": partner.vat,
            }
            for field_name, value in partner_values.items():
                if not vals.get(field_name):
                    vals[field_name] = value
        return super().create(vals_list)

    def _recompute_completion(self):
        slide_channel_partners = self.filtered("is_public_slide_channel_partner")
        if not slide_channel_partners:
            return super()._recompute_completion()
        read_group_res = (
            self.env["slide.slide.partner"]
            .sudo()
            ._read_group(
                [
                    ("channel_id", "in", self.mapped("channel_id").ids),
                    ("identification_number", "!=", False),
                    ("completed", "=", True),
                    ("slide_id.is_published", "=", True),
                    ("slide_id.active", "=", True),
                ],
                ["channel_id", "identification_number"],
                aggregates=["__count"],
            )
        )
        mapped_data = {
            (channel.id, identification_number): count
            for channel, identification_number, count in read_group_res
        }
        for record in slide_channel_partners:
            if record.member_status in ("completed", "invited"):
                continue
            record.completed_slides_count = mapped_data.get(
                (record.channel_id.id, record.identification_number), 0
            )
            record.completion = round(
                100.0
                * record.completed_slides_count
                / (record.channel_id.total_slides or 1)
            )
            if not record.channel_id.active:
                continue
            if record.completion == 100:
                record.member_status = "completed"
            elif record.completion == 0:
                record.member_status = "joined"
            else:
                record.member_status = "ongoing"
        return super(
            SlideChannelPartner,
            self.filtered(lambda scp: not scp.child_channel_partner_ids)
            - slide_channel_partners,
        )._recompute_completion()

    def _send_confirm_mail(self, sale_order=False):
        self.ensure_one()
        template = self.env.ref(
            "website_sale_slides_multi_qty.mail_template_slide_channel_confirm",
            raise_if_not_found=False,
        )
        if not template:
            return
        email_values = {}
        if sale_order:
            email_values.update(
                {
                    "model": "sale.order",
                    "res_id": sale_order.id,
                }
            )
        return template.send_mail(self.id, force_send=False, email_values=email_values)

    def _send_completed_mail(self):
        # Avoiding duplicate email sending when completing the course
        return super(
            SlideChannelPartner,
            self.filtered(lambda record: not record.child_channel_partner_ids),
        )._send_completed_mail()
