# Copyright 2025 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models, tools
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

    def _compute_is_member(self):
        res = super()._compute_is_member()
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
            mapped_data = {
                info.channel_id.id: (info.completed, info.completed_slides_count)
                for info in current_user_info
            }
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

    # def _compute_action_rights(self):

    def _action_add_members(self, target_partners, **member_values):
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
        if self.env.context.get("course_sale_order_lines", False):
            new_target_partners = target_partners.filtered(
                lambda x: x.id not in self.channel_partner_ids.partner_id.ids
            )
        res = super()._action_add_members(target_partners, **member_values)
        if new_target_partners:
            for target in self.channel_partner_ids.filtered(
                lambda x: x.partner_id.id in new_target_partners.ids
            ):
                target._send_confirm_mail()
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
    invitation_hash = fields.Char(compute="_compute_invitation", store=True)
    invitation_link = fields.Char(compute="_compute_invitation", store=True)
    slide_channel_partner_name = fields.Char(string="Name")
    slide_channel_partner_email = fields.Char(string="Participation Email")
    slide_channel_partner_phone = fields.Char(string="Phone")
    identification_number = fields.Char(
        help="User's personal identification number",
    )
    is_public_slide_channel_partner = fields.Boolean(default=False)

    _sql_constraints = [
        (
            "unique_channel_identification",
            "unique(channel_id, identification_number)",
            "The identification number must be unique per course!",
        )
    ]

    @api.depends("sale_order_line_ids.product_uom_qty")
    def _compute_available_registrations(self):
        for record in self:
            total_qty = sum(record.sale_order_line_ids.mapped("product_uom_qty"))
            record.available_registrations = total_qty

    @api.depends("child_channel_partner_ids")
    def _compute_used_registrations(self):
        for record in self:
            record.used_registrations = len(record.child_channel_partner_ids)

    @api.depends("channel_id", "partner_id")
    def _compute_invitation(self):
        # This sets the url used as hyperlink in the channel invitation email in
        # template mail_notification_channel_invite.
        # The partner_id is given in the url, as well as a hash based on the partner
        # and channel id.
        for record in self:
            record.invitation_hash = record._get_invitation_hash()
            record.invitation_link = (
                f"{record.channel_id.get_base_url()}/slides/{record.channel_id.id}"
                f"/invite?invite_partner_id={record.partner_id.id}"
                f"&invite_hash={record.invitation_hash}"
            )

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
        if not self.channel_id._is_public_with_key():
            return super()._recompute_completion()
        identification_number = request.session.get("identification_number", False)
        # Obtain progress only from the participation of the user with current password
        read_group_res = (
            self.env["slide.slide.partner"]
            .sudo()
            .read_group(
                [
                    ("channel_id", "in", self.mapped("channel_id").ids),
                    ("identification_number", "=", identification_number),
                    ("completed", "=", True),
                    ("slide_id.is_published", "=", True),
                    ("slide_id.active", "=", True),
                ],
                ["channel_id"],
                groupby=["channel_id"],
                lazy=False,
            )
        )
        mapped_data = {
            item["channel_id"][0]: item["__count"] for item in read_group_res
        }
        # Filter only shares that have an ID number
        for record in self.filtered("identification_number"):
            if record.identification_number != identification_number:
                continue
            completed_slides_count = mapped_data.get(record.channel_id.id, 0)
            record.completed_slides_count = completed_slides_count
            record.completion = (
                100.0
                if record.completed
                else round(
                    100.0
                    * completed_slides_count
                    / (record.channel_id.total_slides or 1)
                )
            )
            if (
                not record.completed
                and record.channel_id.active
                and completed_slides_count >= record.channel_id.total_slides
            ):
                record.completed = True

    def _get_invitation_hash(self):
        # Returns the invitation hash of the attendee, used to access courses
        # as invited / joined.
        self.ensure_one()
        token = (self.partner_id.id, self.channel_id.id)
        return tools.hmac(self.env(su=True), "website_slides-channel-invite", token)

    def _send_confirm_mail(self):
        self.ensure_one()
        template = self.env.ref(
            "website_sale_slides_multi_qty.mail_template_slide_channel_confirm",
            raise_if_not_found=False,
        )
        template.send_mail(self.id, force_send=False)

    def _send_completed_mail(self):
        # Avoiding duplicate email sending when completing the course
        filtered_self = self.filtered(
            lambda record: not record.child_channel_partner_ids
        )
        if not filtered_self:
            return super()._send_completed_mail()
        return super(SlideChannelPartner, filtered_self)._send_completed_mail()
