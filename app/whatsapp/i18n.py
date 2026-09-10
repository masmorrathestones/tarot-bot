from __future__ import annotations


SUPPORTED_LANGUAGES = ("en", "pt", "es")
LANGUAGE_NAMES = {"en": "English", "pt": "Português", "es": "Español"}

_LANGUAGE_ALIASES = {
    "1": "en", "en": "en", "english": "en", "inglês": "en", "ingles": "en",
    "2": "pt", "pt": "pt", "português": "pt", "portugues": "pt", "portuguese": "pt",
    "3": "es", "es": "es", "español": "es", "espanol": "es", "spanish": "es",
}


def normalize_language(value: str | None) -> str:
    if not value:
        return "en"
    value = value.strip().lower()
    return value if value in SUPPORTED_LANGUAGES else "en"


def parse_language_choice(value: str) -> str | None:
    return _LANGUAGE_ALIASES.get(value.strip().lower())


def language_selection_prompt() -> str:
    return (
        "🌐 Choose your language / Escolha seu idioma / Elige tu idioma:\n\n"
        "1 — English\n"
        "2 — Português\n"
        "3 — Español\n\n"
        "Reply with 1, 2 or 3."
    )


_MESSAGES = {
    "ask_name": {
        "en": "Hi! Before we begin, what would you like me to call you? Send me your name.",
        "pt": "Oi! Antes de começarmos, como você gostaria que eu te chamasse? Me envie seu nome.",
        "es": "¡Hola! Antes de empezar, ¿cómo te gustaría que te llamara? Envíame tu nombre.",
    },
    "ask_name_again": {
        "en": "Please tell me your name so I can finish setting up your profile.",
        "pt": "Por favor, me diga seu nome para eu concluir a configuração do seu perfil.",
        "es": "Por favor, dime tu nombre para que pueda terminar de configurar tu perfil.",
    },
    "welcome": {
        "en": "Hi, {name}! Welcome. ✨\n\nThis is a digital cartomancy experience designed to turn Tarot symbols into reflection, interpretation, and narrative.",
        "pt": "Oi, {name}! Bem-vindo. ✨\n\nEsta é uma experiência de cartomancia digital criada para transformar os símbolos do Tarô em reflexão, interpretação e narrativa.",
        "es": "¡Hola, {name}! Bienvenido. ✨\n\nEsta es una experiencia de cartomancia digital creada para transformar los símbolos del Tarot en reflexión, interpretación y narrativa.",
    },
    "main_menu": {
        "en": "What would you like to do?\n\nTAROT — start a Tarot card reading\nPROFILE — build your symbolic profile: zodiac sign, natal chart, MBTI personality, Personal Arcana, Year Arcana, and a saved annual profile analysis\nLANGUAGE — change language\nHELP — show this menu again\n\nA Tarot reading only starts after you send TAROT.",
        "pt": "O que você gostaria de fazer?\n\nTAROT — iniciar uma leitura de Tarô\nPERFIL — montar seu perfil simbólico: signo, mapa astral, personalidade MBTI, Arcano Pessoal, Arcano do Ano e uma análise anual salva do seu perfil\nIDIOMA — mudar o idioma\nAJUDA — mostrar este menu novamente\n\nUma leitura de Tarô só começa depois que você enviar TAROT.",
        "es": "¿Qué te gustaría hacer?\n\nTAROT — iniciar una lectura de Tarot\nPERFIL — crear tu perfil simbólico: signo, carta natal, personalidad MBTI, Arcano Personal, Arcano del Año y un análisis anual guardado de tu perfil\nIDIOMA — cambiar el idioma\nAYUDA — mostrar este menú de nuevo\n\nUna lectura de Tarot solo comienza después de que envíes TAROT.",
    },
    "language_changed": {
        "en": "Language changed to English.",
        "pt": "Idioma alterado para Português.",
        "es": "Idioma cambiado a Español.",
    },
    "cancelled": {
        "en": "The current action has been canceled.",
        "pt": "A ação atual foi cancelada.",
        "es": "La acción actual ha sido cancelada.",
    },
    "tarot_cancelled": {
        "en": "The Tarot reading has been canceled.",
        "pt": "A leitura de Tarô foi cancelada.",
        "es": "La lectura de Tarot ha sido cancelada.",
    },
    "with_cancel": {
        "en": "{text}\n\nSend CANCEL at any time to return to the main menu.",
        "pt": "{text}\n\nEnvie CANCELAR a qualquer momento para voltar ao menu principal.",
        "es": "{text}\n\nEnvía CANCELAR en cualquier momento para volver al menú principal.",
    },
    "reading_started": {
        "en": "🔮 Tarot reading started. Send the question you want to explore.",
        "pt": "🔮 Leitura de Tarô iniciada. Envie a pergunta que você quer explorar.",
        "es": "🔮 Lectura de Tarot iniciada. Envía la pregunta que quieres explorar.",
    },
    "send_question": {
        "en": "Send the question you want to explore.",
        "pt": "Envie a pergunta que você quer explorar.",
        "es": "Envía la pregunta que quieres explorar.",
    },
    "context_prompt": {
        "en": "Now add any context that may help with the reading, or reply SKIP if you want to continue with the question alone.",
        "pt": "Agora adicione qualquer contexto que possa ajudar na leitura, ou responda PULAR se quiser continuar apenas com a pergunta.",
        "es": "Ahora añade cualquier contexto que pueda ayudar con la lectura, o responde OMITIR si quieres continuar solo con la pregunta.",
    },
    "payment_required": {
        "en": "💳 This Tarot reading costs US$1.00. Open the link below and choose whether to pay in US dollars or Brazilian reais:\n\n{url}\n\nThe cards will only be drawn after payment is confirmed. The checkout expires in about 30 minutes; if it is not paid, the reading is canceled.",
        "pt": "💳 Esta leitura de Tarô custa US$ 1,00. Abra o link abaixo e escolha se quer pagar em dólar ou em reais:\n\n{url}\n\nAs cartas só serão tiradas após a confirmação do pagamento. O checkout expira em cerca de 30 minutos; se não houver pagamento, a leitura será cancelada.",
        "es": "💳 Esta lectura de Tarot cuesta US$1,00. Abre el enlace y elige si quieres pagar en dólares estadounidenses o en reales brasileños:\n\n{url}\n\nLas cartas solo se sacarán después de confirmar el pago. El checkout vence en unos 30 minutos; si no se paga, la lectura se cancela.",
    },
    "payment_pending": {
        "en": "Payment is still pending. Use the link below to choose USD or BRL and complete the checkout:\n\n{url}",
        "pt": "O pagamento ainda está pendente. Use o link abaixo para escolher dólar ou real e concluir o checkout:\n\n{url}",
        "es": "El pago sigue pendiente. Usa el enlace para elegir USD o BRL y completar el checkout:\n\n{url}",
    },
    "payment_confirmed": {
        "en": "✅ Payment confirmed. Your Tarot reading will continue now.",
        "pt": "✅ Pagamento confirmado. Sua leitura de Tarô vai continuar agora.",
        "es": "✅ Pago confirmado. Tu lectura de Tarot continuará ahora.",
    },
    "payment_expired": {
        "en": "The payment was not completed in time, so the Tarot reading was canceled. No cards were drawn.",
        "pt": "O pagamento não foi concluído a tempo, então a leitura de Tarô foi cancelada. Nenhuma carta foi tirada.",
        "es": "El pago no se completó a tiempo, así que la lectura de Tarot fue cancelada. No se sacó ninguna carta.",
    },
    "payment_unavailable": {
        "en": "I couldn't start the payment right now, so the Tarot operation was canceled. Please try again later.",
        "pt": "Não consegui iniciar o pagamento agora, então a operação de Tarô foi cancelada. Tente novamente mais tarde.",
        "es": "No pude iniciar el pago ahora, así que la operación de Tarot fue cancelada. Inténtalo de nuevo más tarde.",
    },
    "payment_flow_lost": {
        "en": "Your payment was confirmed, but the pending Tarot question could not be recovered. Please contact support with your payment receipt.",
        "pt": "Seu pagamento foi confirmado, mas não foi possível recuperar a pergunta pendente do Tarô. Entre em contato com o suporte com o comprovante de pagamento.",
        "es": "Tu pago fue confirmado, pero no se pudo recuperar la pregunta pendiente del Tarot. Contacta al soporte con tu comprobante de pago.",
    },
    "shuffling": {
        "en": "🃏 Shuffling the deck...",
        "pt": "🃏 Embaralhando o baralho...",
        "es": "🃏 Barajando las cartas...",
    },
    "fallen_intro": {
        "en": "A few cards slipped out of the deck on their own — almost as if they had chosen themselves.",
        "pt": "Algumas cartas escaparam sozinhas do baralho — quase como se tivessem se escolhido.",
        "es": "Algunas cartas se deslizaron solas fuera del mazo — casi como si se hubieran elegido a sí mismas.",
    },
    "fallen_choice": {
        "en": "Choose one of the cards that fell from the deck. Reply with {options}.",
        "pt": "Escolha uma das cartas que caíram do baralho. Responda com {options}.",
        "es": "Elige una de las cartas que cayeron del mazo. Responde con {options}.",
    },
    "spread_unavailable": {
        "en": "The selected spread is no longer available.",
        "pt": "A tiragem selecionada não está mais disponível.",
        "es": "La tirada seleccionada ya no está disponible.",
    },
    "select_spread_failed": {
        "en": "I couldn't select the most appropriate spread right now. Please try again.",
        "pt": "Não consegui selecionar a tiragem mais adequada agora. Tente novamente.",
        "es": "No pude seleccionar la tirada más adecuada en este momento. Inténtalo de nuevo.",
    },
    "analysis_wait": {
        "en": "🔍 I'm analyzing the complete spread now. Please wait while I finish the full reading.\n\nSend CANCEL if you want to stop this reading.",
        "pt": "🔍 Estou analisando a tiragem completa agora. Aguarde enquanto termino a leitura.\n\nEnvie CANCELAR se quiser interromper esta leitura.",
        "es": "🔍 Estoy analizando la tirada completa ahora. Espera mientras termino la lectura.\n\nEnvía CANCELAR si quieres detener esta lectura.",
    },
    "already_analyzing": {
        "en": "Your cards have already been drawn and the reading is being analyzed.",
        "pt": "Suas cartas já foram tiradas e a leitura está sendo analisada.",
        "es": "Tus cartas ya fueron sacadas y la lectura está siendo analizada.",
    },
    "reading_caption": {
        "en": "*Reading #{id}* — your complete spread",
        "pt": "*Leitura #{id}* — sua tiragem completa",
        "es": "*Lectura #{id}* — tu tirada completa",
    },
    "overall_label": {"en": "Overall narrative", "pt": "Narrativa geral", "es": "Narrativa general"},
    "cards_label": {"en": "Card-by-card interpretation", "pt": "Interpretação carta a carta", "es": "Interpretación carta por carta"},
    "synthesis_label": {"en": "Final synthesis", "pt": "Síntese final", "es": "Síntesis final"},
    "upright": {"en": "Upright", "pt": "Normal", "es": "Derecha"},
    "reversed": {"en": "Reversed", "pt": "Invertida", "es": "Invertida"},
    "card_number": {"en": "Card {number}", "pt": "Carta {number}", "es": "Carta {number}"},
    "profile_menu": {
        "en": "Your profile can calculate and save your zodiac sign, Personal Arcana, Year Arcana, complete natal chart, and MBTI personality. Once those pieces are complete, the AI can also create one saved annual profile analysis.\n\n1 — Date of birth → zodiac sign + Personal Arcana + Year Arcana\n2 — Birth time/place → complete natal chart\n3 — Personality test → MBTI\n4 — Annual profile analysis → strengths, weaknesses, traits, opportunities and points of attention\n\nThe annual profile analysis can only be generated once. Send 1, 2, 3, or 4.",
        "pt": "Seu perfil permite calcular e salvar seu signo, Arcano Pessoal, Arcano do Ano, mapa astral completo e personalidade MBTI. Depois de completar essas informações, a IA também pode criar uma análise anual do seu perfil e salvá-la.\n\n1 — Data de nascimento → signo + Arcano Pessoal + Arcano do Ano\n2 — Horário/local de nascimento → mapa astral completo\n3 — Teste de personalidade → MBTI\n4 — Análise anual do perfil → qualidades, defeitos, características, oportunidades e pontos de atenção\n\nA análise anual do perfil só pode ser gerada uma vez. Envie 1, 2, 3 ou 4.",
        "es": "Tu perfil permite calcular y guardar tu signo, Arcano Personal, Arcano del Año, carta natal completa y personalidad MBTI. Después de completar esos datos, la IA también puede crear y guardar un análisis anual de tu perfil.\n\n1 — Fecha de nacimiento → signo + Arcano Personal + Arcano del Año\n2 — Hora/lugar de nacimiento → carta natal completa\n3 — Test de personalidad → MBTI\n4 — Análisis anual del perfil → cualidades, defectos, características, oportunidades y puntos de atención\n\nEl análisis anual del perfil solo puede generarse una vez. Envía 1, 2, 3 o 4.",
    },
    "birth_date_prompt": {
        "en": "What is your date of birth? Send it as DD/MM/YYYY. Example: 17/08/2002.",
        "pt": "Qual é a sua data de nascimento? Envie no formato DD/MM/AAAA. Exemplo: 17/08/2002.",
        "es": "¿Cuál es tu fecha de nacimiento? Envíala como DD/MM/AAAA. Ejemplo: 17/08/2002.",
    },
    "birth_time_prompt": {
        "en": "What is your birth time? Send it as HH:MM. Example: 14:35.",
        "pt": "Qual é o seu horário de nascimento? Envie no formato HH:MM. Exemplo: 14:35.",
        "es": "¿Cuál es tu hora de nacimiento? Envíala como HH:MM. Ejemplo: 14:35.",
    },
}


def t(language: str | None, key: str, **kwargs) -> str:
    lang = normalize_language(language)
    values = _MESSAGES[key]
    template = values.get(lang) or values["en"]
    return template.format(**kwargs)


def output_language_instruction(language: str | None) -> str:
    lang = normalize_language(language)
    if lang == "pt":
        return "LANGUAGE REQUIREMENT: Write the entire user-facing answer in Brazilian Portuguese. Do not switch to English or Spanish, except for proper names or technical labels that should remain unchanged."
    if lang == "es":
        return "LANGUAGE REQUIREMENT: Write the entire user-facing answer in Spanish. Do not switch to English or Portuguese, except for proper names or technical labels that should remain unchanged."
    return "LANGUAGE REQUIREMENT: Write the entire user-facing answer in English. Do not switch to Portuguese or Spanish, except for proper names or technical labels that should remain unchanged."
