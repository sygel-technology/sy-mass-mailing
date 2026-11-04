# Copyright 2026 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class MailBlacklist(models.Model):
    _inherit = "mail.blacklist"

    def _sync_mailing_subscription_opt_out(self, opt_out):
        contacts = self.env["mailing.contact"].search(
            [("partner_id.email_normalized", "in", self.mapped("email"))]
        )
        contacts.subscription_ids.write({"opt_out": opt_out})

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.filtered("active")._sync_mailing_subscription_opt_out(True)
        return records

    def write(self, vals):
        update_active = "active" in vals
        previous_active = (
            {record.id: record.active for record in self} if update_active else {}
        )
        result = super().write(vals)
        if update_active:
            changed_records = self.filtered(
                lambda record: previous_active[record.id] != record.active
            )
            changed_records._sync_mailing_subscription_opt_out(vals["active"])
        return result

    def unlink(self):
        self.filtered("active")._sync_mailing_subscription_opt_out(False)
        return super().unlink()
