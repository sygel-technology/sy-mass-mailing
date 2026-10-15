# Copyright 2026 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class PartnerMailListWizard(models.TransientModel):
    _name = "partner.mail.list.wizard"
    _description = "Add Partners to Mailing Lists"

    partner_ids = fields.Many2many(
        comodel_name="res.partner",
        string="Partners",
        default=lambda self: self.env["res.partner"].browse(
            self.env.context.get("active_ids", [])
        ),
        required=True,
    )
    mailing_list_ids = fields.Many2many(
        comodel_name="mailing.list",
        string="Mailing Lists",
        required=True,
    )

    def action_add_to_mailing_lists(self):
        self.ensure_one()
        # Los contactos deben tener un email para poder importarse.
        partners_without_email = self.partner_ids.filtered(lambda p: not p.email)
        if partners_without_email:
            raise UserError(
                _(
                    "The following partners do not have an email address:\n%s",
                    "\n".join(partners_without_email.mapped("display_name")),
                )
            )
        # Crear o reutilizar los contactos de marketing y asociarlos a las listas.
        self.partner_ids._add_to_mailing_lists(self.mailing_list_ids)
        return {"type": "ir.actions.act_window_close"}
