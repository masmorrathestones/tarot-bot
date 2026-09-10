from __future__ import annotations

import argparse
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.database.session import SessionLocal
from app.social.x.models import ScheduledXPostEntity
from app.tarot.deck import RIDER_WAITE_DECK


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CAMPAIGN_ID = "tarot-card-series-v1"
CTA_TEXT = "Quer uma leitura personalizada? 🔮\n+55 21 99228-3542\nwa.me/5521992283542"

_CARD_COPY_DATA = """
THE_FOOL|O Louco|Novos começos, espontaneidade e liberdade; na sombra, ingenuidade e imprudência.
THE_MAGICIAN|O Mago|Iniciativa, habilidade e poder de realização; na sombra, manipulação ou confiança excessiva.
THE_HIGH_PRIESTESS|A Sacerdotisa|Intuição, silêncio e conhecimento interior; na sombra, passividade, segredos e confusão.
THE_EMPRESS|A Imperatriz|Criatividade, fertilidade e crescimento; na sombra, excesso, dependência ou energia criativa sem direção.
THE_EMPEROR|O Imperador|Estrutura, responsabilidade e estabilidade; na sombra, rigidez, controle e autoritarismo.
THE_HIEROPHANT|O Hierofante|Valores, tradição e busca de sentido; na sombra, dogmatismo e obediência sem reflexão.
THE_LOVERS|Os Enamorados|Amor, união e escolhas feitas de coração; na sombra, indecisão, divisão e medo de compromisso.
THE_CHARIOT|O Carro|Coragem, avanço e independência; na sombra, pressa, arrogância ou movimento sem direção.
STRENGTH|A Força|Vitalidade, coragem e domínio dos impulsos; na sombra, repressão, orgulho ou paixão descontrolada.
THE_HERMIT|O Eremita|Reflexão, sabedoria e autonomia; na sombra, isolamento e afastamento excessivo.
WHEEL_OF_FORTUNE|A Roda da Fortuna|Mudanças de ciclo e viradas inevitáveis; na sombra, repetição de padrões e resistência ao tempo.
JUSTICE|A Justiça|Verdade, equilíbrio e responsabilidade; na sombra, julgamento enviesado e fuga das consequências.
THE_HANGED_MAN|O Enforcado|Pausa, entrega e mudança de perspectiva; na sombra, estagnação e sacrifício sem aprendizado.
DEATH|A Morte|Fim, desapego e transformação; na sombra, medo de encerrar o que já cumpriu seu ciclo.
TEMPERANCE|A Temperança|Moderação, harmonia e integração; na sombra, extremos, impaciência e desequilíbrio.
THE_DEVIL|O Diabo|Desejos, vínculos e aspectos ocultos que pedem consciência; na sombra, compulsão, dependência e autoengano.
THE_TOWER|A Torre|Ruptura de estruturas falsas e libertação; na sombra, resistência a uma verdade que já não pode ser contida.
THE_STAR|A Estrela|Esperança, confiança e visão de futuro; na sombra, desânimo e dificuldade de enxergar possibilidades.
THE_MOON|A Lua|Mistério, inconsciente e travessia da incerteza; na sombra, medo, projeção e confusão.
THE_SUN|O Sol|Alegria, vitalidade e clareza; na sombra, vaidade, excesso de exposição ou otimismo forçado.
JUDGEMENT|O Julgamento|Despertar, chamado e libertação; na sombra, medo de responder ao que precisa mudar.
THE_WORLD|O Mundo|Conclusão, realização e integração; na sombra, pendências que impedem o fechamento de um ciclo.
ACE_OF_WANDS|Ás de Paus|Oportunidade, iniciativa e energia criativa; na sombra, impulso desperdiçado ou ação sem direção.
TWO_OF_WANDS|Dois de Paus|Planejamento e possibilidades futuras; na sombra, indecisão e distância entre intenção e ação.
THREE_OF_WANDS|Três de Paus|Expansão, visão e uma base para crescer; na sombra, planos grandes apoiados em fundamentos frágeis.
FOUR_OF_WANDS|Quatro de Paus|Celebração, estabilidade e comunidade; na sombra, conforto que vira acomodação.
FIVE_OF_WANDS|Cinco de Paus|Conflito, competição e teste de forças; na sombra, disputa improdutiva e desgaste.
SIX_OF_WANDS|Seis de Paus|Reconhecimento, vitória e confiança; na sombra, vaidade e dependência de aprovação.
SEVEN_OF_WANDS|Sete de Paus|Coragem para defender sua posição; na sombra, defensividade e esgotamento.
EIGHT_OF_WANDS|Oito de Paus|Movimento, notícias e aceleração; na sombra, pressa, atropelo e caos.
NINE_OF_WANDS|Nove de Paus|Resistência, perseverança e limites; na sombra, paranoia e cansaço acumulado.
TEN_OF_WANDS|Dez de Paus|Responsabilidade, esforço e carga; na sombra, sobrecarga e dificuldade de delegar.
PAGE_OF_WANDS|Pajem de Paus|Curiosidade, entusiasmo e começo de aventura; na sombra, imaturidade e dispersão.
KNIGHT_OF_WANDS|Cavaleiro de Paus|Paixão, ação e aventura; na sombra, impulsividade e inconstância.
QUEEN_OF_WANDS|Rainha de Paus|Carisma, confiança e independência; na sombra, ciúme, orgulho e controle.
KING_OF_WANDS|Rei de Paus|Liderança, visão e coragem; na sombra, autoritarismo e ego.
ACE_OF_CUPS|Ás de Copas|Abertura emocional, amor e intuição; na sombra, bloqueio afetivo ou emoções transbordando.
TWO_OF_CUPS|Dois de Copas|Parceria, reciprocidade e encontro; na sombra, desequilíbrio e dependência.
THREE_OF_CUPS|Três de Copas|Amizade, celebração e apoio; na sombra, superficialidade e excessos.
FOUR_OF_CUPS|Quatro de Copas|Introspecção e reavaliação emocional; na sombra, apatia e oportunidades ignoradas.
FIVE_OF_CUPS|Cinco de Copas|Perda, luto e decepção; na sombra, fixação no que faltou e dificuldade de ver o que permanece.
SIX_OF_CUPS|Seis de Copas|Memória, afeto e vínculos com o passado; na sombra, idealização e apego ao que já foi.
SEVEN_OF_CUPS|Sete de Copas|Opções, imaginação e desejo; na sombra, ilusão, confusão e escolhas sem base.
EIGHT_OF_CUPS|Oito de Copas|Afastamento e busca de algo com mais sentido; na sombra, fuga e medo de desapegar de verdade.
NINE_OF_CUPS|Nove de Copas|Satisfação, prazer e desejos realizados; na sombra, excesso e autossatisfação.
TEN_OF_CUPS|Dez de Copas|Harmonia emocional, família e pertencimento; na sombra, idealização e pressão por perfeição.
PAGE_OF_CUPS|Pajem de Copas|Sensibilidade, mensagem afetiva e intuição; na sombra, ingenuidade emocional.
KNIGHT_OF_CUPS|Cavaleiro de Copas|Romance, convite e imaginação; na sombra, idealização e promessas vazias.
QUEEN_OF_CUPS|Rainha de Copas|Empatia, intuição e maturidade emocional; na sombra, absorver demais as emoções alheias.
KING_OF_CUPS|Rei de Copas|Equilíbrio emocional e compaixão; na sombra, repressão ou manipulação emocional.
ACE_OF_SWORDS|Ás de Espadas|Clareza, verdade e decisão; na sombra, dureza, confusão ou uso cortante da razão.
TWO_OF_SWORDS|Dois de Espadas|Impasse, pausa e escolha difícil; na sombra, negação e adiamento da decisão.
THREE_OF_SWORDS|Três de Espadas|Dor, separação e uma verdade difícil; na sombra, ruminação e apego à mágoa.
FOUR_OF_SWORDS|Quatro de Espadas|Descanso, recuperação e reflexão; na sombra, estagnação e isolamento prolongado.
FIVE_OF_SWORDS|Cinco de Espadas|Conflito e o preço de vencer a qualquer custo; na sombra, ressentimento e humilhação.
SIX_OF_SWORDS|Seis de Espadas|Transição e afastamento da turbulência; na sombra, levar o passado junto para onde se vai.
SEVEN_OF_SWORDS|Sete de Espadas|Estratégia, discrição e autonomia; na sombra, engano e fuga de responsabilidade.
EIGHT_OF_SWORDS|Oito de Espadas|Restrição, medo e sensação de aprisionamento; na sombra, acreditar que não existe saída.
NINE_OF_SWORDS|Nove de Espadas|Ansiedade, preocupação e culpa; na sombra, pensamento catastrófico e sofrimento antecipado.
TEN_OF_SWORDS|Dez de Espadas|Fim doloroso, esgotamento e encerramento; na sombra, resistência a aceitar que algo terminou.
PAGE_OF_SWORDS|Pajem de Espadas|Curiosidade mental, vigilância e comunicação; na sombra, fofoca e desconfiança.
KNIGHT_OF_SWORDS|Cavaleiro de Espadas|Ação mental, urgência e franqueza; na sombra, agressividade e precipitação.
QUEEN_OF_SWORDS|Rainha de Espadas|Lucidez, independência e bons limites; na sombra, frieza e cinismo.
KING_OF_SWORDS|Rei de Espadas|Razão, autoridade e justiça; na sombra, rigidez e uso frio do poder.
ACE_OF_PENTACLES|Ás de Ouros|Oportunidade material, segurança e uma semente concreta; na sombra, apego ou chance desperdiçada.
TWO_OF_PENTACLES|Dois de Ouros|Equilíbrio, gestão e adaptação; na sombra, desorganização e sobrecarga.
THREE_OF_PENTACLES|Três de Ouros|Trabalho em equipe, ofício e reconhecimento; na sombra, falta de cooperação ou qualidade.
FOUR_OF_PENTACLES|Quatro de Ouros|Segurança, controle e preservação; na sombra, avareza e medo de perder.
FIVE_OF_PENTACLES|Cinco de Ouros|Escassez, dificuldade e sensação de exclusão; na sombra, isolamento e recusa de ajuda.
SIX_OF_PENTACLES|Seis de Ouros|Troca, generosidade e reciprocidade; na sombra, dívida, desigualdade e controle pela ajuda.
SEVEN_OF_PENTACLES|Sete de Ouros|Paciência, avaliação e investimento; na sombra, impaciência ou insistência sem retorno.
EIGHT_OF_PENTACLES|Oito de Ouros|Prática, aprendizado e dedicação; na sombra, perfeccionismo e trabalho mecânico.
NINE_OF_PENTACLES|Nove de Ouros|Autonomia, conforto e resultado conquistado; na sombra, isolamento e materialismo.
TEN_OF_PENTACLES|Dez de Ouros|Legado, família e estabilidade; na sombra, peso de expectativas e conflitos patrimoniais.
PAGE_OF_PENTACLES|Pajem de Ouros|Estudo, oportunidade prática e começo concreto; na sombra, procrastinação e falta de foco.
KNIGHT_OF_PENTACLES|Cavaleiro de Ouros|Constância, responsabilidade e método; na sombra, lentidão e rigidez.
QUEEN_OF_PENTACLES|Rainha de Ouros|Cuidado concreto, prosperidade e pragmatismo; na sombra, sobrecarga e materialismo.
KING_OF_PENTACLES|Rei de Ouros|Domínio material, estabilidade e liderança; na sombra, ganância e controle.
""".strip()

