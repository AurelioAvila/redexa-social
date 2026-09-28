# Redexa Social — Design QA

## Redexa Social 1.9.2 migration

- Live landing page, navigation, legal pages and three search-focused landing pages verified at `https://redexa.getcertsprint.com`.
- Current Redexa favicon, application icons and product screenshot verified on the deployed site.
- Canonical, Open Graph and Twitter metadata now point to the Redexa hostname and versioned visual assets.
- The former public hostname redirects to Redexa while preserving POST endpoints required by existing clients.
- The Windows package now launches `Redexa Social.exe`; a compatibility launcher preserves existing shortcuts and upgrades.
- Automated verification: 262 Python tests and 16 Worker tests passed before release.

## Reference and implementation

- Approved direction: visual concept 2, captured in `exec-d3485a22-87d3-4bd5-be6b-b405aa951dc8.png`.
- Verified implementation: local desktop build at the same wide desktop viewport.
- Brand adjustment: the concept name was replaced with Redexa Social after finding an existing NorthStar Social product. The approved bright, approachable direction was preserved.

## Visual comparison

The implementation preserves the reference's strongest characteristics: a bright white canvas, cobalt-blue accents, a calm left navigation rail, a large editorial headline, restrained card borders, generous spacing and highly legible metric hierarchy. The new Redexa mark replaces the concept's star with an original analytics-oriented identity.

Intentional product-led differences:

- Existing platform, diagnostics, account, theme and language routes remain available rather than reducing the product to a static concept.
- Empty states show honest zero or unavailable values instead of fabricated customer data.
- Recommendations and trend charts remain in their established analytics flows until real connected-account data can support them.

The public landing page now carries the same approved direction: a split editorial hero, a real product screenshot, proof points, benefit-led feature cards, transparent pricing and a focused final call to action. It was checked in the local Worker preview at a desktop viewport; the navigation, image, anchors and release links resolve correctly, with no clipped or overlapping content above the fold.

## Interaction and accessibility checks

- Overview, Analytics, Diagnostics, Themes and Plans navigation were exercised in the running app.
- Pricing loads gracefully when private production configuration is absent.
- The generated brand mark remains distinguishable at sidebar and favicon sizes.
- Heading order, labelled controls, visible focus treatment, readable contrast and reduced-motion behavior are retained.
- No overflow, clipping, overlapping text or broken asset paths were observed at the verified desktop viewport.

## Automated verification

- Python: 262 tests passed.
- Worker and licensing service: 16 tests passed.
- JavaScript syntax checks passed for the app and worker modules.

## Final result

Passed.

## Desktop restyle — 28 September 2026

- Removed CSS gradients and SVG gradient fills, overview kicker and repeated rounded overview containers. Retained existing data and actions.
- Browser inspection: light Overview and dark Plans layout render without clipping at 1280x720; local preview has no connected account and no production plan cards loaded, so populated-account coverage remains limited.
- Native DWM caption/background/text attributes accepted on the local Windows installation. Native screenshot verification remains for the visible development window; API success alone is not a visual comparison.
- JavaScript syntax passed; 32 theme, caption-bridge and update-start tests passed. Invalid colors are rejected before native calls.
- Development app opened on port8795; installed app at8787 untouched. No commit, packaging or release performed.

## Approved B implementation — 28 September 2026
Channel desk applied to the app, with rail-colored native caption, bounded working sheets and a setup-channel list separated from real diagnostics. Verified light/dark themes, Diagnostics to Link account navigation, and 760px layout without horizontal overflow. Browser console had no errors. 37 theme/caption/i18n checks passed, plus Node checks for empty Overview, request handling and diagnostics setup/error separation. Local preview has no linked accounts; populated diagnostic behavior is covered by the focused Node check. No commit or release.

## Premium refinement — 28 September 2026
Approved B palette retained. Larger working-panel titles, status pills, quieter secondary actions, stronger active navigation and distinct corner sizes. Real loading skeletons plus inline Refresh; prior results preserved during refresh. JavaScript syntax, focused loading and diagnostics checks and 32 Python theme/window/update tests passed. Browser verified 1020x680 and 760x520 without horizontal overflow; Refresh completed and console was clear. No accounts linked in the preview, so populated-account behavior is covered by focused checks. No commit or release.

## Release candidate 1.10.6 — 28 September 2026

- 351 Python tests passed, including Windows caption validation and updater behavior.
- JavaScript syntax, account/refresh requests, Overview empty state, diagnostic setup separation and loading-state checks passed. New UI checks are included in CI.
- Application and public-page version metadata are aligned to 1.10.6.
- PyInstaller built the app, updater and compatibility launcher. The packaged startup/configuration gate passed and the app reported version 1.10.6.
- Signing, final archive/manifest verification and distribution are separate release gates; this source validation is not evidence of publication.
