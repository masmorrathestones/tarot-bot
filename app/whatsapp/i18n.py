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
        "en": "What would you like to do?\n\nTAROT — start a Tarot card reading\nPAST LIFE — two six-card Past Life Tarot spreads (US$2 / R$12)\nPROFILE — build your symbolic profile: zodiac sign, natal chart, MBTI personality, Personal Arcana, Year Arcana, and a saved annual profile analysis\nABOUT — learn about the Holomancy Tarot project and its method\nLANGUAGE — change language\nHELP — show this menu again\nPLAN — Daily Tarot + weekly astrology plan\n\nA Tarot reading only starts after you send TAROT or PAST LIFE.",
        "pt": "O que você gostaria de fazer?\n\nTAROT — iniciar uma leitura de Tarô\nVIDAS PASSADAS — duas tiragens de seis cartas (US$ 2 / R$ 12)\nPERFIL — montar seu perfil simbólico: signo, mapa astral, personalidade MBTI, Arcano Pessoal, Arcano do Ano e uma análise anual salva do seu perfil\nSOBRE — conhecer o projeto Holomancy Tarot e seu método\nIDIOMA — mudar o idioma\nAJUDA — mostrar este menu novamente\nPLANO — Tarô diário + astrologia semanal\n\nUma leitura só começa depois que você enviar TAROT ou VIDAS PASSADAS.",
        "es": "¿Qué te gustaría hacer?\n\nTAROT — iniciar una lectura de Tarot\nVIDAS PASADAS — dos tiradas de seis cartas (US$2 / R$12)\nPERFIL — crear tu perfil simbólico: signo, carta natal, personalidad MBTI, Arcano Personal, Arcano del Año y un análisis anual guardado de tu perfil\nACERCA — conocer el proyecto Holomancy Tarot y su método\nIDIOMA — cambiar idioma\nAYUDA — mostrar este menú\nPLAN — Tarot diario + astrología semanal\n\nUna lectura comienza después de enviar TAROT o VIDAS PASADAS.",
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
        "en": "🔍 I'm going to carefully analyze your complete spread now. This may take up to 10 minutes. I'll send the full reading here as soon as it's ready.\n\nSend CANCEL if you want to stop this reading.",
        "pt": "🔍 Agora vou analisar cuidadosamente a sua tiragem completa. Isso pode levar até 10 minutos. Enviarei a leitura completa por aqui assim que estiver pronta.\n\nEnvie CANCELAR se quiser interromper esta leitura.",
        "es": "🔍 Ahora voy a analizar cuidadosamente tu tirada completa. Esto puede tardar hasta 10 minutos. Te enviaré la lectura completa por aquí en cuanto esté lista.\n\nEnvía CANCELAR si quieres detener esta lectura.",
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
        "en": "Your profile can calculate and save your zodiac sign, Personal Arcana, Year Arcana, complete natal chart, and MBTI personality. Once those pieces are complete, the AI can also create one saved annual profile analysis.\n\n1 — Date of birth → zodiac sign + Personal Arcana + Year Arcana\n2 — Birth time/place → complete natal chart\n3 — Personality test → MBTI\n4 — Annual profile analysis → strengths, weaknesses, traits, opportunities and points of attention\n5 — Current location (update whenever you travel/move)\n\nThe annual profile analysis can only be generated once. Send 1, 2, 3, 4 or 5.",
        "pt": "Seu perfil permite calcular e salvar seu signo, Arcano Pessoal, Arcano do Ano, mapa astral completo e personalidade MBTI. Depois de completar essas informações, a IA também pode criar uma análise anual do seu perfil e salvá-la.\n\n1 — Data de nascimento → signo + Arcano Pessoal + Arcano do Ano\n2 — Horário/local de nascimento → mapa astral completo\n3 — Teste de personalidade → MBTI\n4 — Análise anual do perfil → qualidades, defeitos, características, oportunidades e pontos de atenção\n5 — Local atual (atualize sempre que viajar/mudar)\n\nA análise anual do perfil só pode ser gerada uma vez. Envie 1, 2, 3, 4 ou 5.",
        "es": "Tu perfil permite calcular y guardar tu signo, Arcano Personal, Arcano del Año, carta natal completa y personalidad MBTI. Después de completar esos datos, la IA también puede crear y guardar un análisis anual de tu perfil.\n\n1 — Fecha de nacimiento → signo + Arcano Personal + Arcano del Año\n2 — Hora/lugar de nacimiento → carta natal completa\n3 — Test de personalidad → MBTI\n4 — Análisis anual del perfil → cualidades, defectos, características, oportunidades y puntos de atención\n5 — Ubicación actual (actualízala cuando viajes/te mudes)\n\nEl análisis anual del perfil solo puede generarse una vez. Envía 1, 2, 3, 4 o 5.",
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
