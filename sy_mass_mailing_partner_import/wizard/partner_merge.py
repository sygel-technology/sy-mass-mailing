# Copyright 2026 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class BasePartnerMergeAutomaticWizard(models.TransientModel):
    _inherit = "base.partner.merge.automatic.wizard"

    def _merge(self, partner_ids, dst_partner=None, extra_checks=True):
        if dst_partner:
            # Unificar los contactos de marketing de los partners fusionados.
            contacts = (
                self.env["mailing.contact"]
                .sudo()
                .search([("partner_id", "in", partner_ids)])
            )
            if contacts:
                contacts = contacts.sorted(
                    lambda contact: 0 if contact.partner_id == dst_partner else 1
                )
                list_ids = contacts.mapped("list_ids").ids
                # Recuperar las listas en las que existe una exclusión.
                Subscription = self.env["mailing.subscription"].sudo()
                opt_out_list_ids = (
                    Subscription.search(
                        [
                            ("contact_id", "in", contacts.ids),
                            ("opt_out", "=", True),
                        ]
                    )
                    .mapped("list_id")
                    .ids
                )
                contacts[1:].unlink()
                contacts[0].partner_id = dst_partner
                contacts[0].list_ids = [(4, list_id) for list_id in list_ids]
                # Conservar las exclusiones de los contactos fusionados.
                subscriptions = Subscription.search(
                    [
                        ("contact_id", "=", contacts[0].id),
                        ("list_id", "in", opt_out_list_ids),
                    ]
                )
                subscriptions.write({"opt_out": True})
        return super()._merge(
            partner_ids,
            dst_partner=dst_partner,
            extra_checks=extra_checks,
        )
