# Past Life Tarot

The WhatsApp command `PAST LIFE`, `VIDAS PASSADAS`, or `VIDAS PASADAS` starts a
separate paid flow priced at US$2 or R$12.

## Flow

1. Payment is confirmed through the existing Stripe currency selector.
2. The user meditates for at least two minutes and sends `READY`, `PRONTO`, or `LISTO`.
3. The first word supplied by the user is normalized to A–Z values and reduced by
   repeated digit sums until it is at most 22. Values 1–21 map to their numbered
   Major Arcana and 22 maps to The Fool.
4. A six-card personality spread is sent as one image and analyzed in at most three paragraphs.
5. Five concrete themes are generated and scored from the word and saved profile;
   only the selected intuitive question is shown.
6. If rejected, an alternate theme is selected silently.
7. A second six-card spread is sent as one image and interpreted as behavior
   (1–2), profession (3–4), and place of life/death (5–6).
8. The user is asked whether the reading helped, and the response is persisted.

## Deployment

Run `alembic upgrade head`. Optional price overrides:

- `PAST_LIFE_PRICE_USD_CENTS` (default `200`)
- `PAST_LIFE_PRICE_BRL_CENTS` (default `1200`)
