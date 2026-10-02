"""A small labelled dataset of customer-support tickets.

Four categories, 15 tickets each. The first 2 of each category form the
few-shot pool; the remaining 13 are the test set (52 items). Written for this
lab - small enough to run on a laptop, large enough that the bootstrap
confidence intervals mean something.
"""

CATEGORIES = ["billing", "bug", "account_access", "feature_request"]

TICKETS = {
    "billing": [
        "I was charged twice for my March subscription. Please refund one of the charges.",
        "Can I get an invoice with our company VAT number on it?",
        "My card was declined but the money still left my account.",
        "Why did my bill go up from $20 to $35 this month? Nobody told us about a price change.",
        "We downgraded to the Starter plan last week but were billed for Pro again.",
        "How do I switch from monthly to annual billing and get the discount?",
        "The receipt email never arrived after I paid. I need it for expenses.",
        "Please cancel my subscription and confirm I won't be charged again.",
        "There's a charge from you labelled 'overage' - what is that for?",
        "Our purchase order requires net-60 payment terms. Is that possible?",
        "I used a promo code at checkout but the discount isn't on the invoice.",
        "Can you move our billing from my personal card to the company card?",
        "We were charged sales tax but we're a tax-exempt nonprofit.",
        "The refund you promised two weeks ago still hasn't appeared.",
        "Do you offer a student discount on the individual plan?",
    ],
    "bug": [
        "The export to CSV button does nothing when I click it in Chrome.",
        "The app crashes every time I open a project with more than 500 files.",
        "Dates in the report show as 01/01/1970 for every row.",
        "After the latest update the dashboard charts are blank.",
        "Search returns results from a workspace I was removed from.",
        "Uploading a PNG larger than 5 MB fails with 'unknown error'.",
        "The mobile app logs me out every few minutes on Android 15.",
        "Webhook deliveries are arriving twice for each event.",
        "The dark mode toggle resets to light every time I reload.",
        "Copy-paste from Excel drops the last column of the table.",
        "Notifications show the wrong timezone - everything is 5 hours off.",
        "The API returns HTTP 500 when the name field contains an emoji.",
        "Keyboard shortcuts stopped working in the editor on Firefox.",
        "Scheduled reports are sent at the right time but are empty.",
        "The progress bar gets stuck at 99% and the import never finishes.",
    ],
    "account_access": [
        "I can't log in - it says my password is wrong but I just reset it.",
        "I lost my phone and can't get the two-factor code. How do I get back in?",
        "My account is locked after too many attempts. Please unlock it.",
        "I never received the password reset email.",
        "Our admin left the company and nobody can manage the workspace now.",
        "SSO login loops back to the sign-in page for everyone on our team.",
        "How do I change the email address I log in with?",
        "I'm getting 'account suspended' but we paid our bill.",
        "The magic login link says it has expired as soon as I click it.",
        "Can you remove a former employee's access to our workspace?",
        "I signed up with Google but now want to use a password instead.",
        "My new team member's invitation link says it is invalid.",
        "We need to transfer ownership of the account to a new manager.",
        "Security keys aren't accepted as a second factor on my laptop.",
        "I think someone else logged into my account from another country.",
    ],
    "feature_request": [
        "It would be great if we could schedule posts for a specific timezone.",
        "Please add an integration with Microsoft Teams.",
        "Could you support exporting reports as PDF, not just CSV?",
        "We'd love a way to set different permissions for guests and members.",
        "Any plans for an offline mode in the mobile app?",
        "Please let us customise the colours of the dashboard to match our brand.",
        "Can you add bulk editing so I can change 100 tasks at once?",
        "A public API endpoint for audit logs would help our compliance team.",
        "It would help to have keyboard shortcuts for moving cards between columns.",
        "Please support right-to-left languages like Arabic and Hebrew.",
        "Could the weekly summary email include a chart of the trends?",
        "We need a way to archive projects instead of deleting them.",
        "Is there any chance of a Linux desktop app?",
        "Let us pin important comments to the top of a thread.",
        "Would be nice to have two-way sync with Google Calendar.",
    ],
}


def split(n_shots_per_class: int = 2):
    """Return (few_shot_pool, test_set) as lists of (text, label)."""
    pool, test = [], []
    for label, texts in TICKETS.items():
        pool += [(t, label) for t in texts[:n_shots_per_class]]
        test += [(t, label) for t in texts[n_shots_per_class:]]
    return pool, test
