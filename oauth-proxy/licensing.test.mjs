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

const SECRET = "whsec_test_secret";

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
    get: async (k) => store.get(k) ?? null,
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
    const env = { STRIPE_WEBHOOK_SECRET: SECRET, RESEND_API_KEY: "re_test", LICENSES: kvStub() };
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
    const env = { STRIPE_WEBHOOK_SECRET: SECRET, RESEND_API_KEY: "re_test", LICENSES: kvStub() };
    await handleWebhook(env, await signed(checkoutBody("")));
    assert.equal(sent.length, 1, "only the owner is written to");
    assert.match(sent[0].body.html, /no address given to Stripe/);
  });
});

test("an unsigned request issues nothing", async () => {
  await withStubbedResend(async (sent) => {
    const env = { STRIPE_WEBHOOK_SECRET: SECRET, RESEND_API_KEY: "re_test", LICENSES: kvStub() };
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
      RESEND_API_KEY: "re_test",
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
