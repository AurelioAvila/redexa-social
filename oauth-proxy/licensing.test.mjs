/**
 * Tests for the licence webhook.
 *
 * Copyright (c) 2026 Aurelio Avila. All rights reserved.
 *
 * The Worker had no tests of its own — the suite in ../tests covers the app
 * side in Python — so the one path where money turns into a licence was
 * verified only by reading it. These exercise handleWebhook end to end with a
 * genuinely signed payload, a stubbed KV and a stubbed Resend, which is what
 * makes the claim "the owner is now told about a sale" checkable rather than
 * plausible.
 *
 *     node --test oauth-proxy/licensing.test.mjs
 */

import test from "node:test";
import assert from "node:assert/strict";
import { handleWebhook } from "./licensing.js";

// Deliberately not shaped like the real thing. Stripe and Resend both give
// their live keys a recognisable prefix, and a secret scanner reading a diff
// cannot tell a test fixture wearing one of those prefixes from a leaked key
// — nor should it have to.
const SECRET = "test-webhook-signing-secret";
const FAKE_RESEND_KEY = "test-mail-key";

/** Signs a body the way Stripe does, so the real check runs rather than a
 *  bypass written for the test. */
async function signed(body) {
  const timestamp = Math.floor(Date.now() / 1000);
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(SECRET),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const mac = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(`${timestamp}.${body}`));
  const hex = [...new Uint8Array(mac)].map((b) => b.toString(16).padStart(2, "0")).join("");
  return new Request("https://example.com/stripe/webhook", {
    method: "POST",
    headers: { "stripe-signature": `t=${timestamp},v1=${hex}` },
    body,
  });
}

/** A KV namespace that remembers what was written. */
function kvStub() {
  const store = new Map();
  return {
    store,
    // Honours the "json" type the way the real namespace does. Without it
    // every read on the revocation path came back as a string and the code
    // under test looked broken when the stub was.
    get: async (k, type) => {
      const raw = store.get(k) ?? null;
      return type === "json" && raw !== null ? JSON.parse(raw) : raw;
    },
    put: async (k, v) => void store.set(k, v),
    delete: async (k) => void store.delete(k),
    list: async () => ({ keys: [...store.keys()].map((name) => ({ name })) }),
  };
}

/** Captures every Resend call instead of sending anything. */
function withStubbedResend(fn) {
  const sent = [];
  const original = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    sent.push({ url: String(url), body: JSON.parse(init.body) });
    return new Response("{}", { status: 200 });
  };
  return fn(sent).finally(() => {
    globalThis.fetch = original;
  });
}

const checkoutBody = (email) =>
  JSON.stringify({
    type: "checkout.session.completed",
    data: {
      object: {
        id: "cs_test_123",
        customer_email: email,
        customer: "cus_test_123",
        subscription: "sub_test_123",
        metadata: { plan: "pro" },
      },
    },
  });

test("a paid checkout issues a key, emails the buyer and tells the owner", async () => {
  await withStubbedResend(async (sent) => {
    const env = { STRIPE_WEBHOOK_SECRET: SECRET, RESEND_API_KEY: FAKE_RESEND_KEY, LICENSES: kvStub() };
    const response = await handleWebhook(env, await signed(checkoutBody("buyer@example.com")));
    assert.equal(response.status, 200);

    const keys = [...env.LICENSES.store.keys()];
    assert.ok(
      keys.some((k) => k.startsWith("key:")),
      "the licence itself must be stored",
    );

    const recipients = sent.map((s) => s.body.to);
    assert.ok(recipients.includes("buyer@example.com"), "the buyer gets their key");
    assert.ok(
      recipients.some((to) => to !== "buyer@example.com"),
      "the owner is told a sale happened — this is what was missing entirely",
    );

    const notice = sent.find((s) => s.body.to !== "buyer@example.com");
    assert.match(notice.body.subject, /New Social Dashboard sale/);
    assert.match(notice.body.html, /Pro/);
  });
});

