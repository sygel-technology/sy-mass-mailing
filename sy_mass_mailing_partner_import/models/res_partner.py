# Copyright 2026 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    mailing_contact_ids = fields.One2many(
        comodel_name="mailing.contact",
        inverse_name="partner_id",
        string="Mailing Contacts",
    )
    mailing_contact_count = fields.Integer(
        compute="_compute_mailing_contact_count",
        store=True,
    )

    @api.depends("mailing_contact_ids")
    def _compute_mailing_contact_count(self):
        for partner in self:
            partner.mailing_contact_count = len(partner.mailing_contact_ids)

    def action_view_mailing_contact(self):
        self.ensure_one()
        action = {
            "type": "ir.actions.act_window",
            "name": "Mailing Contacts",
            "res_model": "mailing.contact",
            "view_mode": "list,form",
            "domain": [("id", "in", self.mailing_contact_ids.ids)],
            "target": "current",
        }
        if len(self.mailing_contact_ids) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": self.mailing_contact_ids.id,
                }
            )
        return action

    def _prepare_mailing_contact_vals(self):
        self.ensure_one()
        return {
            "partner_id": self.id,
            "name": self.name,
            "email": self.email,
            "title_id": self.title.id,
            "company_name": self.company_id.name or self.company_name,
            "country_id": self.country_id.id,
        }

    def _add_to_mailing_lists(self, mailing_lists):
        MailingContact = self.env["mailing.contact"]
        contacts_by_partner = {}
        for contact in MailingContact.search([("partner_id", "in", self.ids)]):
            contacts_by_partner.setdefault(contact.partner_id.id, contact)
        created_count = 0
        subscription_count = 0
        for partner in self:
            contact = contacts_by_partner.get(partner.id)
            if not contact:
                contact = MailingContact.create(partner._prepare_mailing_contact_vals())
                created_count += 1
            lists_to_add = mailing_lists - contact.list_ids
            if lists_to_add:
                contact.write(
                    {"list_ids": [fields.Command.link(lst.id) for lst in lists_to_add]}
                )
                subscription_count += len(lists_to_add)
        return created_count, subscription_count
