# © 2025 Binhex - Rolando Pérez <r.perez@binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import SUPERUSER_ID, api


def channel_partner_recompute_completion(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["slide.channel.partner"].search([])._recompute_completion()
    return
