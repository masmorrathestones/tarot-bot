from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse


router = APIRouter(tags=["Landing"])

WHATSAPP_NUMBER = "5521992283542"

_COPY = {
    "pt": {
        "lang": "pt-BR",
        "eyebrow": "TAROT • ASTROLOGIA • PERSONALIDADE",
        "title": "Uma leitura que vai além das cartas.",
        "subtitle": "A Holomancy combina Tarot, mapa astral, aspectos de personalidade e o contexto da sua pergunta em uma leitura profunda e integrada.",
        "price": "Leitura completa por R$6",
        "cta": "Começar leitura no WhatsApp",
        "note": "Você será direcionado para o WhatsApp oficial da Holomancy.",
        "benefit1_title": "Leitura personalizada",
        "benefit1_text": "As cartas são interpretadas em conjunto com o seu contexto e perfil simbólico.",
        "benefit2_title": "Visão holística",
        "benefit2_text": "Tarot, astrologia e personalidade são analisados como partes de um mesmo sistema.",
        "benefit3_title": "Direto no WhatsApp",
        "benefit3_text": "Sem cadastro complicado. Faça sua pergunta e siga o fluxo da leitura pelo bot.",
        "annual": "Análise anual de perfil grátis",
        "annual_text": "Signo, Arcano Pessoal, Arcano do Ano, mapa astral e aspectos de personalidade podem complementar suas leituras.",
        "footer": "Holomancy Tarot • mais que cartas, conexões.",
        "wa_text": "Olá! Quero fazer uma leitura Holomancy.",
    },
    "en": {
        "lang": "en",
        "eyebrow": "TAROT • ASTROLOGY • PERSONALITY",
        "title": "A reading that goes beyond the cards.",
        "subtitle": "Holomancy combines Tarot, your natal chart, personality traits and the context of your question into one deep, integrated reading.",
        "price": "Complete reading for US$1",
        "cta": "Start your reading on WhatsApp",
        "note": "You will be redirected to Holomancy's official WhatsApp.",
        "benefit1_title": "Personalized reading",
        "benefit1_text": "The cards are interpreted together with your context and symbolic profile.",
        "benefit2_title": "Holistic perspective",
        "benefit2_text": "Tarot, astrology and personality are analyzed as parts of the same system.",
        "benefit3_title": "Directly on WhatsApp",
        "benefit3_text": "No complicated signup. Ask your question and follow the reading flow in the bot.",
        "annual": "Free annual profile analysis",
        "annual_text": "Zodiac sign, Personal Arcana, Year Arcana, natal chart and personality traits can complement your readings.",
        "footer": "Holomancy Tarot • more than cards, connections.",
        "wa_text": "Hello! I want a Holomancy reading.",
    },
    "es": {
        "lang": "es",
        "eyebrow": "TAROT • ASTROLOGÍA • PERSONALIDAD",
        "title": "Una lectura que va más allá de las cartas.",
        "subtitle": "Holomancy combina Tarot, carta natal, aspectos de personalidad y el contexto de tu pregunta en una lectura profunda e integrada.",
        "price": "Lectura completa por US$1",
        "cta": "Comenzar lectura en WhatsApp",
        "note": "Serás dirigido al WhatsApp oficial de Holomancy.",
        "benefit1_title": "Lectura personalizada",
        "benefit1_text": "Las cartas se interpretan junto con tu contexto y tu perfil simbólico.",
        "benefit2_title": "Visión holística",
        "benefit2_text": "Tarot, astrología y personalidad se analizan como partes de un mismo sistema.",
        "benefit3_title": "Directo en WhatsApp",
        "benefit3_text": "Sin registros complicados. Haz tu pregunta y sigue el flujo de la lectura en el bot.",
        "annual": "Análisis anual de perfil gratis",
        "annual_text": "Signo zodiacal, Arcano Personal, Arcano del Año, carta natal y personalidad pueden complementar tus lecturas.",
        "footer": "Holomancy Tarot • más que cartas, conexiones.",
        "wa_text": "¡Hola! Quiero hacer una lectura Holomancy.",
    },
}


