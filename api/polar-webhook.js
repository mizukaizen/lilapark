/**
 * Polar Webhook Handler — Post-Purchase Delivery
 *
 * Handles order.created events from Polar:
 * 1. Sends branded delivery email via Resend with PDF download link
 * 2. Adds buyer to Beehiiv newsletter
 *
 * Required env vars (set in Vercel project settings):
 *   POLAR_WEBHOOK_SECRET   — Polar Dashboard > Webhooks > your endpoint secret
 *   RESEND_API_KEY          — resend.com dashboard (free tier: 3,000/month)
 *   BEEHIIV_API_KEY         — Beehiiv Settings > API
 *   BEEHIIV_PUB_ID          — Beehiiv publication ID (format: pub_xxxxxxxx)
 *   PDF_DOWNLOAD_URL        — Fallback if not in product metadata
 *
 * Polar webhook payload (order.created):
 *   data.order.customer.email
 *   data.order.customer.name
 *   data.order.product.name
 *   data.order.product.metadata.download_url (optional)
 *
 * Setup steps:
 *   1. Deploy to Vercel (auto on push to main)
 *   2. Go to Polar Dashboard → Webhooks → Add endpoint
 *   3. URL: https://lilapark.xyz/api/polar-webhook
 *   4. Events: order.created
 *   5. Copy the webhook secret → add to Vercel env as POLAR_WEBHOOK_SECRET
 *   6. Set remaining env vars in Vercel project settings
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

function buildDeliveryEmail(productName, downloadUrl) {
  return `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#1a2e1a;font-family:Georgia,'Times New Roman',serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#1a2e1a;">
<tr><td align="center" style="padding:40px 20px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

  <!-- Header -->
  <tr><td style="text-align:center;padding:0 0 16px;">
    <span style="font-family:Georgia,serif;font-size:14px;font-weight:normal;letter-spacing:0.3em;text-transform:uppercase;color:#f5f0e8;">LILA PARK</span>
  </td></tr>

  <!-- Sage divider -->
  <tr><td style="padding:0 0 24px;">
    <div style="height:1px;background:#8fbc8f;opacity:0.4;max-width:80px;margin:0 auto;"></div>
  </td></tr>

  <!-- Card -->
  <tr><td style="background:#243824;border-radius:8px;padding:36px 32px;">

    <!-- Heading -->
    <p style="font-family:Georgia,serif;font-size:22px;line-height:1.4;color:#f5f0e8;margin:0 0 24px;text-align:center;">
      Your order is here &#10022;
    </p>

    <!-- Personal note from Lila -->
    <p style="font-family:Georgia,serif;font-size:16px;line-height:1.75;color:#b8c9b8;margin:0 0 28px;">
      You made a quiet, important decision tonight. ${productName} is yours now &mdash; a guide built from Korean sleep wisdom and modern science, for the women who need it most. I hope it brings you back to rest.
    </p>

    <!-- Download button -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:0 0 16px;">
      <a href="${downloadUrl}" style="display:inline-block;background:#8fbc8f;color:#1a2e1a;font-family:-apple-system,Helvetica,Arial,sans-serif;font-size:16px;font-weight:700;text-decoration:none;padding:14px 32px;border-radius:4px;">
        Download ${productName} &rarr;
      </a>
    </td></tr>
    </table>

    <!-- Bookmark note -->
    <p style="font-family:-apple-system,Helvetica,Arial,sans-serif;font-size:13px;color:#b8c9b8;opacity:0.7;margin:0;text-align:center;line-height:1.6;">
      This link is yours to keep. Bookmark it or<br>come back to this email anytime.
    </p>

  </td></tr>

  <!-- Divider -->
  <tr><td style="padding:24px 0 0;">
    <div style="height:1px;background:#8fbc8f;opacity:0.2;"></div>
  </td></tr>

  <!-- Footer -->
  <tr><td style="padding:20px 0 0;text-align:center;">
    <p style="font-family:Georgia,serif;font-size:14px;font-style:italic;color:#b8c9b8;opacity:0.6;line-height:1.6;margin:0 0 12px;">
      You're now part of Lila's inner circle.<br>Expect gentle wisdom in your inbox.
    </p>
    <p style="font-family:-apple-system,Helvetica,Arial,sans-serif;font-size:11px;color:#b8c9b8;opacity:0.35;margin:0;">
      lilapark.xyz &middot; hello@lilapark.xyz
    </p>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>`;
}

async function sendDeliveryEmail(email, productName, downloadUrl) {
  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.RESEND_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from: 'Lila Park <hello@lilapark.xyz>',
      to: [email],
      subject: `Your 3am Protocol is here \u2726`,
      html: buildDeliveryEmail(productName, downloadUrl),
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
  const signature = req.headers['webhook-signature'] || '';
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
  const productName = order.product?.name || 'The 3am Protocol';
  const downloadUrl =
    order.product?.metadata?.download_url || process.env.PDF_DOWNLOAD_URL;
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
  const emailPromise = sendDeliveryEmail(email, productName, downloadUrl);
  const beehiivPromise = pubId
    ? addToBeehiiv(email, pubId, productName).catch((err) => {
        console.error(
          'Beehiiv subscription failed (non-blocking):',
          err.message
        );
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
