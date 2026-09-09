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
        "en": "What would you like to do?\n\nTAROT — start a Tarot card reading\nPROFILE — add or update your personal profile\nLANGUAGE — change language\nHELP — show this menu again\n\nA Tarot reading only starts after you send TAROT.",
        "pt": "O que você gostaria de fazer?\n\nTAROT — iniciar uma leitura de Tarô\nPERFIL — adicionar ou atualizar seu perfil pessoal\nIDIOMA — mudar o idioma\nAJUDA — mostrar este menu novamente\n\nUma leitura de Tarô só começa depois que você enviar TAROT.",
        "es": "¿Qué te gustaría hacer?\n\nTAROT — iniciar una lectura de Tarot\nPERFIL — añadir o actualizar tu perfil personal\nIDIOMA — cambiar el idioma\nAYUDA — mostrar este menú de nuevo\n\nUna lectura de Tarot solo comienza después de que envíes TAROT.",
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
        "en": "You can add or update the following profile information:\n\n1 — Date of birth\n2 — Birth time and natal chart\n3 — Personality test (MBTI)\n\nSend 1, 2, or 3.",
        "pt": "Você pode adicionar ou atualizar as seguintes informações do perfil:\n\n1 — Data de nascimento\n2 — Horário de nascimento e mapa natal\n3 — Teste de personalidade (MBTI)\n\nEnvie 1, 2 ou 3.",
        "es": "Puedes añadir o actualizar la siguiente información de tu perfil:\n\n1 — Fecha de nacimiento\n2 — Hora de nacimiento y carta natal\n3 — Test de personalidad (MBTI)\n\nEnvía 1, 2 o 3.",
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