test("a sale with no address still reaches the owner", async () => {
  // Stripe does not always have an email. The buyer cannot be written to, but
  // that is exactly when the owner most needs to know a key was issued that
  // nobody received.
  await withStubbedResend(async (sent) => {
    const env = { STRIPE_WEBHOOK_SECRET: SECRET, RESEND_API_KEY: FAKE_RESEND_KEY, LICENSES: kvStub() };
    await handleWebhook(env, await signed(checkoutBody("")));
    assert.equal(sent.length, 1, "only the owner is written to");
    assert.match(sent[0].body.html, /no address given to Stripe/);
  });
});

test("an unsigned request issues nothing", async () => {
  await withStubbedResend(async (sent) => {
    const env = { STRIPE_WEBHOOK_SECRET: SECRET, RESEND_API_KEY: FAKE_RESEND_KEY, LICENSES: kvStub() };
    const request = new Request("https://example.com/stripe/webhook", {
      method: "POST",
      headers: { "stripe-signature": "t=1,v1=deadbeef" },
      body: checkoutBody("buyer@example.com"),
    });
    const response = await handleWebhook(env, request);
    assert.equal(response.status, 400);
    assert.equal(env.LICENSES.store.size, 0, "no licence may exist without a valid signature");
    assert.equal(sent.length, 0);
  });
});

test("the sender address is configurable, so it can stop being CertSprint's", async () => {
  await withStubbedResend(async (sent) => {
    const env = {
      STRIPE_WEBHOOK_SECRET: SECRET,
      RESEND_API_KEY: FAKE_RESEND_KEY,
      LICENSE_FROM: "Social Dashboard <licenses@example.com>",
      LICENSES: kvStub(),
    };
    await handleWebhook(env, await signed(checkoutBody("buyer@example.com")));
    assert.ok(sent.length > 0);
    for (const message of sent) {
      assert.equal(message.body.from, "Social Dashboard <licenses@example.com>");
    }
  });
});

const revocationBody = (type) =>
  JSON.stringify(
    type === "invoice.payment_failed"
      ? { type, data: { object: { subscription: "sub_test_123" } } }
      : { type, data: { object: { id: "sub_test_123" } } },
  );

/** Buys first, so the revocation runs against a licence that really exists. */
async function soldEnv(sent) {
  const env = { STRIPE_WEBHOOK_SECRET: SECRET, RESEND_API_KEY: FAKE_RESEND_KEY, LICENSES: kvStub() };
  await handleWebhook(env, await signed(checkoutBody("buyer@example.com")));
  sent.length = 0;
  return env;
}

test("a failed payment tells the buyer, and says the card can fix it", async () => {
  await withStubbedResend(async (sent) => {
    const env = await soldEnv(sent);
    await handleWebhook(env, await signed(revocationBody("invoice.payment_failed")));

    const notice = sent.find((s) => s.body.to === "buyer@example.com");
    assert.ok(notice, "the buyer must learn their licence stopped working");
    assert.match(notice.body.subject, /payment failed/i);
    assert.match(notice.body.html, /Updating the card restores it/);
    assert.ok(notice.body.text, "HTML-only mail lands in spam far more often");
    assert.match(notice.body.text, /not been deleted/);
  });
});

test("a cancellation is worded as a choice, not as a failure", async () => {
  await withStubbedResend(async (sent) => {
    const env = await soldEnv(sent);
    await handleWebhook(env, await signed(revocationBody("customer.subscription.deleted")));

    const notice = sent.find((s) => s.body.to === "buyer@example.com");
    assert.match(notice.body.subject, /subscription has ended/i);
    assert.doesNotMatch(notice.body.html, /payment did not go through/);
  });
});

