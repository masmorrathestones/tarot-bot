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
        "🌐 *CHOOSE YOUR LANGUAGE*\n"
        "_Escolha seu idioma · Elige tu idioma_\n\n"
        "1️⃣  English\n"
        "2️⃣  Português\n"
        "3️⃣  Español\n\n"
        "💬 Reply with *1, 2 or 3*."
    )


_MESSAGES = {
    "ask_name": {
        "en": "✨ *Welcome to Holomancy!*\n\nBefore we begin, what would you like me to call you?\n\n💬 Send me your *name*.",
        "pt": "✨ *Boas-vindas ao Holomancy!*\n\nAntes de começarmos, como você gostaria que eu te chamasse?\n\n💬 Envie seu *nome*.",
        "es": "✨ *¡Bienvenido a Holomancy!*\n\nAntes de empezar, ¿cómo te gustaría que te llamara?\n\n💬 Envíame tu *nombre*.",
    },
    "ask_name_again": {
        "en": "Please tell me your name so I can finish setting up your profile.",
        "pt": "Por favor, me diga seu nome para eu concluir a configuração do seu perfil.",
        "es": "Por favor, dime tu nombre para que pueda terminar de configurar tu perfil.",
    },
    "welcome": {
        "en": "✨ *Welcome, {name}!*\n\n🔮 Here, Tarot symbols become _reflection, interpretation and narrative_.",
        "pt": "✨ *Bem-vindo, {name}!*\n\n🔮 Aqui, os símbolos do Tarô se transformam em _reflexão, interpretação e narrativa_.",
        "es": "✨ *¡Bienvenido, {name}!*\n\n🔮 Aquí, los símbolos del Tarot se transforman en _reflexión, interpretación y narrativa_.",
    },
    "main_menu": {
        "en": "🔮 *HOLOMANCY MENU*\n_What would you like to explore?_\n\n🃏 *TAROT* — personalized card reading\n🕯️ *PAST LIFE* — two six-card spreads · _US$2 / R$12_\n🌙 *PLAN* — Daily Tarot + weekly astrology\n🧿 *PROFILE* — natal chart, personality and personal arcana\n✨ *ABOUT* — discover our method\n🌐 *LANGUAGE* — change language\n❓ *HELP* — show this menu\n\n💬 Send the *bold command* to continue.",
        "pt": "🔮 *MENU HOLOMANCY*\n_O que você deseja explorar?_\n\n🃏 *TAROT* — leitura personalizada das cartas\n🕯️ *VIDAS PASSADAS* — duas tiragens de 6 cartas · _US$ 2 / R$ 12_\n🌙 *PLANO* — Tarô diário + astrologia semanal\n🧿 *PERFIL* — mapa astral, personalidade e arcanos\n✨ *SOBRE* — conheça nosso método\n🌐 *IDIOMA* — altere o idioma\n❓ *AJUDA* — veja este menu\n\n💬 Envie o *comando em destaque* para continuar.",
        "es": "🔮 *MENÚ HOLOMANCY*\n_¿Qué deseas explorar?_\n\n🃏 *TAROT* — lectura personalizada de las cartas\n🕯️ *VIDAS PASADAS* — dos tiradas de 6 cartas · _US$2 / R$12_\n🌙 *PLAN* — Tarot diario + astrología semanal\n🧿 *PERFIL* — carta natal, personalidad y arcanos\n✨ *ACERCA* — conoce nuestro método\n🌐 *IDIOMA* — cambia el idioma\n❓ *AYUDA* — muestra este menú\n\n💬 Envía el *comando destacado* para continuar.",
    },
    "about_project": {
        "en": "✨ *About the Holomancy Tarot project*\n\nHolomancy Tarot is an automated symbolic-reading project developed from extensive study of number theory, astrology, Kabbalah, Hermeticism, Tarot, cybernetics, and mathematical communication theory.\n\nThe automated answers are not deterministic. The system uses coordinated pseudo-random protocols whose parameters are linked to variables such as weather phenomena, astronomical and solar movements, and other contextual signals relevant to the symbolic method. AI is used to automate the response process, but the card-interpretation framework comes from rigorous human training and is recalibrated every day.\n\nThis means the system does not simply invent answers. The reading combines pseudo-randomness based on parameters considered relevant to astrology and Tarot, daily human analysis, and reference material prepared by astrologers and other specialist sources for the AI to use as interpretive grounding.\n\nThe idea behind the project came from an insight while studying cybernetics in Norbert Wiener and Claude Shannon's mathematical theory of communication: a Tarot deck can be understood as an information-propagation system. The huge number of possible combinations, together with the selected cards, their order, positions, context and relationships, creates a very large informational space. The reader acts as a control center that selects, organizes and interprets the information being propagated. In that sense, a reading can also be viewed as a way of propagating bits.\n\nComputers, at a very abstract level, also propagate, control and calibrate bits. The central insight of Holomancy is that computation can be used without stripping Tarot of its soul.\n\nFor that reason, the method is deliberately holistic. Horoscope data, natal-chart factors, personality traits, context, statistical inferences and the relationships among all these elements are analyzed *together*, rather than as isolated modules.\n\nA Tarot reader should never be reductionist. The first step toward understanding Tarot is to see reality as something greater than the sum of its parts.",
        "pt": "✨ *Sobre o projeto Holomancy Tarot*\n\nO Holomancy Tarot é um projeto de leitura simbólica automatizada desenvolvido a partir de muito estudo de teoria dos números, astrologia, Cabala, hermetismo, Tarô, cibernética e teoria matemática da comunicação.\n\nAs respostas automatizadas não são determinísticas. O sistema utiliza protocolos coordenados de pseudo-aleatoriedade cujos parâmetros são vinculados a variáveis como fenômenos climáticos, movimentos astronômicos e solares e outros sinais contextuais relevantes para o método simbólico. Uma IA é utilizada para automatizar o processo de respostas, mas a estrutura de interpretação das cartas resulta de treinamento humano extremamente rigoroso e é recalibrada todos os dias.\n\nIsso significa que o sistema não simplesmente inventa respostas. A leitura combina pseudo-aleatoriedade baseada em parâmetros considerados relevantes para astrologia e Tarô, análise humana diária e material de base produzido por astrólogos e outras fontes especializadas para servir de fundamento interpretativo à IA.\n\nA ideia do projeto nasceu de um insight durante o estudo da cibernética de Norbert Wiener e da teoria matemática da comunicação de Claude Shannon: um baralho de Tarô pode ser entendido como um sistema de propagação de informação. A enorme multiplicidade de combinações possíveis, somada às cartas selecionadas, sua ordem, posições, contexto e relações entre si, cria um espaço informacional gigantesco. O tarólogo atua como um centro de controle que seleciona, organiza e interpreta a informação propagada. Nesse sentido, uma tiragem também pode ser vista como uma forma de propagar bits.\n\nComputadores, em um nível muito abstrato, também não fazem outra coisa senão propagar, controlar e calibrar bits. O grande insight do Holomancy é que seria possível utilizar a computação sem retirar a alma do Tarô.\n\nPor isso, o método segue deliberadamente uma abordagem holística. Horóscopo, fatores do mapa astral, aspectos de personalidade, contexto, inferências estatísticas e as relações entre todas essas informações são analisados *em conjunto*, e não como módulos isolados.\n\nÉ sempre importante para um tarólogo não ser reducionista. O primeiro passo para compreender o Tarô é enxergar a realidade como algo maior que a soma de suas partes.",
        "es": "✨ *Acerca del proyecto Holomancy Tarot*\n\nHolomancy Tarot es un proyecto de lectura simbólica automatizada desarrollado a partir de un estudio profundo de teoría de números, astrología, Cábala, hermetismo, Tarot, cibernética y teoría matemática de la comunicación.\n\nLas respuestas automatizadas no son deterministas. El sistema utiliza protocolos coordinados de pseudoaleatoriedad cuyos parámetros están vinculados a variables como fenómenos climáticos, movimientos astronómicos y solares y otras señales contextuales relevantes para el método simbólico. Se utiliza IA para automatizar el proceso de respuesta, pero la estructura de interpretación de las cartas proviene de un entrenamiento humano extremadamente riguroso y se recalibra todos los días.\n\nEsto significa que el sistema no se limita a inventar respuestas. La lectura combina pseudoaleatoriedad basada en parámetros considerados relevantes para la astrología y el Tarot, análisis humano diario y material de base elaborado por astrólogos y otras fuentes especializadas para proporcionar fundamento interpretativo a la IA.\n\nLa idea del proyecto nació de una intuición surgida durante el estudio de la cibernética de Norbert Wiener y de la teoría matemática de la comunicación de Claude Shannon: una baraja de Tarot puede entenderse como un sistema de propagación de información. La enorme multiplicidad de combinaciones posibles, junto con las cartas seleccionadas, su orden, posiciones, contexto y relaciones, crea un espacio informacional gigantesco. El tarotista actúa como un centro de control que selecciona, organiza e interpreta la información propagada. En ese sentido, una tirada también puede verse como una forma de propagar bits.\n\nLos computadores, en un nivel muy abstracto, tampoco hacen otra cosa que propagar, controlar y calibrar bits. La gran intuición de Holomancy es que es posible utilizar la computación sin quitarle el alma al Tarot.\n\nPor eso, el método adopta deliberadamente un enfoque holístico. El horóscopo, los factores de la carta natal, los rasgos de personalidad, el contexto, las inferencias estadísticas y las relaciones entre toda esa información se analizan *en conjunto*, no como módulos aislados.\n\nPara un tarotista siempre es importante no ser reduccionista. El primer paso para comprender el Tarot es ver la realidad como algo mayor que la suma de sus partes.",
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
        "en": "{text}\n\n↩️ _Send *CANCEL* at any time to return to the menu._",
        "pt": "{text}\n\n↩️ _Envie *CANCELAR* a qualquer momento para voltar ao menu._",
        "es": "{text}\n\n↩️ _Envía *CANCELAR* en cualquier momento para volver al menú._",
    },
    "reading_started": {
        "en": "🔮 *Your Tarot reading has begun*\n\nWhat question would you like the cards to illuminate?\n\n💬 _Write it in your own words._",
        "pt": "🔮 *Sua leitura de Tarô começou*\n\nQual questão você deseja iluminar por meio das cartas?\n\n💬 _Escreva com suas próprias palavras._",
        "es": "🔮 *Tu lectura de Tarot ha comenzado*\n\n¿Qué cuestión deseas iluminar por medio de las cartas?\n\n💬 _Escríbela con tus propias palabras._",
    },
    "send_question": {
        "en": "Send the question you want to explore.",
        "pt": "Envie a pergunta que você quer explorar.",
        "es": "Envía la pregunta que quieres explorar.",
    },
    "context_prompt": {
        "en": "📝 *Would you like to add some context?*\n\nShare anything that may help the reading, or send *SKIP* to continue with the question alone.",
        "pt": "📝 *Deseja acrescentar algum contexto?*\n\nConte o que pode ajudar na leitura ou envie *PULAR* para continuar somente com a pergunta.",
        "es": "📝 *¿Deseas añadir algún contexto?*\n\nCuenta lo que pueda ayudar en la lectura o envía *OMITIR* para continuar solo con la pregunta.",
    },
    "payment_required": {
        "en": "💳 *CONFIRM YOUR READING*\n\n💰 Price: *US$1.00*\n🌎 Pay in dollars or Brazilian reais:\n\n{url}\n\n🔒 _The cards are drawn only after confirmation. This link expires in about 30 minutes._",
        "pt": "💳 *CONFIRME SUA LEITURA*\n\n💰 Valor: *US$ 1,00*\n🌎 Pague em dólar ou em real:\n\n{url}\n\n🔒 _As cartas só serão tiradas após a confirmação. Este link expira em cerca de 30 minutos._",
        "es": "💳 *CONFIRMA TU LECTURA*\n\n💰 Precio: *US$1,00*\n🌎 Paga en dólares o reales brasileños:\n\n{url}\n\n🔒 _Las cartas solo se sacarán tras la confirmación. Este enlace vence en unos 30 minutos._",
    },
    "payment_pending": {
        "en": "⏳ *Payment pending*\n\nComplete the checkout to continue:\n{url}",
        "pt": "⏳ *Pagamento pendente*\n\nConclua o pagamento para continuar:\n{url}",
        "es": "⏳ *Pago pendiente*\n\nCompleta el pago para continuar:\n{url}",
    },
    "payment_confirmed": {
        "en": "✅ *Payment confirmed!*\nYour reading will continue now. 🔮",
        "pt": "✅ *Pagamento confirmado!*\nSua leitura continuará agora. 🔮",
        "es": "✅ *¡Pago confirmado!*\nTu lectura continuará ahora. 🔮",
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
        "en": "🃏 _Shuffling the deck and preparing your spread..._ ✨",
        "pt": "🃏 _Embaralhando o baralho e preparando sua tiragem..._ ✨",
        "es": "🃏 _Barajando las cartas y preparando tu tirada..._ ✨",
    },
    "fallen_intro": {
        "en": "✨ *Something unusual happened...*\nA few cards slipped out of the deck — almost as if they had chosen themselves.",
        "pt": "✨ *Algo incomum aconteceu...*\nAlgumas cartas escaparam do baralho — quase como se tivessem se escolhido.",
        "es": "✨ *Algo inusual ocurrió...*\nAlgunas cartas se deslizaron fuera del mazo — casi como si se hubieran elegido a sí mismas.",
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
        "en": "🔍 *Your spread is being analyzed*\n\nI'm connecting the cards, their positions and your context. This may take *up to 10 minutes*.\n\n✨ _I'll send the complete reading here when it's ready._\n↩️ Send *CANCEL* to stop.",
        "pt": "🔍 *Sua tiragem está sendo analisada*\n\nEstou conectando as cartas, suas posições e o seu contexto. Isso pode levar *até 10 minutos*.\n\n✨ _Enviarei a leitura completa por aqui assim que estiver pronta._\n↩️ Envie *CANCELAR* para interromper.",
        "es": "🔍 *Tu tirada está siendo analizada*\n\nEstoy conectando las cartas, sus posiciones y tu contexto. Esto puede tardar *hasta 10 minutos*.\n\n✨ _Enviaré la lectura completa por aquí cuando esté lista._\n↩️ Envía *CANCELAR* para detenerla.",
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
        "en": "🧿 *YOUR SYMBOLIC PROFILE*\n_Connect different layers of who you are._\n\n1️⃣ *Birth date*\n└ Zodiac sign · Personal Arcana · Year Arcana\n\n2️⃣ *Birth time and place*\n└ Complete natal chart\n\n3️⃣ *Personality test*\n└ MBTI-based traits\n\n4️⃣ *Annual profile analysis*\n└ Strengths · challenges · opportunities\n\n5️⃣ *Current location*\n└ Update when traveling or moving\n\n💬 Send a number from *1 to 5*.\n_The annual analysis can be generated only once._",
        "pt": "🧿 *SEU PERFIL SIMBÓLICO*\n_Conecte diferentes camadas de quem você é._\n\n1️⃣ *Data de nascimento*\n└ Signo · Arcano Pessoal · Arcano do Ano\n\n2️⃣ *Horário e local de nascimento*\n└ Mapa astral completo\n\n3️⃣ *Teste de personalidade*\n└ Traços baseados no MBTI\n\n4️⃣ *Análise anual do perfil*\n└ Qualidades · desafios · oportunidades\n\n5️⃣ *Local atual*\n└ Atualize quando viajar ou se mudar\n\n💬 Envie um número de *1 a 5*.\n_A análise anual pode ser gerada apenas uma vez._",
        "es": "🧿 *TU PERFIL SIMBÓLICO*\n_Conecta diferentes capas de quien eres._\n\n1️⃣ *Fecha de nacimiento*\n└ Signo · Arcano Personal · Arcano del Año\n\n2️⃣ *Hora y lugar de nacimiento*\n└ Carta natal completa\n\n3️⃣ *Test de personalidad*\n└ Rasgos basados en MBTI\n\n4️⃣ *Análisis anual del perfil*\n└ Cualidades · desafíos · oportunidades\n\n5️⃣ *Ubicación actual*\n└ Actualiza al viajar o mudarte\n\n💬 Envía un número del *1 al 5*.\n_El análisis anual solo puede generarse una vez._",
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
