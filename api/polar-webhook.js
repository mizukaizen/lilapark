/**
 * Polar Webhook Handler — Post-Purchase Delivery
 *
 * Handles order.created events from Polar:
 * 1. Sends branded delivery email via Resend with PDF download link
 * 2. Adds buyer to Beehiiv newsletter
 *
 * Required env vars (set in Vercel project settings):
 *   POLAR_WEBHOOK_SECRET   — Polar Dashboard > Settings > Webhooks > Secret
 *   RESEND_API_KEY          — resend.com > API Keys
 *   BEEHIIV_API_KEY         — Beehiiv > Settings > API
 *   BEEHIIV_PUB_ID          — Beehiiv publication ID (pub_xxxxxxxx)
 *   PDF_DOWNLOAD_URL        — Stable URL to the hosted PDF
 *
 * Polar webhook setup:
 *   URL: https://lilapark.xyz/api/polar-webhook
 *   Events: order.created
 *   Copy the webhook secret → add to Vercel env as POLAR_WEBHOOK_SECRET
 *
 * Payload structure (order.created):
 *   data.order.customer.email
 *   data.order.customer.name
 *   data.order.product.name
 */

import { createHmac, timingSafeEqual } from 'crypto';

export const config = { api: { bodyParser: false } };

async function buffer(readable) {
  const chunks = [];
  for await (const chunk of readable) {
    chunks.push(typeof chunk === 'string' ? Buffer.from(chunk) : chunk);
  }
  return Buffer.concat(chunks);
}

function verifyWebhookSignature(payload, signature, secret) {
  const expected = createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  const sig = signature.replace(/^sha256=/, '');
  if (expected.length !== sig.length) return false;
  return timingSafeEqual(Buffer.from(expected), Buffer.from(sig));
}

function buildDeliveryEmail(name, productName, downloadUrl) {
  const firstName = (name || '').split(' ')[0] || 'there';
  return `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#1a2e1a;font-family:Georgia,'Times New Roman',serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#1a2e1a;">
<tr><td align="center" style="padding:40px 20px;">
<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;">

  <!-- Header -->
  <tr><td style="text-align:center;padding:0 0 8px;">
    <span style="font-family:Georgia,serif;font-size:28px;font-weight:normal;font-style:italic;color:#8fbc8f;letter-spacing:1px;">Lila Park</span>
  </td></tr>
  <tr><td style="text-align:center;padding:0 0 32px;">
    <span style="font-family:-apple-system,Helvetica,Arial,sans-serif;font-size:12px;letter-spacing:2px;text-transform:uppercase;color:rgba(143,188,143,0.5);">Your order is ready &#10022;</span>
  </td></tr>

  <!-- Card -->
  <tr><td style="background:#243424;border-radius:16px;padding:36px 32px;">

    <!-- Personal note -->
    <p style="font-family:Georgia,serif;font-size:17px;line-height:1.7;color:#f5f0e8;margin:0 0 8px;">
      Hi ${firstName},
    </p>
    <p style="font-family:Georgia,serif;font-size:16px;line-height:1.7;color:rgba(245,240,232,0.8);margin:0 0 6px;">
      Thank you for trusting me with something as personal as your sleep. The fact that you're here means you're done accepting exhaustion as normal &mdash; and that takes courage.
    </p>
    <p style="font-family:Georgia,serif;font-size:16px;line-height:1.7;color:rgba(245,240,232,0.8);margin:0 0 28px;">
      Your copy of <strong style="color:#f5f0e8;">${productName}</strong> is ready. Everything you need is inside.
    </p>

    <!-- Download button -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:0 0 20px;">
      <a href="${downloadUrl}" style="display:inline-block;background:#8fbc8f;color:#1a2e1a;font-family:-apple-system,Helvetica,Arial,sans-serif;font-size:15px;font-weight:700;text-decoration:none;padding:14px 36px;border-radius:10px;letter-spacing:0.3px;">
        Download ${productName} &rarr;
      </a>
    </td></tr>
    </table>

    <p style="font-family:-apple-system,Helvetica,Arial,sans-serif;font-size:13px;color:rgba(245,240,232,0.4);margin:0;text-align:center;">
      This link is yours to keep. Bookmark it.
    </p>

  </td></tr>

  <!-- Footer -->
  <tr><td style="padding:28px 0 0;text-align:center;">
    <p style="font-family:Georgia,serif;font-size:14px;font-style:italic;color:rgba(143,188,143,0.6);line-height:1.6;margin:0 0 16px;">
      You're also now part of Lila's inner circle &mdash;<br>expect gentle wisdom in your inbox.
    </p>
    <p style="font-family:-apple-system,Helvetica,Arial,sans-serif;font-size:11px;color:rgba(143,188,143,0.3);margin:0;">
      &copy; 2026 Lila Park &middot; lilapark.xyz
    </p>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>`;
}