test("Stripe's retries of the same failed invoice send one email, not four", async () => {
  // Stripe re-fires invoice.payment_failed on every retry over about a week.
  // Telling the customer four times that the same payment failed reads as a
  // broken product.
  await withStubbedResend(async (sent) => {
    const env = await soldEnv(sent);
    for (let attempt = 0; attempt < 4; attempt += 1) {
      await handleWebhook(env, await signed(revocationBody("invoice.payment_failed")));
    }
    const notices = sent.filter((s) => s.body.to === "buyer@example.com");
    assert.equal(notices.length, 1, `sent ${notices.length} notices for one lapsed subscription`);
  });
});

// --- a recovered payment has to bring the licence back -----------------
//
// invoice.payment_failed fires on the FIRST failed attempt. Stripe then
// retries the invoice for about a week, and the email above tells the
// customer to update their card — so recovery is the normal path, not the
// exception. Neither outcome reached this handler: only a brand-new checkout
// ever set a licence back to active, so somebody whose payment recovered kept
// being billed with a dead key.

/** The stored record for the licence soldEnv created. */
async function record(env) {
  const keyName = [...env.LICENSES.store.keys()].find((k) => k.startsWith("key:"));
  return JSON.parse(env.LICENSES.store.get(keyName));
}

const paidBody = () =>
  JSON.stringify({ type: "invoice.paid", data: { object: { subscription: "sub_test_123" } } });

const updatedBody = (status) =>
  JSON.stringify({
    type: "customer.subscription.updated",
    data: { object: { id: "sub_test_123", status } },
  });

test("a retried invoice that finally goes through restores the licence", async () => {
  await withStubbedResend(async (sent) => {
    const env = await soldEnv(sent);

    await handleWebhook(env, await signed(revocationBody("invoice.payment_failed")));
    assert.equal((await record(env)).status, "inactive", "the failure must suspend it");

    await handleWebhook(env, await signed(paidBody()));

    const rec = await record(env);
    assert.equal(rec.status, "active", "a paid invoice has to bring the licence back");
    assert.equal(rec.revoked_at, undefined, "the revocation stamp must not outlive the revocation");
  });
});

test("a new card in the portal restores it too", async () => {
  await withStubbedResend(async (sent) => {
    const env = await soldEnv(sent);
    await handleWebhook(env, await signed(revocationBody("invoice.payment_failed")));

    await handleWebhook(env, await signed(updatedBody("active")));

    assert.equal((await record(env)).status, "active");
  });
});

test("a trial counts as entitled", async () => {
  await withStubbedResend(async (sent) => {
    const env = await soldEnv(sent);
    await handleWebhook(env, await signed(revocationBody("invoice.payment_failed")));

    await handleWebhook(env, await signed(updatedBody("trialing")));

    assert.equal((await record(env)).status, "active");
  });
});

test("a subscription Stripe still calls past_due does not come back", async () => {
  await withStubbedResend(async (sent) => {
    const env = await soldEnv(sent);

    await handleWebhook(env, await signed(updatedBody("past_due")));

    const rec = await record(env);
    assert.equal(rec.status, "inactive", "only Stripe saying active or trialing entitles");
    assert.ok(rec.revoked_at, "and the suspension has to be stamped");
  });
});

test("restoring a licence says nothing to the customer", async () => {
  // They have just fixed their card and the app starts working on its own
  // recheck. A second message about it is noise.
  await withStubbedResend(async (sent) => {
    const env = await soldEnv(sent);
    await handleWebhook(env, await signed(revocationBody("invoice.payment_failed")));
    sent.length = 0;

    await handleWebhook(env, await signed(paidBody()));

    assert.deepEqual(sent, []);
  });
});

test("an event for a subscription we never sold is ignored quietly", async () => {
  await withStubbedResend(async (sent) => {
    const env = await soldEnv(sent);
    const body = JSON.stringify({
      type: "invoice.paid",
      data: { object: { subscription: "sub_someone_elses" } },
    });

    const response = await handleWebhook(env, await signed(body));

    assert.equal(response.status, 200, "throwing would make Stripe retry it forever");
    assert.equal((await record(env)).status, "active", "our licence must be untouched");
  });
});
