# Copyright 2025-2026 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.http import request


class SlideChannel(models.Model):
    _inherit = "slide.channel"

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

    def _compute_membership_values(self):
        res = super()._compute_membership_values()
        if self._is_public_with_key():
            channel_partner = (
                self.env["slide.channel.partner"]
                .sudo()
                .search(
                    [
                        ("channel_id", "in", self.ids),
                        (
                            "identification_number",
                            "=",
                            request.session.get("identification_number"),
                        ),
                        ("invitation_hash", "=", request.session.get("invite_hash")),
                    ]
                )
            )
            if channel_partner:
                self.is_member = True
        return res

    def _compute_user_statistics(self):
        identification_number = request.session.get("identification_number", False)
        invite_hash = request.session.get("invite_hash", False)
        is_public_with_key = (
            self.env.user._is_public() and identification_number and invite_hash
        )
        if is_public_with_key:
            current_user_info = (
                self.env["slide.channel.partner"]
                .sudo()
                .search(
                    [
                        ("channel_id", "in", self.ids),
                        ("identification_number", "=", identification_number),
                        ("invitation_hash", "=", invite_hash),
                    ]
                )
            )
            mapped_data = dict(
                (
                    info.channel_id.id,
                    (info.member_status == "completed", info.completed_slides_count),
                )
                for info in current_user_info
            )
            for record in self:
                completed, completed_slides_count = mapped_data.get(
                    record.id, (False, 0)
                )
                record.completed = completed
                record.completion = (
                    100.0
                    if completed
                    else round(
                        100.0 * completed_slides_count / (record.total_slides or 1)
                    )
                )
        else:
            return super()._compute_user_statistics()

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
            # Agregar dinámicamente los valores de member_values
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
            request.session["channel_error"] = _(
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

    _sql_constraints = [
        ("channel_partner_uniq", "CHECK (true)", "Temporal constraint disabled"),
        (
            "unique_channel_identification",
            "unique(channel_id, identification_number)",
            "The identification number must be unique per course!",
        ),
    ]

    @api.depends("sale_order_line_ids.product_uom_qty")
    def _compute_available_registrations(self):
        for record in self:
            total_qty = sum(record.sale_order_line_ids.mapped("product_uom_qty"))
            record.available_registrations = total_qty or 1

    @api.depends("available_registrations", "used_registrations")
    def _compute_remaining_registrations(self):
        for rec in self:
            rec.remaining_registrations = (rec.available_registrations or 0) - (
                rec.used_registrations or 0
            )

    @api.depends("child_channel_partner_ids")
    def _compute_used_registrations(self):
        for record in self:
            record.used_registrations = (
                len(record.child_channel_partner_ids)
                if record.sale_order_line_ids
                else 1
            )

    @api.depends("channel_id", "partner_id")
    def _compute_invitation_link(self):
        res = super()._compute_invitation_link()
        for record in self:
            record.invitation_hash = record._get_invitation_hash()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if (
                not vals.get("slide_channel_partner_name", False)
                or not vals.get("slide_channel_partner_email", False)
                or not vals.get("slide_channel_partner_phone", False)
            ):
                partner = self.env["res.partner"].browse(vals["partner_id"])
                vals["slide_channel_partner_name"] = partner.name
                vals["slide_channel_partner_email"] = partner.email
                vals["slide_channel_partner_phone"] = partner.phone or partner.mobile
        return super().create(vals_list)

    def _recompute_completion(self):
        slide_channel_partners = self.filtered(lambda scp: scp.identification_number)
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
        filtered_self = self.filtered(
            lambda record: not record.child_channel_partner_ids
        )
        if not filtered_self:
            return super()._send_completed_mail()
        return super(SlideChannelPartner, filtered_self)._send_completed_mail()
