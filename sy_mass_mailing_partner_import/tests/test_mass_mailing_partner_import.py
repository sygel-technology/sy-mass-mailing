# Copyright 2026 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase
from odoo.tools import mute_logger


class TestMassMailingPartnerImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "email": "partner@example.com",
                "ref": "TEST001",
            }
        )
        cls.mailing_contact = cls.env["mailing.contact"].create(
            {
                "name": cls.partner.name,
                "email": cls.partner.email,
                "partner_id": cls.partner.id,
            }
        )
        cls.mailing_list_1 = cls.env["mailing.list"].create(
            {"name": "Test Mailing List 1"}
        )
        cls.mailing_list_2 = cls.env["mailing.list"].create(
            {"name": "Test Mailing List 2"}
        )
        cls.partner_same_email = cls.env["res.partner"].create(
            {
                "name": "Partner Same Email",
                "email": cls.partner.email,
            }
        )
        cls.partner_other_email = cls.env["res.partner"].create(
            {
                "name": "Partner Other Email",
                "email": "other@example.com",
            }
        )

    def test_mailing_contact_partner(self):
        self.assertEqual(self.mailing_contact.partner_id, self.partner)
        self.assertEqual(self.mailing_contact.partner_ref, "TEST001")

    def test_mailing_contact_unique_partner(self):
        with (
            self.assertRaises(IntegrityError),
            self.cr.savepoint(),
            mute_logger("odoo.sql_db"),
        ):
            self.env["mailing.contact"].create(
                {
                    "name": "Duplicate Contact",
                    "email": "duplicate@example.com",
                    "partner_id": self.partner.id,
                }
            )

    def test_add_to_mailing_lists(self):
        partner = self.env["res.partner"].create(
            {
                "name": "New Partner",
                "email": "newpartner@example.com",
            }
        )

        created_count, subscription_count = partner._add_to_mailing_lists(
            self.mailing_list_1 | self.mailing_list_2
        )
        contact = self.env["mailing.contact"].search([("partner_id", "=", partner.id)])
        self.assertEqual(created_count, 1)
        self.assertEqual(subscription_count, 2)
        self.assertEqual(contact.partner_id, partner)
        self.assertEqual(
            contact.list_ids,
            self.mailing_list_1 | self.mailing_list_2,
        )

    def test_add_to_mailing_lists_existing(self):
        self.partner._add_to_mailing_lists(self.mailing_list_1)
        created_count, subscription_count = self.partner._add_to_mailing_lists(
            self.mailing_list_1 | self.mailing_list_2
        )
        self.assertEqual(created_count, 0)
        self.assertEqual(subscription_count, 1)
        self.assertEqual(
            self.mailing_contact.list_ids,
            self.mailing_list_1 | self.mailing_list_2,
        )
        self.assertEqual(
            self.env["mailing.contact"].search_count(
                [("partner_id", "=", self.partner.id)]
            ),
            1,
        )

    def test_add_to_mailing_lists_opt_out(self):
        self.partner._add_to_mailing_lists(self.mailing_list_1)
        subscription = self.mailing_contact.subscription_ids.filtered(
            lambda sub: sub.list_id == self.mailing_list_1
        )
        subscription.opt_out = True
        created_count, subscription_count = self.partner._add_to_mailing_lists(
            self.mailing_list_1 | self.mailing_list_2
        )
        self.assertEqual(created_count, 0)
        self.assertEqual(subscription_count, 1)
        self.assertTrue(subscription.opt_out)
        self.assertIn(self.mailing_list_2, self.mailing_contact.list_ids)

    def test_partner_mail_list_wizard(self):
        wizard = self.env["partner.mail.list.wizard"].create(
            {
                "partner_ids": [fields.Command.set(self.partner.ids)],
                "mailing_list_ids": [
                    fields.Command.set((self.mailing_list_1 | self.mailing_list_2).ids)
                ],
            }
        )

        action = wizard.action_add_to_mailing_lists()
        self.assertEqual(action["type"], "ir.actions.act_window_close")
        self.assertEqual(
            self.mailing_contact.list_ids,
            self.mailing_list_1 | self.mailing_list_2,
        )

    def test_partner_mail_list_wizard_without_email(self):
        partner = self.env["res.partner"].create({"name": "Partner Without Email"})
        wizard = self.env["partner.mail.list.wizard"].create(
            {
                "partner_ids": [fields.Command.set(partner.ids)],
                "mailing_list_ids": [fields.Command.set(self.mailing_list_1.ids)],
            }
        )
        with self.assertRaises(UserError):
            wizard.action_add_to_mailing_lists()

        self.assertFalse(
            self.env["mailing.contact"].search([("partner_id", "=", partner.id)])
        )

    def test_mailing_contact_import_domain(self):
        wizard = self.env["mailing.contact.import"].create(
            {
                "import_type": "partner",
                "partner_domain": f"[('id', '=', {self.partner.id})]",
                "mailing_list_ids": [fields.Command.set(self.mailing_list_1.ids)],
            }
        )
        action = wizard.action_import()
        self.assertEqual(action["tag"], "display_notification")
        self.assertIn(self.mailing_list_1, self.mailing_contact.list_ids)
        self.assertEqual(
            self.env["mailing.contact"].search_count(
                [("partner_id", "=", self.partner.id)]
            ),
            1,
        )

    def test_mailing_contact_import_without_email(self):
        partner = self.env["res.partner"].create({"name": "Partner Without Email"})
        wizard = self.env["mailing.contact.import"].create(
            {
                "import_type": "partner",
                "partner_domain": f"[('id', '=', {partner.id})]",
                "mailing_list_ids": [fields.Command.set(self.mailing_list_1.ids)],
            }
        )
        with self.assertRaises(UserError):
            wizard.action_import()
        self.assertFalse(
            self.env["mailing.contact"].search([("partner_id", "=", partner.id)])
        )

    def test_mailing_contact_import_email(self):
        wizard = self.env["mailing.contact.import"].create(
            {
                "import_type": "email",
                "contact_list": "standard-import@example.com",
                "mailing_list_ids": [fields.Command.set(self.mailing_list_1.ids)],
            }
        )
        wizard.action_import()
        contact = self.env["mailing.contact"].search(
            [("email", "=", "standard-import@example.com")]
        )
        self.assertTrue(contact)
        self.assertIn(self.mailing_list_1, contact.list_ids)

    def test_partner_merge(self):
        partner_a = self.env["res.partner"].create(
            {"name": "Partner A", "email": "merge-a@example.com"}
        )
        partner_b = self.env["res.partner"].create(
            {"name": "Partner B", "email": "merge-b@example.com"}
        )
        partner_a._add_to_mailing_lists(self.mailing_list_1)
        partner_b._add_to_mailing_lists(self.mailing_list_2)
        contact_a = partner_a.mailing_contact_ids
        contact_b = partner_b.mailing_contact_ids
        self.assertIn(self.mailing_list_1, contact_a.list_ids)
        self.assertIn(self.mailing_list_2, contact_b.list_ids)
        subscription = self.env["mailing.subscription"].search(
            [
                ("contact_id", "=", contact_a.id),
                ("list_id", "=", self.mailing_list_1.id),
            ]
        )
        self.assertEqual(len(subscription), 1)
        subscription.write({"opt_out": True})
        self.assertTrue(subscription.opt_out)
        self.assertEqual(subscription.list_id, self.mailing_list_1)
        wizard = self.env["base.partner.merge.automatic.wizard"].create({})
        wizard._merge(
            (partner_a | partner_b).ids,
            dst_partner=partner_b,
        )
        self.env.invalidate_all()
        contacts = self.env["mailing.contact"].search(
            [("partner_id", "=", partner_b.id)]
        )
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts, contact_b)
        self.assertEqual(
            contacts.list_ids,
            self.mailing_list_1 | self.mailing_list_2,
        )
        subscription = self.env["mailing.subscription"].search(
            [
                ("contact_id", "=", contacts.id),
                ("list_id", "=", self.mailing_list_1.id),
            ]
        )
        self.assertEqual(len(subscription), 1)
        self.assertTrue(subscription.opt_out)

    def test_mailing_contact_count(self):
        self.assertEqual(self.partner.mailing_contact_count, 1)
        self.mailing_contact.partner_id = False
        self.assertEqual(self.partner.mailing_contact_count, 0)
        self.mailing_contact.partner_id = self.partner
        self.assertEqual(self.partner.mailing_contact_count, 1)

    def test_action_view_mailing_contact(self):
        action = self.partner.action_view_mailing_contact()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "mailing.contact")
        self.assertEqual(action["view_mode"], "form")
        self.assertEqual(action["res_id"], self.mailing_contact.id)

    def test_mailing_contact_import_default_type(self):
        config = self.env["ir.config_parameter"].sudo()
        config.set_param(
            "sy_mass_mailing_partner_import.mailing_import_type",
            "partner",
        )
        wizard = self.env["mailing.contact.import"].create({})
        self.assertEqual(wizard.import_type, "partner")
        config.set_param(
            "sy_mass_mailing_partner_import.mailing_import_type",
            "email",
        )
        wizard = self.env["mailing.contact.import"].create({})
        self.assertEqual(wizard.import_type, "email")

    def test_partner_blacklist_add(self):
        self.assertFalse(self.partner.is_blacklisted)
        self.partner.mail_blacklist_add()
        blacklist = self.env["mail.blacklist"].search(
            [("email", "=", self.partner.email_normalized)]
        )
        self.assertTrue(blacklist)
        self.assertTrue(blacklist.active)
        self.assertTrue(self.partner.is_blacklisted)
        self.assertTrue(self.mailing_contact.is_blacklisted)

    def test_partner_blacklist_remove(self):
        self.partner.is_blacklisted = True
        self.partner.is_blacklisted = False
        blacklist = (
            self.env["mail.blacklist"]
            .with_context(active_test=False)
            .search([("email", "=", self.partner.email_normalized)])
        )
        self.assertTrue(blacklist)
        self.assertFalse(blacklist.active)
        self.partner.invalidate_recordset(["is_blacklisted"])
        self.mailing_contact.invalidate_recordset(["is_blacklisted"])
        self.assertFalse(self.partner.is_blacklisted)
        self.assertFalse(self.mailing_contact.is_blacklisted)

    def test_partner_blacklist_opt_out(self):
        self.partner._add_to_mailing_lists(self.mailing_list_1)
        subscription = self.mailing_contact.subscription_ids
        self.assertFalse(subscription.opt_out)
        self.partner.is_blacklisted = True
        self.assertTrue(self.partner.is_blacklisted)
        self.assertTrue(subscription.opt_out)
        self.partner.is_blacklisted = False
        self.assertFalse(self.partner.is_blacklisted)
        self.assertFalse(subscription.opt_out)

    def test_partner_blacklist_multiple_lists(self):
        self.partner._add_to_mailing_lists(self.mailing_list_1 | self.mailing_list_2)
        subscriptions = self.mailing_contact.subscription_ids
        subscription_2 = subscriptions.filtered(
            lambda sub: sub.list_id == self.mailing_list_2
        )
        subscription_2.opt_out = True
        self.partner.is_blacklisted = True
        self.assertTrue(self.partner.is_blacklisted)
        self.assertTrue(all(subscriptions.mapped("opt_out")))
        self.partner.is_blacklisted = False
        self.assertFalse(self.partner.is_blacklisted)
        self.assertFalse(any(subscriptions.mapped("opt_out")))
        self.assertEqual(
            self.mailing_contact.list_ids,
            self.mailing_list_1 | self.mailing_list_2,
        )

    def test_blacklist_create_active(self):
        self.partner._add_to_mailing_lists(self.mailing_list_1)
        subscription = self.mailing_contact.subscription_ids
        blacklist = self.env["mail.blacklist"].create({"email": self.partner.email})
        self.assertTrue(blacklist.active)
        self.assertTrue(subscription.opt_out)

    def test_blacklist_create_inactive(self):
        self.partner._add_to_mailing_lists(self.mailing_list_1)
        subscription = self.mailing_contact.subscription_ids
        blacklist = self.env["mail.blacklist"].create(
            {
                "email": self.partner.email,
                "active": False,
            }
        )
        self.assertFalse(blacklist.active)
        self.assertFalse(subscription.opt_out)

    def test_blacklist_archive_unarchive(self):
        self.partner._add_to_mailing_lists(self.mailing_list_1)
        subscription = self.mailing_contact.subscription_ids
        blacklist = self.env["mail.blacklist"].create({"email": self.partner.email})
        self.assertTrue(subscription.opt_out)
        blacklist.action_archive()
        self.assertFalse(blacklist.active)
        self.assertFalse(subscription.opt_out)
        blacklist.action_unarchive()
        self.assertTrue(blacklist.active)
        self.assertTrue(subscription.opt_out)

    def test_blacklist_unlink(self):
        self.partner._add_to_mailing_lists(self.mailing_list_1)
        subscription = self.mailing_contact.subscription_ids
        blacklist = self.env["mail.blacklist"].create({"email": self.partner.email})
        self.assertTrue(subscription.opt_out)
        blacklist.unlink()
        self.assertFalse(subscription.opt_out)
        self.assertFalse(
            self.env["mail.blacklist"]
            .with_context(active_test=False)
            .search([("email", "=", self.partner.email_normalized)])
        )

    def test_blacklist_remove_wizard(self):
        self.partner._add_to_mailing_lists(self.mailing_list_1)
        subscription = self.mailing_contact.subscription_ids
        self.partner.mail_blacklist_add()
        self.assertTrue(subscription.opt_out)
        wizard = self.env["mail.blacklist.remove"].create(
            {
                "email": self.partner.email,
                "reason": "Test unblacklist",
            }
        )
        wizard.action_unblacklist_apply()
        self.assertFalse(subscription.opt_out)
        self.partner.invalidate_recordset(["is_blacklisted"])
        self.assertFalse(self.partner.is_blacklisted)

    def test_blacklist_write_without_active_change(self):
        self.partner._add_to_mailing_lists(self.mailing_list_1)
        subscription = self.mailing_contact.subscription_ids
        subscription.opt_out = True
        blacklist = self.env["mail.blacklist"].create(
            {
                "email": self.partner.email,
                "active": False,
            }
        )
        blacklist.write({"active": False})
        self.assertTrue(subscription.opt_out)

    def test_blacklist_mass_write(self):
        self.partner._add_to_mailing_lists(self.mailing_list_1)
        self.partner_other_email._add_to_mailing_lists(self.mailing_list_2)
        subscriptions = (
            self.partner.mailing_contact_ids.subscription_ids
            | self.partner_other_email.mailing_contact_ids.subscription_ids
        )
        blacklist = self.env["mail.blacklist"].create(
            [
                {"email": self.partner.email, "active": False},
                {"email": self.partner_other_email.email, "active": False},
            ]
        )
        blacklist.write({"active": True})
        self.assertTrue(all(subscriptions.mapped("opt_out")))
        blacklist.write({"active": False})
        self.assertFalse(any(subscriptions.mapped("opt_out")))

    def test_partner_blacklist_multiple_partners(self):
        same_contact = self.env["mailing.contact"].create(
            {
                "name": self.partner_same_email.name,
                "email": self.partner_same_email.email,
                "partner_id": self.partner_same_email.id,
            }
        )
        other_contact = self.env["mailing.contact"].create(
            {
                "name": self.partner_other_email.name,
                "email": self.partner_other_email.email,
                "partner_id": self.partner_other_email.id,
            }
        )
        same_subscription = self.env["mailing.subscription"].create(
            {
                "contact_id": same_contact.id,
                "list_id": self.mailing_list_1.id,
            }
        )
        other_subscription = self.env["mailing.subscription"].create(
            {
                "contact_id": other_contact.id,
                "list_id": self.mailing_list_1.id,
            }
        )
        self.assertFalse(same_subscription.opt_out)
        self.assertFalse(other_subscription.opt_out)
        self.partner.mail_blacklist_add()
        self.partner_same_email.invalidate_recordset(["is_blacklisted"])
        self.partner_other_email.invalidate_recordset(["is_blacklisted"])
        self.assertTrue(self.partner.is_blacklisted)
        self.assertTrue(self.partner_same_email.is_blacklisted)
        self.assertFalse(self.partner_other_email.is_blacklisted)
        self.assertTrue(same_subscription.opt_out)
        self.assertFalse(other_subscription.opt_out)
        self.partner.is_blacklisted = False
        self.partner_same_email.invalidate_recordset(["is_blacklisted"])
        self.partner_other_email.invalidate_recordset(["is_blacklisted"])
        self.assertFalse(self.partner.is_blacklisted)
        self.assertFalse(self.partner_same_email.is_blacklisted)
        self.assertFalse(self.partner_other_email.is_blacklisted)
        self.assertFalse(same_subscription.opt_out)
        self.assertFalse(other_subscription.opt_out)
