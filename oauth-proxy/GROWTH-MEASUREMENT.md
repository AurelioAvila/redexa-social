# Anonymous acquisition counters

The existing Worker receives only a predefined event name, with the product derived from an exact Origin allowlist. D1 stores UTC day, product, action and aggregate count. There are no visitor IDs, cookies, prompt contents, channel data or IPs in this database. Platform network handling is disclosed separately. Browser privacy signals suppress events.

Counts are deduplicated within one page lifetime, not across pages or visits. They are **not unique people, completed downloads, verified installations, paying users or retention cohorts**. Public counters can be inflated by bots; Origin checks are not authentication. Daily counts cap at 100,000 per cell. Optional app-review feedback is self-reported, not instrumented desktop activity. No desktop binary was changed in this website release.

Read locally with the authorized Cloudflare CLI:

```powershell
npx --no-install wrangler d1 execute redaxa-redexa-growth --remote --command "SELECT day, product, event, count FROM growth_daily ORDER BY day DESC, product, event"
```

Interpret Redaxa visit → demo_result → demo_copy / extension_click, and compare trial_gate with scan_success cautiously (no cross-session attribution). For Redexa compare homepage visit, guide_view, download_click and voluntary feedback categories. Repeated feedback from one person cannot be identified. The browser tests and first production verification may contribute a documented baseline.

Next research: recruit 5 relevant testers per product through explicitly authorized brand channels. Ask them to complete a task without help. Record where they stop and what would make them return; do not invent testimonials. No outreach or scheduled campaign is created by this deployment.

Installer: existing signed 1.9.3 NSIS package, SHA256 ddd09ac66c0389747a96f3e66ea432ad098e042081c42c14f3370ae5bb0a91ea. Publisher and timestamp checked with Windows SignTool; published asset digest matches. Updater manifest and ZIP unchanged.
