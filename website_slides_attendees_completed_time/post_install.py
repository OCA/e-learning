# © 2025 Binhex - Rolando Pérez <r.perez@binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


def channel_partner_recompute_completion(env):
    env["slide.channel.partner"].search([])._recompute_completion()
    return