@router.get("/tarot", response_class=HTMLResponse)
def tarot_landing_page(lang: str = Query(default="pt")) -> HTMLResponse:
    language = lang.lower().strip()
    copy = _COPY.get(language, _COPY["pt"])
    whatsapp_url = f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(copy['wa_text'])}"

    html = f"""<!doctype html>
<html lang="{copy['lang']}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Holomancy Tarot: leitura holística com Tarot, astrologia e personalidade.">
  <meta name="theme-color" content="#090714">
  <title>Holomancy Tarot</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #090714;
      --panel: rgba(19, 14, 34, .82);
      --panel-strong: rgba(27, 18, 47, .95);
      --gold: #e8c77f;
      --gold-soft: #f5e4b8;
      --violet: #8f68d8;
      --text: #f8f3ff;
      --muted: #c9bed9;
      --whatsapp: #20b968;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at 20% 12%, rgba(118, 72, 176, .28), transparent 28rem),
        radial-gradient(circle at 83% 24%, rgba(64, 45, 128, .22), transparent 25rem),
        radial-gradient(circle at 50% 100%, rgba(190, 142, 65, .10), transparent 30rem),
        linear-gradient(145deg, #080611 0%, #110b20 48%, #06050d 100%);
      overflow-x: hidden;
    }}
    body::before {{
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      opacity: .45;
      background-image:
        radial-gradient(circle at 15% 24%, #fff 0 1px, transparent 1.5px),
        radial-gradient(circle at 72% 12%, #fff 0 1px, transparent 1.5px),
        radial-gradient(circle at 84% 64%, #e8c77f 0 1px, transparent 1.5px),
        radial-gradient(circle at 36% 78%, #fff 0 1px, transparent 1.5px),
        radial-gradient(circle at 56% 36%, #b99be8 0 1px, transparent 1.5px);
      background-size: 240px 240px, 310px 310px, 280px 280px, 360px 360px, 420px 420px;
    }}
    a {{ color: inherit; }}
    .wrap {{ width: min(1120px, calc(100% - 32px)); margin: 0 auto; position: relative; }}
    .nav {{ display: flex; justify-content: space-between; align-items: center; padding: 26px 0; gap: 18px; }}
    .brand {{ font-family: Georgia, "Times New Roman", serif; font-size: clamp(1.4rem, 4vw, 2rem); color: var(--gold-soft); letter-spacing: .02em; }}
    .langs {{ display: flex; gap: 8px; }}
    .langs a {{ text-decoration: none; border: 1px solid rgba(232,199,127,.32); padding: 7px 10px; border-radius: 999px; color: var(--muted); font-size: .82rem; }}
    .langs a:hover {{ border-color: var(--gold); color: var(--gold-soft); }}
    .hero {{ min-height: 72vh; display: grid; grid-template-columns: 1.1fr .9fr; align-items: center; gap: 48px; padding: 54px 0 70px; }}
    .eyebrow {{ color: var(--gold); letter-spacing: .20em; font-weight: 700; font-size: .76rem; margin-bottom: 18px; }}
    h1 {{ font-family: Georgia, "Times New Roman", serif; font-size: clamp(3rem, 7.5vw, 6.6rem); line-height: .94; margin: 0 0 26px; letter-spacing: -.045em; font-weight: 500; }}
    .lead {{ color: var(--muted); font-size: clamp(1rem, 2.1vw, 1.3rem); line-height: 1.7; max-width: 760px; margin-bottom: 24px; }}
    .price {{ display: inline-block; color: var(--gold-soft); border: 1px solid rgba(232,199,127,.5); background: rgba(58,37,86,.55); padding: 10px 16px; border-radius: 12px; font-weight: 750; margin-bottom: 24px; }}
    .cta {{ display: inline-flex; align-items: center; justify-content: center; gap: 12px; background: linear-gradient(135deg, #159956, var(--whatsapp)); color: white; text-decoration: none; font-weight: 800; font-size: 1.04rem; padding: 17px 23px; border-radius: 999px; box-shadow: 0 14px 42px rgba(20, 178, 97, .27); transition: transform .18s ease, box-shadow .18s ease; }}
    .cta:hover {{ transform: translateY(-2px); box-shadow: 0 18px 48px rgba(20, 178, 97, .38); }}
    .cta-icon {{ width: 24px; height: 24px; display: grid; place-items: center; border: 2px solid white; border-radius: 50%; font-size: .78rem; }}
    .note {{ color: #9f95ae; font-size: .82rem; margin: 12px 0 0 4px; }}
    .orb-wrap {{ display: grid; place-items: center; min-height: 420px; }}
    .orb {{ width: min(390px, 84vw); aspect-ratio: 1; border-radius: 50%; position: relative; display: grid; place-items: center; background: radial-gradient(circle at 43% 37%, rgba(249,234,196,.95) 0 2%, rgba(154,116,212,.55) 4%, rgba(48,28,91,.84) 36%, rgba(6,5,15,.96) 70%); border: 1px solid rgba(232,199,127,.55); box-shadow: 0 0 0 14px rgba(232,199,127,.035), 0 0 90px rgba(123,83,193,.27), inset 0 0 60px rgba(0,0,0,.55); }}
    .orb::before, .orb::after {{ content: ""; position: absolute; border: 1px solid rgba(232,199,127,.34); border-radius: 50%; }}
    .orb::before {{ inset: 9%; }} .orb::after {{ inset: 18%; }}
    .symbol {{ font-family: Georgia, serif; font-size: clamp(4rem, 10vw, 7rem); color: var(--gold-soft); text-shadow: 0 0 28px rgba(232,199,127,.28); z-index: 2; }}
    .features {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; padding: 0 0 24px; }}
    .card {{ background: linear-gradient(155deg, var(--panel-strong), var(--panel)); border: 1px solid rgba(232,199,127,.22); border-radius: 20px; padding: 24px; min-height: 190px; box-shadow: 0 20px 55px rgba(0,0,0,.18); }}
    .card .num {{ color: var(--gold); font-family: Georgia, serif; font-size: 2rem; margin-bottom: 18px; }}
    .card h2 {{ font-family: Georgia, serif; font-weight: 500; margin: 0 0 11px; color: var(--gold-soft); font-size: 1.35rem; }}
    .card p {{ color: var(--muted); line-height: 1.6; margin: 0; }}
    .annual {{ margin: 34px 0 70px; padding: 30px; border-radius: 24px; border: 1px solid rgba(232,199,127,.28); background: linear-gradient(110deg, rgba(69,41,101,.55), rgba(21,14,37,.75)); display: flex; align-items: center; justify-content: space-between; gap: 24px; }}
    .annual h2 {{ font-family: Georgia, serif; color: var(--gold-soft); font-weight: 500; font-size: clamp(1.7rem, 4vw, 2.4rem); margin: 0 0 9px; }}
    .annual p {{ color: var(--muted); margin: 0; max-width: 760px; line-height: 1.6; }}
    footer {{ text-align: center; color: #8f849e; padding: 0 0 42px; font-size: .88rem; }}
    @media (max-width: 820px) {{
      .hero {{ grid-template-columns: 1fr; padding-top: 30px; gap: 20px; }}
      .orb-wrap {{ min-height: 300px; order: -1; }}
      .orb {{ width: min(270px, 72vw); }}
      .features {{ grid-template-columns: 1fr; }}
      .annual {{ flex-direction: column; align-items: flex-start; }}
      .nav {{ align-items: flex-start; }}
      .langs {{ flex-wrap: wrap; justify-content: flex-end; }}
    }}
  </style>
</head>
<body>
  <main class="wrap">
    <nav class="nav" aria-label="Holomancy">
      <div class="brand">✦ Holomancy Tarot</div>
      <div class="langs" aria-label="Language">
        <a href="/tarot?lang=pt">PT</a>
        <a href="/tarot?lang=en">EN</a>
        <a href="/tarot?lang=es">ES</a>
      </div>
    </nav>

    <section class="hero">
      <div>
        <div class="eyebrow">{copy['eyebrow']}</div>
        <h1>{copy['title']}</h1>
        <p class="lead">{copy['subtitle']}</p>
        <div class="price">{copy['price']}</div><br>
        <a class="cta" href="{whatsapp_url}" target="_blank" rel="noopener noreferrer">
          <span class="cta-icon">☎</span>{copy['cta']}
        </a>
        <p class="note">{copy['note']}</p>
      </div>
      <div class="orb-wrap" aria-hidden="true">
        <div class="orb"><div class="symbol">☾✦☉</div></div>
      </div>
    </section>

    <section class="features">
      <article class="card"><div class="num">01</div><h2>{copy['benefit1_title']}</h2><p>{copy['benefit1_text']}</p></article>
      <article class="card"><div class="num">02</div><h2>{copy['benefit2_title']}</h2><p>{copy['benefit2_text']}</p></article>
      <article class="card"><div class="num">03</div><h2>{copy['benefit3_title']}</h2><p>{copy['benefit3_text']}</p></article>
    </section>

    <section class="annual">
      <div><h2>{copy['annual']}</h2><p>{copy['annual_text']}</p></div>
      <a class="cta" href="{whatsapp_url}" target="_blank" rel="noopener noreferrer">{copy['cta']}</a>
    </section>

    <footer>{copy['footer']}</footer>
  </main>
</body>
</html>"""
    return HTMLResponse(content=html)