CARD_COPY: dict[str, tuple[str, str]] = {}
for _line in _CARD_COPY_DATA.splitlines():
    _code, _name, _summary = _line.split("|", 2)
    CARD_COPY[_code] = (_name, _summary)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Schedule one Portuguese Tarot-card thread per day on X."
    )
    parser.add_argument("--start-date", help="YYYY-MM-DD; defaults to tomorrow.")
    parser.add_argument("--time", default="12:00", help="Local root-post time, HH:MM.")
    parser.add_argument("--timezone", default="America/Sao_Paulo")
    parser.add_argument("--campaign-id", default=DEFAULT_CAMPAIGN_ID)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    tz = ZoneInfo(args.timezone)
    now_local = datetime.now(timezone.utc).astimezone(tz)
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    else:
        start_date = now_local.date() + timedelta(days=1)
    root_time = time.fromisoformat(args.time)

    deck_codes = {card.code for card in RIDER_WAITE_DECK}
    copy_codes = set(CARD_COPY)
    if deck_codes != copy_codes:
        missing = sorted(deck_codes - copy_codes)
        extra = sorted(copy_codes - deck_codes)
        raise RuntimeError(f"CARD_COPY mismatch. Missing={missing} extra={extra}")

    db = SessionLocal()
    inserted = 0
    try:
        for day_offset, card in enumerate(RIDER_WAITE_DECK):
            pt_name, summary = CARD_COPY[card.code]
            root_source_key = f"{args.campaign_id}:{card.code}:root"[:160]
            cta_source_key = f"{args.campaign_id}:{card.code}:cta"[:160]
            root_dt = datetime.combine(
                start_date + timedelta(days=day_offset),
                root_time,
                tzinfo=tz,
            ).astimezone(timezone.utc)
            cta_dt = root_dt + timedelta(minutes=1)

            media_path = f"app/assets/arcana/{card.name}.jpg"
            if not (PROJECT_ROOT / media_path).is_file():
                raise RuntimeError(f"Tarot image not found: {media_path}")

            root = db.scalar(
                select(ScheduledXPostEntity).where(
                    ScheduledXPostEntity.source_key == root_source_key
                )
            )
            if root is None:
                db.add(
                    ScheduledXPostEntity(
                        text=f"🃏 Carta {day_offset + 1}/78 — {pt_name}\n\n{summary}",
                        language="pt",
                        source_key=root_source_key,
                        media_path=media_path,
                        parent_source_key=None,
                        scheduled_at=root_dt,
                        status="PENDING",
                    )
                )
                inserted += 1

            cta = db.scalar(
                select(ScheduledXPostEntity).where(
                    ScheduledXPostEntity.source_key == cta_source_key
                )
            )
            if cta is None:
                db.add(
                    ScheduledXPostEntity(
                        text=CTA_TEXT,
                        language="pt",
                        source_key=cta_source_key,
                        media_path=None,
                        parent_source_key=root_source_key,
                        scheduled_at=cta_dt,
                        status="PENDING",
                    )
                )
                inserted += 1

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(
        f"Scheduled {inserted} rows for {len(RIDER_WAITE_DECK)} daily Tarot threads "
        f"starting {start_date.isoformat()} at {args.time} {args.timezone}."
    )


if __name__ == "__main__":
    main()
