# Copyright 2026 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class MailingContactImport(models.TransientModel):
    _inherit = "mailing.contact.import"

    import_type = fields.Selection(
        selection=[
            ("email", "Email Addresses"),
            ("partner", "Odoo Contacts"),
        ],
        default="email",
        required=True,
    )
    partner_domain = fields.Char(
        string="Partner Filter",
        default="[]",
    )

    def action_import(self):
        self.ensure_one()
        if self.import_type == "email":
            # Mantener el funcionamiento original de Odoo.
            action = super().action_import()
        else:
            # Obtener los contactos que cumplen el dominio seleccionado.
            domain = safe_eval(self.partner_domain or "[]")
            partners = self.env["res.partner"].search(domain)
            # Solo podemos importar contactos que tengan email.
            partners = partners.filtered(lambda partner: partner.email)
            if not partners:
                raise UserError(
                    _("No partners with an email address match the selected filter.")
                )
            # Crear o reutilizar los contactos de marketing y asociarlos a las listas.
            created_count, subscription_count = partners._add_to_mailing_lists(
                self.mailing_list_ids
            )
            action = {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "message": _(
                        "Partners successfully imported. "
                        "New mailing contacts: %(contacts)s. "
                        "New subscriptions: %(subscriptions)s.",
                        contacts=created_count,
                        subscriptions=subscription_count,
                    ),
                    "type": "success",
                    "sticky": False,
                    "next": {"type": "ir.actions.act_window_close"},
                },
            }
        return action
