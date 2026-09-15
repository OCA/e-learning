# Copyright 2025 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from markupsafe import Markup

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _action_confirm(self):
        additions = {}
        for order in self:
            course_lines = order.order_line.filtered(
                lambda line: line.product_id.channel_ids
            )
            for line in course_lines:
                registration = self.env["slide.channel.partner"].search(
                    [
                        ("channel_id", "in", line.product_id.channel_ids.ids),
                        ("partner_id", "=", order.partner_id.id),
                        ("parent_id", "=", False),
                        ("sale_order_line_ids", "!=", False),
                    ],
                    limit=1,
                )
                if not registration or line in registration.sale_order_line_ids:
                    continue
                if registration._is_individual_course_registration():
                    registration = registration._create_registration_parent(line)
                else:
                    line.slide_channel_partner_id = registration
                key = (order.id, registration.id)
                additions.setdefault(
                    key,
                    [order, registration, 0.0],
                )[2] += line.product_uom_qty
        result = super()._action_confirm()
        for order, registration, added_qty in additions.values():
            order._send_registrations_added_mail(
                added_qty,
                registration,
            )
        return result

    def _verify_updated_quantity(
        self, order_line, product_id, new_qty, uom_id, **kwargs
    ):
        # Allow adding more than 1 quantity of a course to the cart
        res = super()._verify_updated_quantity(
            order_line, product_id, new_qty, uom_id, **kwargs
        )
        product = self.env["product.product"].browse(product_id)
        if product.service_tracking == "course" and new_qty > 1:
            return new_qty, ""
        return res

    def _send_registrations_added_mail(self, added_qty, registration):
        body = Markup(
            self.env._(
                "<p>Your registrations for the course <strong>%(course_name)s</strong> "
                "have been increased by <strong>%(added_qty)s registration(s)</strong>."
                "</p>"
                "<p>You now have a total of "
                "<strong>%(available_registrations)s</strong> "
                "registration(s) purchased, of which "
                "<strong>%(used_registrations)s</strong> have already been used and "
                "<strong>%(remaining_registrations)s</strong> are still available.</p>",
                course_name=registration.channel_id.name,
                added_qty=int(added_qty),
                available_registrations=registration.available_registrations,
                used_registrations=registration.used_registrations,
                remaining_registrations=registration.remaining_registrations,
            )
        )
        self.message_post(
            body=body,
            subject=self.env._(
                "Course Registrations Added: %s",
                registration.channel_id.name,
            ),
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
            partner_ids=[self.partner_id.id],
            email_layout_xmlid="mail.mail_notification_light",
        )
