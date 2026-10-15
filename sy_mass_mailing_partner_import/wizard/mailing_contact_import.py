# Copyright 2026 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval


class MailingContactImport(models.TransientModel):
    _inherit = "mailing.contact.import"

    import_type = fields.Selection(
        selection=[
            ("email", "Email Addresses"),
            ("partner", "Odoo Contacts"),
        ],
        default=lambda self: self._default_import_type(),
        required=True,
    )
    partner_domain = fields.Char(
        string="Partner Filter",
        default="[]",
    )

    def _default_import_type(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "sy_mass_mailing_partner_import.mailing_import_type",
                "email",
            )
        )

    def action_import(self):
        self.ensure_one()
        if self.import_type == "email":
            action = super().action_import()
        else:
            domain = safe_eval(self.partner_domain or "[]")
            domain = expression.AND([domain, [("email", "!=", False)]])
            partners = self.env["res.partner"].search(domain)
            if not partners:
                raise UserError(
                    _("No partners with an email address match the selected filter.")
                )
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
