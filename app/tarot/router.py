from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.tarot.schemas import (
    DrawRequest,
    DrawResponse,
    DrawnCardResponse,
    SpreadPositionResponse,
    SpreadResponse,
    TarotCardResponse,
    CardMetadataResponse,
    InterpretationKnowledgeResponse,
    TarotReadRequest,
    TarotReadResponse,
    TarotInterpretationResponse,
    PersistedReadingResponse,
)
from app.tarot.service import tarot_draw_service
from app.ai.service import (
    tarot_interpretation_service,
    UserSymbolicProfile,
)
from app.ai.provider import AIConfigurationError, AIProviderError
from app.database.session import get_db
from app.tarot.persistence_service import (
    ReadingNotFoundError,
    ReadingRetryNotAllowedError,
    reading_persistence_service,
)
from app.users.service import UserNotFoundError, user_service


router = APIRouter(
    prefix="/api/tarot",
    tags=["Tarot"]
)


def map_position(position):
    return SpreadPositionResponse(
        index=position.index,
        code=position.code,
        name=position.name,
        description=position.description
    )


def map_spread(spread):
    return SpreadResponse(
        code=spread.code,
        name=spread.name,
        description=spread.description,
        positions=[map_position(position) for position in spread.positions]
    )


def map_card(card):
    metadata = None

    if card.metadata is not None:
        metadata = CardMetadataResponse(
            upright_keywords=list(card.metadata.upright_keywords),
            upright_meaning=card.metadata.upright_meaning,
            reversed_keywords=list(card.metadata.reversed_keywords),
            reversed_meaning=card.metadata.reversed_meaning,
            element=card.metadata.element,
            astrological_association=card.metadata.astrological_association,
            source_page=card.metadata.source_page,
            reversed_is_derived=card.metadata.reversed_is_derived
        )

    return TarotCardResponse(
        id=card.id,
        code=card.code,
        name=card.name,
        arcana=card.arcana,
        number=card.number,
        suit=card.suit,
        metadata=metadata
    )


@router.get("/cards", response_model=list[TarotCardResponse])
def list_cards():
    return [map_card(card) for card in tarot_draw_service.list_cards()]


@router.get("/cards/{card_id}", response_model=TarotCardResponse)
def get_card(card_id: int):
    card = next(
        (
            card
            for card in tarot_draw_service.list_cards()
            if card.id == card_id
        ),
        None
    )

    if card is None:
        raise HTTPException(
            status_code=404,
            detail="Card not found"
        )

    return map_card(card)


@router.get("/spreads", response_model=list[SpreadResponse])
def list_spreads():
    return [
        map_spread(spread)
        for spread in tarot_draw_service.list_spreads()
    ]


@router.get("/spreads/{spread_code}", response_model=SpreadResponse)
def get_spread(spread_code: str):
    spread = tarot_draw_service.get_spread(spread_code)

    if spread is None:
        raise HTTPException(
            status_code=404,
            detail="Spread not found"
        )

    return map_spread(spread)


@router.get(
    "/cards/{card_id}/interpretation",
    response_model=InterpretationKnowledgeResponse
)
def get_card_interpretation(card_id: int):
    card = next(
        (
            card
            for card in tarot_draw_service.list_cards()
            if card.id == card_id
        ),
        None
    )

    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")

    knowledge = tarot_draw_service.get_interpretation_knowledge(card.code)

    if knowledge is None:
        raise HTTPException(
            status_code=404,
            detail="Interpretation knowledge not found"
        )

    return InterpretationKnowledgeResponse(
        card_code=card.code,
        card_name=card.name,
        general=knowledge.general,
        career=knowledge.career,
        consciousness=knowledge.consciousness,
        relationships=knowledge.relationships,
        source_page=knowledge.source_page,
        source=knowledge.source,
        language=knowledge.language,
        is_paraphrase=knowledge.is_paraphrase
    )


