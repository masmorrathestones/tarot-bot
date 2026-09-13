# Dream interpretation service

The WhatsApp commands `SONHOS`, `DREAM`, `SUEÑOS`, and `/dream` start a separate paid service.
The price defaults to US$3 or R$18 and can be overridden with `DREAM_PRICE_USD_CENTS` and
`DREAM_PRICE_BRL_CENTS`.

After payment the service stores a structured initial AI pass (up to ten sound-based linguistic
analogies and up to nine contextual questions), asks each question separately, and persists every
answer. A second structured pass saves up to five user-supplied durable facts in
`user_relevant_information`.

Symbol retrieval is deterministic: names in Portuguese, English, and Spanish are normalized for
case, accents and punctuation and matched on complete word/phrase boundaries. The final AI pass
receives a snapshot of every matched catalog row, including localized meaning, internal provenance,
the linguistic mapping and all question-answer pairs. The user-facing analysis is intentionally
unified and does not expose internal interpretive-school labels.
