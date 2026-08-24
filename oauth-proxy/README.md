# OAuth token exchange and licensing service

The Worker handles two responsibilities for the same underlying reason: they
are the two things an application installed on a customer's computer
**cannot safely handle by itself**.

| | Why it cannot live in the application |
|---|---|
| OAuth token exchange | The client secret could be read by unpacking the executable |
| Licensing | The plan database would live on the computer of the person who is expected to pay |

## Licensing

Complete flow:

1. the application sends `POST /checkout` and receives the Stripe payment URL
2. the customer pays on Stripe
3. Stripe calls `POST /stripe/webhook`, which creates the license key
4. the customer lands on `GET /license/claim` and copies the key
5. the customer pastes it into the application, which calls
   `POST /license/verify` and unlocks the plan

**Prices live in the Worker**, not in the application. If the client selected
the amount, a modified executable could request a zero-cost subscription.
The webhook signature is verified with HMAC, constant-time comparison, and a
five-minute window. Without that verification, an unauthenticated caller
could issue free licenses.

### Configure Stripe

```bash
python deploy_proxy.py --stripe
```

The command requests both keys and uploads them to the Worker without saving
them to disk. Then open
[dashboard.stripe.com](https://dashboard.stripe.com), go to Developers →
Webhooks, and add an endpoint that points to:

```
https://<your-worker>.workers.dev/stripe/webhook
```

Subscribe it to `checkout.session.completed`,
`customer.subscription.deleted`, and `invoice.payment_failed`.

### Configure license delivery by email

The customer reaches `/license/claim` only if the browser remains open until
Stripe completes the redirect. Email delivery prevents the key from being
lost if the tab is closed too early. With [Resend](https://resend.com)
(free for up to 3,000 emails per month):

1. create an account at resend.com
2. under **Domains**, add the sender subdomain
   (`mail.getcertsprint.com` here) and publish the DNS records Resend
   provides for SPF, DKIM, and DMARC
3. under **API Keys**, create a key
4. upload it to the Worker:

```bash
python deploy_proxy.py --resend
```

The application still works without this key. The license remains available
on the claim page, but no backup copy is sent by email.

### Revocation

Refunds and cancellations arrive through the webhook and set the license to
`inactive`. The application detects the change during its next check
(within 24 hours) and removes the plan immediately. The seven-day grace
period covers network failures only, not an unpaid subscription.

## Why the OAuth proxy is required

Instagram and TikTok require a **client secret** to exchange an OAuth
`code` for an access token.

A distributed desktop application has no safe place to store that secret.
If it is compiled into the executable, anyone who downloads the application
can recover it by unpacking the binary. Meta explicitly states that the app
secret must not be embedded in distributed code.

This proxy keeps the secrets on a server. The application sends the `code`
and receives the token; the secret never leaves the Worker and is absent
from the distributed build.

> Google's client secret is an exception. Google documents installed-app
> client secrets as non-confidential, so it can remain in the executable and
> does not pass through this proxy.

## Deploy to Cloudflare Workers

Only two commands are required:

```bash
npx wrangler login       # once: opens the browser for Cloudflare authorization
python deploy_proxy.py   # run from the project directory
```

`deploy_proxy.py` publishes the Worker, uploads the four secrets read from
`brand.py`, writes the Worker URL back to `brand.py`, and **clears**
`INSTAGRAM_APP_SECRET` and `TIKTOK_CLIENT_SECRET` so they cannot enter the
next build. If any step fails, it stops without modifying `brand.py`.

Browser login is the only step that cannot be automated because it authorizes
the Cloudflare account.

Rebuild the application, then verify the distributable:

```bash
python check_release.py --dist
```

<details>
<summary>Manual deployment</summary>

```bash
cd oauth-proxy
npx wrangler deploy
npx wrangler secret put INSTAGRAM_APP_ID
npx wrangler secret put INSTAGRAM_APP_SECRET
npx wrangler secret put TIKTOK_CLIENT_KEY
npx wrangler secret put TIKTOK_CLIENT_SECRET
```

Then set `OAUTH_PROXY_URL` in `brand.py` to the Worker URL and clear both
`*_SECRET` values.
</details>

## Verify the deployment

```bash
curl -X POST https://<your-worker>/exchange \
  -H 'content-type: application/json' \
  -d '{"platform":"tiktok","code":"invalid","redirect_uri":"https://example.com"}'
```

The response should be `{"error":"TikTok rejected the request."}`. That
confirms that the Worker is reachable, has its secrets, and can communicate
with TikTok. A different response such as 404 or 500 indicates a deployment
problem.

## Credential rotation

Treat any secret embedded in a distributed build as compromised and
**regenerate it**:

- Instagram: Meta for Developers → application → Instagram Login API
  configuration → *Instagram app secret* → regenerate
- TikTok: TikTok for Developers → application → Credentials → regenerate the
  client secret

After rotation, update the Worker secrets with `wrangler secret put`.
Existing connections continue to work because they use access tokens, not the
client secret.
