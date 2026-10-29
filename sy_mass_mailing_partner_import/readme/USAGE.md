## Add partners to mailing lists

1. Go to **Contacts**.
2. Select one or more partners from the list view.
3. Use the **Action** menu to open the wizard for adding partners to mailing lists.
4. Select one or more mailing lists.
5. Confirm the operation.

Mailing contacts are created automatically if they do not already exist. Existing
mailing contacts are reused, and only missing mailing list subscriptions are added.

Partners must have an email address to be added to mailing lists.

## Import partners using a domain

1. Go to **Email Marketing > Mailing Lists**.
2. Open a mailing list and access the contact import wizard.
3. Select **Partners** as the import type.
4. Configure the domain to filter the partners to import.
5. Confirm the import.

The module creates or reuses mailing contacts for the matching partners and adds them to
the selected mailing lists.

The standard email import functionality remains available by selecting the email import
type.

## Merge partners

When merging partners that have linked mailing contacts, the module automatically
consolidates their mailing list subscriptions into a single mailing contact associated
with the destination partner.

Existing mailing list associations and opt-out preferences are preserved.

## Manage the global email blacklist

1. Go to **Contacts**.
2. Open a partner with an email address.
3. Click the green **Add to Blacklist** button next to the email address to blacklist it.
4. To remove the email from the blacklist, click the red **Remove from Blacklist** button and confirm the operation.

When an email address is added to the global blacklist, all associated mailing list subscriptions are automatically marked as opted out (`opt_out=True`).

When the email address is removed from the blacklist, all associated subscriptions are automatically marked as opted in (`opt_out=False`). This also resets any previous individual mailing list opt-out preferences.

The blacklist applies to the email address, so all partners sharing the same email are affected.

Blacklist synchronization also applies when entries are created, archived, unarchived, or deleted directly from the global blacklist.

Existing mailing list associations are preserved. Subscription preferences are only updated when the global blacklist status changes.
