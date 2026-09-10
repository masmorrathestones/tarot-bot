# Daily Tarot + Weekly Astrology plan

## Product

The WhatsApp `PLAN` / `PLANO` command offers two billing choices after the user configures delivery times:

- recurring monthly: US$10.00 or R$60.00 per month;
- one month without renewal: US$11.00 or R$66.00.

The setup order is daily Tarot time, weekly astrology weekday, weekly astrology time, billing type, required profile/current-location completion, then Stripe payment.

## Profile requirements

Weekly astrology requires a complete natal profile: date of birth, exact birth time, birthplace, and the saved natal chart. The plan also stores a separate current location on `user_profiles` (`current_place`, latitude, longitude, timezone, update timestamp). Users are told to update it when travelling or moving. The current coordinates are used to calculate local angles/houses for the weekly forecast and the current timezone controls delivery scheduling.

## Daily Tarot

Once per scheduled day the service draws one random Rider-Waite-Smith card and orientation, sends the card image, and generates a compact daily interpretation focused on advice, cautions, opportunities and practical suggestions.

The daily AI context is deliberately smaller than a normal reading: card knowledge plus Personal Arcana, Year Arcana, MBTI-derived personalization, and exactly one hidden mystic intuition. The daily intuition always exists and its weight is sampled from 0 through 10 inclusive.

## Weekly astrology

The application calculates seven days of deterministic transit metadata with Swiss Ephemeris. It supplies planetary positions, major transit-to-natal aspects, and local Placidus Ascendant/Midheaven/house cusps calculated from the user's current coordinates. The AI interprets those calculated values; it is not asked to invent or calculate planetary positions.

The analysis gives an overall weekly outlook plus day-by-day tendencies and practical timing suggestions when supported by the calculated transits.

## Schedule changes

Changing the daily time cannot create a second delivery less than 24 hours after the last daily Tarot. The next delivery is the first occurrence of the newly selected clock time that satisfies that minimum interval.

Changing the weekly weekday/time follows the same rule with a seven-day minimum after the previous weekly analysis. This prevents users from repeatedly moving schedules forward to obtain extra deliveries.

## Cancellation

Recurring subscriptions use Stripe `cancel_at_period_end`. Cancelling therefore leaves the plan usable through the already-paid period but prevents automatic renewal. The one-month purchase has no automatic renewal and expires after its paid access period.

## Stripe webhook

The existing signed endpoint remains:

`POST /api/payments/stripe/webhook`

In addition to the existing Checkout events used by individual Tarot readings, configure Stripe to send these subscription events to the same endpoint:

- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`
- `invoice.paid`
- `customer.subscription.updated`
- `customer.subscription.deleted`

## Deployment

Run:

```bash
python -m alembic upgrade head
```

Expected Alembic head: `0015_daily_weekly_plan`.

Optional price/scheduler environment variables are documented in `.env.example`.

The scheduler runs inside the API process by default and checks due deliveries every 60 seconds. Delivery slots have a database uniqueness constraint to reduce duplicate sends if more than one process observes the same due slot.
