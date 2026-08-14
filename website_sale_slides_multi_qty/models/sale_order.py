# Copyright 2025 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from markupsafe import Markup

from odoo import _, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _verify_updated_quantity(self, order_line, product_id, new_qty, **kwargs):
        # Allow adding more than 1 quantity of a course to the cart
        res = super()._verify_updated_quantity(
            order_line, product_id, new_qty, **kwargs
        )
        product = self.env["product.product"].browse(product_id)
        if product.detailed_type == "course" and new_qty > 1:
            return new_qty, ""
        return res

    def _action_confirm(self):
        course_lines = self.order_line.filtered(
            lambda line: line.product_id.channel_ids
        )
        for line in course_lines:
            existing_parent = self.env["slide.channel.partner"].search(
                [
                    ("channel_id", "in", line.product_id.channel_ids.ids),
                    ("partner_id", "=", self.partner_id.id),
                    ("sale_order_line_ids", "!=", False),
                ],
                limit=1,
            )
            if existing_parent:
                linked_lines_this_order = existing_parent.sale_order_line_ids.filtered(
                    lambda ln: ln.order_id.id == self.id
                )
                commands = [(3, ln.id) for ln in linked_lines_this_order]
                commands.append((4, line.id))
                existing_parent.write({"sale_order_line_ids": commands})
                if not linked_lines_this_order:
                    self._send_registrations_added_mail(
                        line.product_uom_qty, existing_parent
                    )
        return super()._action_confirm()

    def _verify_updated_quantity(self, order_line, product_id, new_qty, **kwargs):
        # Allow adding more than 1 quantity of a course to the cart
        res = super()._verify_updated_quantity(
            order_line, product_id, new_qty, **kwargs
        )
        product = self.env["product.product"].browse(product_id)
        if product.detailed_type == "course" and new_qty > 1:
            return new_qty, ""
        return res

    def _send_registrations_added_mail(self, added_qty, registration):
        body = Markup(
            _(
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
            subject=_("Course Registrations Added: %s") % registration.channel_id.name,
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
            partner_ids=[self.partner_id.id],
            email_layout_xmlid="mail.mail_notification_light",
        )
