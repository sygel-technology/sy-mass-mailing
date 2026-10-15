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
    )

    @api.depends("mailing_contact_ids")
    def _compute_mailing_contact_count(self):
        for partner in self:
            partner.mailing_contact_count = len(partner.mailing_contact_ids)

    def action_view_mailing_contact(self):
        self.ensure_one()
        # Abrir el contacto de marketing asociado al partner.
        return {
            "type": "ir.actions.act_window",
            "name": "Mailing Contact",
            "res_model": "mailing.contact",
            "view_mode": "form",
            "res_id": self.mailing_contact_ids.id,
            "target": "current",
        }

    def _add_to_mailing_lists(self, mailing_lists):
        MailingContact = self.env["mailing.contact"]
        # Recuperar los contactos de marketing existentes.
        contacts_by_partner = {
            contact.partner_id.id: contact
            for contact in MailingContact.search([("partner_id", "in", self.ids)])
        }
        created_count = 0
        subscription_count = 0
        for partner in self:
            contact = contacts_by_partner.get(partner.id)
            if not contact:
                # Crear el contacto de marketing si todavía no existe.
                contact = MailingContact.create(
                    {
                        "partner_id": partner.id,
                        "name": partner.name,
                        "email": partner.email,
                        "title_id": partner.title.id,
                        "company_name": (
                            partner.company_id.name or partner.company_name
                        ),
                        "country_id": partner.country_id.id,
                    }
                )
                created_count += 1
            # Añadir únicamente las listas que todavía no tenga asociadas.
            lists_to_add = mailing_lists - contact.list_ids
            if lists_to_add:
                contact.write(
                    {"list_ids": [fields.Command.link(lst.id) for lst in lists_to_add]}
                )
                subscription_count += len(lists_to_add)
        return created_count, subscription_count
