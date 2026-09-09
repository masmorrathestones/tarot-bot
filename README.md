# Tarot Bot API

Versão 0.2 do backend em Python + FastAPI.

## Funcionalidades

- Rider-Waite-Smith com 78 cartas
- Sorteio sem repetição
- Cartas normais e invertidas
- Tipos de tiragem com posições semânticas
- 3 tiragens iniciais
- Swagger automático

## Tiragens disponíveis

### THREE_CARD_SITUATION
- Situação atual
- Obstáculo ou dinâmica
- Tendência

### PAST_PRESENT_FUTURE
- Passado
- Presente
- Futuro

### SELF_OTHER_RELATIONSHIP
- Você
- Outra pessoa
- Relação

## Executar

```bash
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Swagger:

http://127.0.0.1:8000/docs

## Endpoints

### GET /api/tarot/cards

Lista as 78 cartas.

### GET /api/tarot/cards/{id}

Busca uma carta pelo ID.

### GET /api/tarot/spreads

Lista os tipos de tiragem disponíveis.

### GET /api/tarot/spreads/{spread_code}

Busca a definição de uma tiragem.

### POST /api/tarot/draw

Exemplo:

```json
{
  "spread_code": "THREE_CARD_SITUATION",
  "allow_reversed": true,
  "question": "Como devo lidar com minha situação profissional?",
  "context": "Estou pensando em mudar de emprego."
}
```

Cada carta agora vem vinculada à sua posição semântica:

```json
{
  "position": {
    "index": 1,
    "code": "CURRENT_SITUATION",
    "name": "Situação atual",
    "description": "Representa o estado atual e o núcleo da questão apresentada."
  },
  "orientation": "UPRIGHT",
  "card": {
    "id": 17,
    "code": "THE_TOWER",
    "name": "The Tower",
    "arcana": "MAJOR",
    "number": 16,
    "suit": null
  }
}
```

## Próximos passos

- Imagens das cartas
- Metadados simbólicos das cartas
- Camada de interpretação por IA
- PostgreSQL e persistência
- Perfil do usuário
- WhatsApp


## Card metadata

Every card now includes:

- `upright_keywords`
- `upright_meaning`
- `reversed_keywords`
- `reversed_meaning`
- `element`
- `astrological_association`
- `source_page`
- `reversed_is_derived`

The meanings and astrology are summarized/translated from Hajo Banzhaf's
*Guia Completo do Tarô*.

Important source rule: this book does not provide a reversed-card system.
For that reason, reversed meanings are marked `reversed_is_derived=true`
and are derived from the card's blocked, excessive, immature, negative,
or shadow expressions described in the source.

For elements, the source explicitly maps:
Wands = Fire, Swords = Air, Pentacles = Earth, Cups = Water.
Major Arcana elements are left `null` because this source does not give
a systematic elemental attribution for them.


## Interpretation knowledge layer

A second, richer knowledge layer now exists in:

`app/tarot/interpretation_knowledge.py`

Each of the 78 cards contains four English paraphrases based on Hajo Banzhaf's
interpretive organization:

- `general`
- `career`
- `consciousness`
- `relationships`

The records also include:

- `source_page`
- `source`
- `language`
- `is_paraphrase`

These texts are compact paraphrases intended for future LLM context. They are
not quotations from the book.

### GET /api/tarot/cards/{card_id}/interpretation

Returns the complete interpretation knowledge for one card.

### GET /api/tarot/interpretations/{card_code}

Example:

`GET /api/tarot/interpretations/THE_TOWER`

This separation is intentional: `/api/tarot/cards` remains lightweight, while
the AI orchestration layer can load richer knowledge only for the cards actually
drawn in a reading.


## PostgreSQL persistence

The project now persists users and readings.

User data is intentionally limited to:
`name`, `whatsapp_number`, `sun_sign`, `moon_sign`, `rising_sign`, and `mbti`.

Tables:
`users`, `user_profiles`, `readings`, and `drawn_cards`.

Each reading stores a `profile_snapshot`. This keeps the historical profile
used for that reading even if the user changes their profile later.

Drawn cards are committed **before** the AI request. If the AI provider fails,
the reading remains stored in `FAILED` status with the original cards.

### Start PostgreSQL locally

```bash
docker compose up -d
```

Copy `.env.example` to `.env`, then:

```bash
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn main:app --reload
```

### Create a user

`POST /api/users`

```json
{
  "name": "Alex",
  "whatsapp_number": "+5521999999999",
  "profile": {
    "sun_sign": "Scorpio",
    "moon_sign": "Cancer",
    "rising_sign": "Libra",
    "mbti": "INFJ"
  }
}
```

Unknown profile values may be `null`.

### Create a persisted AI reading

`POST /api/tarot/read`

```json
{
  "user_id": 1,
  "spread_code": "THREE_CARD_SITUATION",
  "allow_reversed": true,
  "question": "What should I understand about this relationship?",
  "context": "Communication has been difficult lately."
}
```

The profile is now loaded from PostgreSQL automatically.

### Retrieve the exact same reading

`GET /api/tarot/readings/{reading_id}`

No new cards are drawn.


## Retry a failed reading without drawing new cards

If the AI provider fails, `POST /api/tarot/read` keeps the reading and its
cards in PostgreSQL with status `FAILED`.

Retry that exact reading with:

```http
POST /api/tarot/readings/{reading_id}/retry
```

The retry endpoint:

- accepts only readings whose status is `FAILED`;
- never calls the random draw service;
- reconstructs the exact cards, positions and orientations from `drawn_cards`;
- reuses the original question and context;
- reuses the historical `profile_snapshot`, not the user's current profile;
- increments `retry_count`;
- sets the status to `RETRYING` while the new AI attempt is running;
- returns the same `reading_id` on success.

Trying to retry a `COMPLETED`, `PENDING`, or already `RETRYING` reading returns
HTTP `409`, preventing accidental duplicate AI calls.

After adding this feature to an existing database, apply the new migration:

```bash
python -m alembic upgrade head
```

The database will then be at revision `0002_add_reading_retry_tracking`.


## WhatsApp conversational MVP

This version adds a conversational layer for the WhatsApp Cloud API.

### Database migration

Apply the new migration:

```bash
python -m alembic upgrade head
```

The new tables are:

- `whatsapp_conversations` — persistent conversation state
- `whatsapp_message_events` — inbound webhook deduplication and processing status

### Environment variables

Add these to `.env` when you are ready to connect Meta:

```env
WHATSAPP_VERIFY_TOKEN=choose-a-long-random-string
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_GRAPH_VERSION=
WHATSAPP_APP_SECRET=
```

`WHATSAPP_GRAPH_VERSION` is intentionally not hard-coded. Use the current
Graph API version configured/documented for your Meta app.

### Test the conversation before connecting Meta

Use:

`POST /api/whatsapp/test-message`

Example:

```json
{
  "from_number": "+5521999999999",
  "display_name": "Alex",
  "text": "What should I understand about my relationship?"
}
```

Call the same endpoint again with the same number to continue the conversation.

Typical flow:

1. question
2. context or `SKIP`
3. spread choice (`1`, `2`, or `3`)
4. reading is generated and persisted

Commands:

- `PROFILE` — update Sun, Moon, Rising and MBTI
- `NEW` — start a new reading
- `CANCEL` — reset the current flow
- `HELP` — show commands

Profile flow accepts `SKIP` for unknown values.

### Real webhook endpoints

Meta verification callback:

`GET /api/whatsapp/webhook`

Incoming webhook:

`POST /api/whatsapp/webhook`

The POST endpoint acknowledges quickly and performs conversational/AI work in a
FastAPI background task.

If `WHATSAPP_APP_SECRET` is configured, inbound payloads must have a valid
`X-Hub-Signature-256`.

Inbound Meta message IDs are persisted uniquely, so webhook retries do not
trigger duplicate tarot readings.

### Current WhatsApp MVP scope

Implemented:

- identify/create user by WhatsApp number
- use WhatsApp profile name when available
- optional Sun/Moon/Rising/MBTI onboarding
- persistent conversation state
- question + context flow
- spread selection
- persisted tarot reading
- AI interpretation
- text response delivery
- webhook deduplication
- webhook signature validation
- local simulator

Not implemented yet:

- card image delivery
- payment gating
- message templates
- durable job queue / worker
- multi-language conversation copy
