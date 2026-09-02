"""The pricing cards may not advertise anything the server does not grant.

Three claims were wrong at the same time, and none of them was a typo:

  - Studio listed separate workspaces, white-label PDF reports and
    multi-user access at 39 a month. plans.py says in its own docstring that
    none of the three is implemented, and its entitlements table gives Studio
    exactly what Pro gets with a higher account cap.
  - Free advertised "top posts and time slots", while app.py strips
    best_hours and sets hours_locked on the same request that draws the card.
  - Free's list of what it lacks named "automated reports", a feature no plan
    sells and no module implements, and left out CSV export, which is real
    and genuinely paid-only.

Each of those is a sentence a customer can quote back in a refund request.
So the cards are now checked against plans.py rather than against nobody:
a feature can be advertised on a plan only if that plan is actually entitled
to it, and a feature can be listed as missing only if it actually is.
"""
import re
from pathlib import Path

import billing
import plans

APP_JS = Path(__file__).resolve().parent.parent / "static" / "app.js"

# Advertised copy -> the entitlement key that decides whether the customer
# gets it. Only claims the server enforces belong here; a promise like
# priority support is a human commitment, not a flag.
GATED = {
    "plan_feat_history": "history",
    "plan_feat_compare": "history",
    "plan_feat_hours": "best_hours",
    "plan_feat_csv": "csv_export",
    "plan_feat_rivals": "rivals",
}

# Claims that are true on every plan, so they gate on nothing. Anything not
# in here and not in GATED fails the last test on purpose: a new bullet on a
# pricing card has to be either enforced or deliberately declared free.
UNGATED = {
    "plan_feat_all_socials",
    "plan_feat_manual_refresh",
    "plan_feat_analytics",
    "plan_feat_diagnostics",
    "plan_feat_insights",
    "plan_feat_all_free",
    "plan_feat_all_pro",
    "plan_feat_priority",
}


def codes(plan, field):
    return [code for code, _ in plan.get(field, [])]


class TestTheCardsMatchTheServer:
    def test_no_plan_advertises_a_feature_it_does_not_get(self):
        for plan in billing.PLANS:
            for code in codes(plan, "features"):
                key = GATED.get(code)
                if key is None:
                    continue
                assert plans.allows(plan["id"], key) is True, (
                    f'{plan["name"]} advertises {code} but plans.py denies '
                    f'"{key}" to the {plan["id"]} plan'
                )

    def test_nothing_listed_as_missing_is_actually_included(self):
        for plan in billing.PLANS:
            for code in codes(plan, "missing"):
                key = GATED.get(code)
                if key is None:
                    continue
                assert plans.allows(plan["id"], key) is False, (
                    f'{plan["name"]} lists {code} as missing, but plans.py '
                    f'grants "{key}" to the {plan["id"]} plan'
                )

    def test_the_paid_plans_differ_from_free_by_something_real(self):
        """A paid tier whose advertised extras are all ungated copy would be
        selling nothing the server can tell apart."""
        for plan in billing.PLANS:
            if plan["id"] == plans.FREE:
                continue
            enforced = [GATED[c] for c in codes(plan, "features") if c in GATED]
            bigger_cap = plans.max_accounts(plan["id"]) > plans.max_accounts(plans.FREE)
            assert enforced or bigger_cap, (
                f'{plan["name"]} costs money but nothing on its card, and not '
                "its account limit either, is enforced anywhere"
            )


class TestEveryClaimIsTranslated:
    def test_each_advertised_code_exists_in_every_language(self):
        source = APP_JS.read_text(encoding="utf-8")
        # Every language block carries this one, so counting it counts the
        # languages without hardcoding how many there are.
        languages = source.count("plan_feat_all_socials:")
        assert languages >= 2, "could not find the language blocks in app.js"

        for plan in billing.PLANS:
            for code in codes(plan, "features") + codes(plan, "missing"):
                found = len(re.findall(r"^\s*%s:" % re.escape(code), source, re.M))
                assert found == languages, (
                    f"{code} is advertised but translated in {found} of "
                    f"{languages} languages"
                )

    def test_no_translation_survives_the_claim_it_described(self):
        """The three removed Studio claims left their strings behind in six
        languages. Dead pricing copy is how a deleted promise comes back."""
        source = APP_JS.read_text(encoding="utf-8")
        translated = set(re.findall(r"^\s*(plan_feat_\w+):", source, re.M))
        advertised = {
            code
            for plan in billing.PLANS
            for code in codes(plan, "features") + codes(plan, "missing")
        }
        orphans = translated - advertised
        assert not orphans, f"translated but advertised nowhere: {sorted(orphans)}"


class TestTheAllowlistsStayHonest:
    def test_every_advertised_code_is_classified(self):
        for plan in billing.PLANS:
            for code in codes(plan, "features") + codes(plan, "missing"):
                assert code in GATED or code in UNGATED, (
                    f"{code} is advertised on {plan['name']} but this test "
                    "does not know whether the server enforces it — add it to "
                    "GATED with its entitlement key, or to UNGATED if it is "
                    "genuinely available to everyone"
                )

    def test_gated_keys_are_real_entitlements(self):
        known = set(plans.ENTITLEMENTS[plans.FREE])
        for code, key in GATED.items():
            assert key in known, f"{code} maps to {key}, which plans.py has no such entitlement for"
