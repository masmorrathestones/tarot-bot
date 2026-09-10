# Tarot payments

Each WhatsApp Tarot reading costs **US$1.00** and is paid through Stripe Checkout after the user provides optional context and before any cards are drawn.

## Required environment variables

Configure these variables in the deployment environment:

- `STRIPE_SECRET_KEY` — Stripe server-side secret key.
- `STRIPE_WEBHOOK_SECRET` — signing secret for the Stripe webhook endpoint.
- `PUBLIC_BASE_URL` — public HTTPS base URL of this API.

## Stripe webhook

Create a Stripe webhook endpoint pointing to:

`https://<your-public-host>/api/payments/stripe/webhook`

Subscribe at least to:

- `checkout.session.completed`
- `checkout.session.expired`
- `checkout.session.async_payment_succeeded`

The webhook signature is verified before payment state is changed.

## Flow

1. User starts TAROT and sends the question.
2. Bot asks for optional context.
3. Bot creates a US$1.00 Stripe Checkout Session and sends the URL.
4. No cards are drawn while payment is pending.
5. On confirmed payment, the Stripe webhook resumes the existing WhatsApp flow automatically.
6. If the Checkout Session expires without payment, the pending Tarot operation is canceled and the user is returned to the main menu.
7. Sending CANCEL/CANCELAR while payment is pending also cancels the pending Checkout Session and Tarot flow.

Checkout Sessions are configured to expire after approximately 30 minutes.