@router.get(
    "/interpretations/{card_code}",
    response_model=InterpretationKnowledgeResponse
)
def get_interpretation_by_code(card_code: str):
    card = next(
        (
            card
            for card in tarot_draw_service.list_cards()
            if card.code == card_code.upper()
        ),
        None
    )

    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")

    knowledge = tarot_draw_service.get_interpretation_knowledge(card.code)

    if knowledge is None:
        raise HTTPException(
            status_code=404,
            detail="Interpretation knowledge not found"
        )

    return InterpretationKnowledgeResponse(
        card_code=card.code,
        card_name=card.name,
        general=knowledge.general,
        career=knowledge.career,
        consciousness=knowledge.consciousness,
        relationships=knowledge.relationships,
        source_page=knowledge.source_page,
        source=knowledge.source,
        language=knowledge.language,
        is_paraphrase=knowledge.is_paraphrase
    )


@router.post("/read", response_model=TarotReadResponse)
def create_ai_reading(
    request: TarotReadRequest,
    db: Session = Depends(get_db),
):
    spread = tarot_draw_service.get_spread(request.spread_code)

    if spread is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown spread_code '{request.spread_code}'. "
                "Use GET /api/tarot/spreads to see available spreads."
            ),
        )

    try:
        user = user_service.get(db, request.user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    drawn = tarot_draw_service.draw(
        spread=spread,
        allow_reversed=request.allow_reversed,
    )

    persisted = reading_persistence_service.create_pending(
        db=db,
        user_id=user.id,
        spread=spread,
        question=request.question,
        context=request.context,
        allow_reversed=request.allow_reversed,
        drawn_cards=drawn,
    )

    profile = UserSymbolicProfile.from_snapshot(persisted.profile_snapshot)

    try:
        interpretation = tarot_interpretation_service.interpret(
            question=request.question,
            context=request.context,
            spread=spread,
            drawn_cards=drawn,
            profile=profile,
        )
    except AIConfigurationError as exc:
        reading_persistence_service.mark_failed(
            db=db,
            reading_id=persisted.id,
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=503,
            detail={
                "message": str(exc),
                "reading_id": persisted.id,
                "cards_were_persisted": True,
            },
        ) from exc
    except AIProviderError as exc:
        reading_persistence_service.mark_failed(
            db=db,
            reading_id=persisted.id,
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=502,
            detail={
                "message": str(exc),
                "reading_id": persisted.id,
                "cards_were_persisted": True,
            },
        ) from exc

    completed = reading_persistence_service.mark_completed(
        db=db,
        reading_id=persisted.id,
        narrative=interpretation.narrative,
        card_analysis=interpretation.card_analysis,
        synthesis=interpretation.synthesis,
    )

    return TarotReadResponse(
        reading_id=completed.id,
        status=completed.status,
        retry_count=completed.retry_count,
        user_id=completed.user_id,
        deck=completed.deck_code,
        spread=map_spread(spread),
        question=completed.question,
        context=completed.context,
        profile_snapshot=completed.profile_snapshot,
        cards=[
            DrawnCardResponse(
                position=map_position(item.position),
                orientation=item.orientation,
                card=map_card(item.card),
            )
            for item in drawn
        ],
        interpretation=TarotInterpretationResponse(
            narrative=completed.narrative or "",
            card_analysis=completed.card_analysis or "",
            synthesis=completed.synthesis or "",
        ),
    )


@router.get(
    "/readings/{reading_id}",
    response_model=PersistedReadingResponse,
)
def get_persisted_reading(
    reading_id: int,
    db: Session = Depends(get_db),
):
    try:
        reading = reading_persistence_service.get(db, reading_id)
    except ReadingNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    drawn = reading_persistence_service.reconstruct_drawn_cards(reading)

    interpretation = None
    if (
        reading.narrative is not None
        and reading.card_analysis is not None
        and reading.synthesis is not None
    ):
        interpretation = TarotInterpretationResponse(
            narrative=reading.narrative,
            card_analysis=reading.card_analysis,
            synthesis=reading.synthesis,
        )

    return PersistedReadingResponse(
        reading_id=reading.id,
        status=reading.status,
        retry_count=reading.retry_count,
        user_id=reading.user_id,
        deck=reading.deck_code,
        spread_code=reading.spread_code,
        question=reading.question,
        context=reading.context,
        profile_snapshot=reading.profile_snapshot,
        cards=[
            DrawnCardResponse(
                position=map_position(item.position),
                orientation=item.orientation,
                card=map_card(item.card),
            )
            for item in drawn
        ],
        interpretation=interpretation,
        error_message=reading.error_message,
    )


@router.post(
    "/readings/{reading_id}/retry",
    response_model=TarotReadResponse,
)
def retry_ai_reading(
    reading_id: int,
    db: Session = Depends(get_db),
):
    try:
        reading = reading_persistence_service.begin_retry(
            db=db,
            reading_id=reading_id,
        )
    except ReadingNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReadingRetryNotAllowedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    # No draw call happens here. These are reconstructed from drawn_cards.
    drawn = reading_persistence_service.reconstruct_drawn_cards(reading)
    spread = tarot_draw_service.get_spread(reading.spread_code)

    if spread is None:
        reading_persistence_service.mark_failed(
            db=db,
            reading_id=reading.id,
            error_message=(
                "The persisted spread is no longer available: "
                f"{reading.spread_code}"
            ),
        )
        raise HTTPException(
            status_code=500,
            detail="Persisted spread definition is unavailable.",
        )

    profile = UserSymbolicProfile.from_snapshot(reading.profile_snapshot)

    try:
        interpretation = tarot_interpretation_service.interpret(
            question=reading.question,
            context=reading.context,
            spread=spread,
            drawn_cards=drawn,
            profile=profile,
        )
    except AIConfigurationError as exc:
        failed = reading_persistence_service.mark_failed(
            db=db,
            reading_id=reading.id,
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=503,
            detail={
                "message": str(exc),
                "reading_id": failed.id,
                "retry_count": failed.retry_count,
                "same_cards_preserved": True,
            },
        ) from exc
    except AIProviderError as exc:
        failed = reading_persistence_service.mark_failed(
            db=db,
            reading_id=reading.id,
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=502,
            detail={
                "message": str(exc),
                "reading_id": failed.id,
                "retry_count": failed.retry_count,
                "same_cards_preserved": True,
            },
        ) from exc

    completed = reading_persistence_service.mark_completed(
        db=db,
        reading_id=reading.id,
        narrative=interpretation.narrative,
        card_analysis=interpretation.card_analysis,
        synthesis=interpretation.synthesis,
    )

    return TarotReadResponse(
        reading_id=completed.id,
        status=completed.status,
        retry_count=completed.retry_count,
        user_id=completed.user_id,
        deck=completed.deck_code,
        spread=map_spread(spread),
        question=completed.question,
        context=completed.context,
        profile_snapshot=completed.profile_snapshot,
        cards=[
            DrawnCardResponse(
                position=map_position(item.position),
                orientation=item.orientation,
                card=map_card(item.card),
            )
            for item in drawn
        ],
        interpretation=TarotInterpretationResponse(
            narrative=completed.narrative or "",
            card_analysis=completed.card_analysis or "",
            synthesis=completed.synthesis or "",
        ),
    )


@router.post("/draw", response_model=DrawResponse)
def draw_cards(request: DrawRequest):
    spread = tarot_draw_service.get_spread(request.spread_code)

    if spread is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown spread_code '{request.spread_code}'. "
                "Use GET /api/tarot/spreads to see available spreads."
            )
        )

    drawn = tarot_draw_service.draw(
        spread=spread,
        allow_reversed=request.allow_reversed
    )

    return DrawResponse(
        deck="Rider-Waite-Smith",
        spread=map_spread(spread),
        question=request.question,
        context=request.context,
        cards=[
            DrawnCardResponse(
                position=map_position(item.position),
                orientation=item.orientation,
                card=map_card(item.card)
            )
            for item in drawn
        ]
    )