async function sendDeliveryEmail(email, name, productName, downloadUrl) {
  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.RESEND_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from: 'Lila Park <lila@lilapark.xyz>',
      to: [email],
      subject: `Your copy of ${productName} is ready`,
      html: buildDeliveryEmail(name, productName, downloadUrl),
    }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Resend API error ${res.status}: ${body}`);
  }
  return res.json();
}

async function addToBeehiiv(email, pubId, productName) {
  const res = await fetch(
    `https://api.beehiiv.com/v2/publications/${pubId}/subscriptions`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.BEEHIIV_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        reactivate_existing: false,
        send_welcome_email: false,
        utm_source: 'lila-park-purchase',
        utm_medium: 'product',
        utm_campaign: '3am-protocol',
        custom_fields: [
          { name: 'purchased_product', value: productName },
        ],
      }),
    }
  );

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Beehiiv API error ${res.status}: ${body}`);
  }
  return res.json();
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).end('Method Not Allowed');
  }

  const buf = await buffer(req);
  const signature = req.headers['x-polar-signature'] || '';
  const secret = process.env.POLAR_WEBHOOK_SECRET;

  if (!secret) {
    console.error('POLAR_WEBHOOK_SECRET not configured');
    return res.status(500).json({ error: 'webhook_secret_not_configured' });
  }

  if (!verifyWebhookSignature(buf, signature, secret)) {
    console.error('Webhook signature verification failed');
    return res.status(400).json({ error: 'invalid_signature' });
  }

  let payload;
  try {
    payload = JSON.parse(buf.toString('utf8'));
  } catch (err) {
    console.error('Invalid JSON payload:', err.message);
    return res.status(400).json({ error: 'invalid_json' });
  }

  if (payload.type !== 'order.created') {
    return res.status(200).json({ received: true, ignored: payload.type });
  }

  const order = payload.data?.order;
  if (!order) {
    console.error('No order data in payload');
    return res.status(200).json({ received: true, error: 'no_order_data' });
  }

  const email = order.customer?.email;
  const name = order.customer?.name || '';
  const productName = order.product?.name || 'The 3am Protocol';
  const downloadUrl = process.env.PDF_DOWNLOAD_URL;
  const pubId = process.env.BEEHIIV_PUB_ID;

  if (!email) {
    console.error('No customer email in order:', order.id);
    return res.status(200).json({ received: true, error: 'no_email' });
  }

  if (!downloadUrl) {
    console.error('PDF_DOWNLOAD_URL not configured');
    return res.status(200).json({ received: true, error: 'no_download_url' });
  }

  // Send email (critical) and add to Beehiiv (best-effort) in parallel
  const emailPromise = sendDeliveryEmail(email, name, productName, downloadUrl);
  const beehiivPromise = pubId
    ? addToBeehiiv(email, pubId, productName).catch(err => {
        console.error('Beehiiv subscription failed (non-blocking):', err.message);
        return { error: err.message };
      })
    : Promise.resolve({ skipped: 'no_pub_id' });

  try {
    const [emailResult, beehiivResult] = await Promise.all([
      emailPromise,
      beehiivPromise,
    ]);

    console.log('Delivery complete:', {
      email,
      product: productName,
      resend: emailResult,
      beehiiv: beehiivResult,
    });

    return res.status(200).json({ received: true, delivered: true });
  } catch (err) {
    console.error('Email delivery failed:', err.message);
    return res.status(500).json({ received: true, error: err.message });
  }
}
