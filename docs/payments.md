# Tarot payments

Each WhatsApp Tarot reading is paid through Stripe Checkout after the user provides optional context and before any cards are drawn.

The default prices are:

- **US$1.00** when paying in USD.
- **R$6.00** when paying in BRL.

The BRL price is a configured local price, not a live exchange-rate conversion. Both prices can be changed independently through environment variables.

## Required environment variables

Configure these variables in the deployment environment:

- `STRIPE_SECRET_KEY` — Stripe server-side secret/restricted key with permission to create Checkout Sessions.
- `STRIPE_WEBHOOK_SECRET` — signing secret for the Stripe webhook endpoint.
- `PUBLIC_BASE_URL` — public HTTPS base URL of this API.

Optional price overrides:

- `TAROT_PRICE_USD_CENTS` — USD amount in cents; defaults to `100`.
- `TAROT_PRICE_BRL_CENTS` — BRL amount in centavos; defaults to `600`.

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
3. Bot sends a payment link hosted by this API.
4. The payment page lets the user choose USD or BRL.
5. The user is redirected to the matching Stripe Checkout Session.
6. No cards are drawn while payment is pending.
7. On confirmed payment, the Stripe webhook resumes the existing WhatsApp flow automatically.
8. If the Checkout Session expires without payment, the pending Tarot operation is canceled and the user is returned to the main menu.
9. Sending CANCEL/CANCELAR while payment is pending also cancels the pending Checkout Session and Tarot flow.

Checkout Sessions are configured to expire after approximately 30 minutes.

The initial Checkout Session exists so an abandoned payment can still expire through Stripe even if the user never selects a currency. When a different currency is selected, the stored payment is moved to the newly created Checkout Session and the previous unused session is expired.
