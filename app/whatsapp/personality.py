from dataclasses import dataclass


@dataclass(frozen=True)
class MBTIQuestion:
    text: str
    option_a: str
    option_b: str
    letter_a: str
    letter_b: str


MBTI_QUESTIONS = [
    MBTIQuestion("After a tiring week, what tends to recharge your energy more?", "Being with people, talking, and doing something outside the house.", "Having time alone, in silence, or doing something more private.", "E", "I"),
    MBTIQuestion("When learning something new, what usually captures your attention more?", "Concrete examples, facts, and how it works in practice.", "General ideas, connections, possibilities, and what it might mean.", "S", "N"),
    MBTIQuestion("When you need to make a difficult decision, what usually weighs more?", "Consistency, objective criteria, and logical consequences.", "Personal values and how the decision will affect the people involved.", "T", "F"),
    MBTIQuestion("How do you feel most comfortable organizing a trip?", "With an itinerary, schedules, and most decisions made in advance.", "With freedom to decide many things on the spot and change plans.", "J", "P"),
    MBTIQuestion("In a group where you know few people, what feels more natural?", "Starting conversations and getting to know people while interacting.", "Observing first and joining conversations once you feel comfortable.", "E", "I"),
    MBTIQuestion("When someone tells a story, what do you tend to remember better?", "Details, specific events, and the sequence of what happened.", "The main idea, patterns, and interpretations of what happened.", "S", "N"),
    MBTIQuestion("During a disagreement between friends, which response feels more natural?", "Separating the arguments and trying to determine what makes the most sense.", "Understanding how each person feels and trying to preserve the relationship.", "T", "F"),
    MBTIQuestion("When you receive a large task with a distant deadline, you tend to prefer:", "Breaking it into stages and progressing in a relatively planned way.", "Keeping options open and concentrating effort as the situation develops.", "J", "P"),
    MBTIQuestion("When you have an idea that excites you, what is your first tendency?", "Sharing it and developing it by talking with someone.", "Thinking about it extensively on your own before showing it to others.", "E", "I"),
    MBTIQuestion("Which description best matches the way you solve problems?", "Starting from what is already known and reliable, then adapting from there.", "Trying new paths even when they have not been tested much yet.", "S", "N"),
    MBTIQuestion("If a rule produces an unfair result for someone, what do you tend to do first?", "Examine whether the rule is still rational and can be applied consistently.", "Consider the specific situation and the human impact of applying it.", "T", "F"),
    MBTIQuestion("Regarding day-to-day commitments, you generally prefer:", "Knowing in advance what will happen and having a defined structure.", "Having room to improvise and decide as the day unfolds.", "J", "P"),
    MBTIQuestion("After spending many hours socializing, you usually:", "Still feel energized or want to keep the interaction going.", "Feel a need to be alone to recover your energy.", "E", "I"),
    MBTIQuestion("When observing a situation, what do you trust more spontaneously?", "What you can directly perceive and the information available right now.", "Intuitions about patterns, trends, and things that might still happen.", "S", "N"),
    MBTIQuestion("When giving advice, what tends to come first?", "A direct analysis of the problem and what seems to work best.", "Trying to understand the person and what makes sense for them.", "T", "F"),
    MBTIQuestion("Which situation tends to bother you more?", "Important plans remaining undefined until the last minute.", "Having to follow a rigid plan when better alternatives appear.", "J", "P"),
    MBTIQuestion("When you need to organize your thoughts about a complex topic, you prefer:", "Talking, debating, or thinking out loud with someone.", "Reflecting internally and only then putting your ideas into words.", "E", "I"),
    MBTIQuestion("What usually sparks more curiosity in you?", "Understanding deeply how real and specific things work.", "Imagining scenarios, theories, and relationships between different ideas.", "S", "N"),
    MBTIQuestion("When someone disagrees with you, what type of argument tends to persuade you more?", "A consistent argument, even if it is emotionally uncomfortable.", "A perspective that considers values, context, and human needs.", "T", "F"),
    MBTIQuestion("After making an important decision, you generally feel more relieved when:", "The decision is settled and you can move on to the next step.", "There is still flexibility to reconsider if something new appears.", "J", "P"),
]


PT_QUESTIONS = [
    ("Depois de uma semana cansativa, o que tende a recarregar mais sua energia?", "Estar com pessoas, conversar e fazer algo fora de casa.", "Ter um tempo sozinho, em silêncio ou fazendo algo mais reservado."),
    ("Ao aprender algo novo, o que costuma chamar mais sua atenção?", "Exemplos concretos, fatos e como aquilo funciona na prática.", "Ideias gerais, conexões, possibilidades e o que aquilo pode significar."),
    ("Quando precisa tomar uma decisão difícil, o que costuma pesar mais?", "Coerência, critérios objetivos e consequências lógicas.", "Valores pessoais e como a decisão afetará as pessoas envolvidas."),
    ("Como você se sente mais confortável organizando uma viagem?", "Com roteiro, horários e a maior parte das decisões tomadas antes.", "Com liberdade para decidir muitas coisas na hora e mudar os planos."),
    ("Em um grupo onde você conhece poucas pessoas, o que parece mais natural?", "Iniciar conversas e conhecer as pessoas enquanto interage.", "Observar primeiro e entrar nas conversas quando se sentir confortável."),
    ("Quando alguém conta uma história, o que você tende a lembrar melhor?", "Detalhes, acontecimentos específicos e a sequência do que ocorreu.", "A ideia principal, os padrões e as interpretações do que aconteceu."),
    ("Durante uma discordância entre amigos, qual reação parece mais natural?", "Separar os argumentos e tentar descobrir o que faz mais sentido.", "Entender como cada pessoa se sente e tentar preservar a relação."),
    ("Ao receber uma tarefa grande com prazo distante, você tende a preferir:", "Dividi-la em etapas e avançar de modo relativamente planejado.", "Manter opções abertas e concentrar o esforço conforme a situação evolui."),
    ("Quando você tem uma ideia que te empolga, qual é sua primeira tendência?", "Compartilhá-la e desenvolvê-la conversando com alguém.", "Pensar bastante sozinho antes de mostrá-la aos outros."),
    ("Qual descrição combina mais com sua forma de resolver problemas?", "Partir do que já é conhecido e confiável e adaptar a partir daí.", "Experimentar caminhos novos mesmo que ainda tenham sido pouco testados."),
    ("Se uma regra produz um resultado injusto para alguém, o que você tende a fazer primeiro?", "Examinar se a regra ainda é racional e pode ser aplicada de modo consistente.", "Considerar a situação específica e o impacto humano de aplicá-la."),
    ("Quanto aos compromissos do dia a dia, você geralmente prefere:", "Saber de antemão o que vai acontecer e ter uma estrutura definida.", "Ter espaço para improvisar e decidir conforme o dia acontece."),
    ("Depois de passar muitas horas socializando, você geralmente:", "Ainda se sente energizado ou quer continuar interagindo.", "Sente necessidade de ficar sozinho para recuperar a energia."),
    ("Ao observar uma situação, em que você confia mais espontaneamente?", "No que pode perceber diretamente e nas informações disponíveis agora.", "Em intuições sobre padrões, tendências e coisas que ainda podem acontecer."),
    ("Ao dar um conselho, o que tende a vir primeiro?", "Uma análise direta do problema e do que parece funcionar melhor.", "Tentar entender a pessoa e o que faz sentido para ela."),
    ("Qual situação tende a incomodar mais você?", "Planos importantes permanecerem indefinidos até a última hora.", "Ter de seguir um plano rígido quando surgem alternativas melhores."),
    ("Quando precisa organizar suas ideias sobre um tema complexo, você prefere:", "Conversar, debater ou pensar em voz alta com alguém.", "Refletir internamente e só depois colocar as ideias em palavras."),
    ("O que costuma despertar mais sua curiosidade?", "Entender profundamente como coisas reais e específicas funcionam.", "Imaginar cenários, teorias e relações entre ideias diferentes."),
    ("Quando alguém discorda de você, que tipo de argumento tende a convencer mais?", "Um argumento coerente, mesmo que seja emocionalmente desconfortável.", "Uma perspectiva que considere valores, contexto e necessidades humanas."),
    ("Depois de tomar uma decisão importante, você costuma se sentir mais aliviado quando:", "A decisão está encerrada e você pode seguir para a próxima etapa.", "Ainda existe flexibilidade para reconsiderar se algo novo aparecer."),
]

ES_QUESTIONS = [
    ("Después de una semana agotadora, ¿qué suele recargar más tu energía?", "Estar con gente, conversar y hacer algo fuera de casa.", "Tener tiempo a solas, en silencio o haciendo algo más privado."),
    ("Al aprender algo nuevo, ¿qué suele captar más tu atención?", "Ejemplos concretos, hechos y cómo funciona en la práctica.", "Ideas generales, conexiones, posibilidades y lo que podría significar."),
    ("Cuando necesitas tomar una decisión difícil, ¿qué suele pesar más?", "La coherencia, los criterios objetivos y las consecuencias lógicas.", "Los valores personales y cómo afectará la decisión a las personas implicadas."),
    ("¿Cómo te resulta más cómodo organizar un viaje?", "Con itinerario, horarios y la mayoría de las decisiones tomadas de antemano.", "Con libertad para decidir muchas cosas sobre la marcha y cambiar los planes."),
    ("En un grupo donde conoces a poca gente, ¿qué se siente más natural?", "Iniciar conversaciones y conocer a la gente mientras interactúas.", "Observar primero y unirte a las conversaciones cuando te sientas cómodo."),
    ("Cuando alguien cuenta una historia, ¿qué tiendes a recordar mejor?", "Los detalles, los hechos concretos y la secuencia de lo ocurrido.", "La idea principal, los patrones y las interpretaciones de lo ocurrido."),
    ("Durante un desacuerdo entre amigos, ¿qué reacción te resulta más natural?", "Separar los argumentos e intentar determinar qué tiene más sentido.", "Comprender cómo se siente cada persona e intentar preservar la relación."),
    ("Cuando recibes una tarea grande con una fecha límite lejana, sueles preferir:", "Dividirla en etapas y avanzar de forma relativamente planificada.", "Mantener abiertas las opciones y concentrar el esfuerzo según evoluciona la situación."),
    ("Cuando tienes una idea que te entusiasma, ¿cuál es tu primera tendencia?", "Compartirla y desarrollarla hablando con alguien.", "Pensarla mucho por tu cuenta antes de mostrársela a otros."),
    ("¿Qué descripción encaja mejor con tu forma de resolver problemas?", "Partir de lo que ya se conoce y es fiable y adaptarse desde ahí.", "Probar caminos nuevos aunque todavía no hayan sido muy probados."),
    ("Si una regla produce un resultado injusto para alguien, ¿qué tiendes a hacer primero?", "Examinar si la regla sigue siendo racional y puede aplicarse de forma coherente.", "Considerar la situación concreta y el impacto humano de aplicarla."),
    ("Respecto a los compromisos cotidianos, generalmente prefieres:", "Saber de antemano qué ocurrirá y tener una estructura definida.", "Tener espacio para improvisar y decidir a medida que avanza el día."),
    ("Después de pasar muchas horas socializando, normalmente:", "Sigues sintiéndote con energía o quieres continuar la interacción.", "Sientes la necesidad de estar a solas para recuperar energía."),
    ("Al observar una situación, ¿en qué confías más espontáneamente?", "En lo que puedes percibir directamente y en la información disponible ahora.", "En intuiciones sobre patrones, tendencias y cosas que todavía podrían ocurrir."),
    ("Al dar un consejo, ¿qué suele venir primero?", "Un análisis directo del problema y de lo que parece funcionar mejor.", "Intentar comprender a la persona y lo que tiene sentido para ella."),
    ("¿Qué situación suele molestarte más?", "Que planes importantes sigan indefinidos hasta el último momento.", "Tener que seguir un plan rígido cuando aparecen alternativas mejores."),
    ("Cuando necesitas organizar tus ideas sobre un tema complejo, prefieres:", "Hablar, debatir o pensar en voz alta con alguien.", "Reflexionar internamente y solo después poner tus ideas en palabras."),
    ("¿Qué suele despertar más tu curiosidad?", "Comprender profundamente cómo funcionan cosas reales y concretas.", "Imaginar escenarios, teorías y relaciones entre ideas diferentes."),
    ("Cuando alguien discrepa contigo, ¿qué tipo de argumento suele convencerte más?", "Un argumento coherente, aunque resulte emocionalmente incómodo.", "Una perspectiva que tenga en cuenta valores, contexto y necesidades humanas."),
    ("Después de tomar una decisión importante, normalmente sientes más alivio cuando:", "La decisión queda cerrada y puedes pasar al siguiente paso.", "Todavía hay flexibilidad para reconsiderarla si aparece algo nuevo."),
]


MBTI_DESCRIPTIONS = {
    "ISTJ": "Reserved, practical, and organized. Often values responsibility, consistency, and reliable methods.",
    "ISFJ": "Attentive, caring, and steady. Often notices people's concrete needs and values commitment and harmony.",
    "INFJ": "Introspective, idealistic, and meaning-oriented. Often looks for deep patterns and coherence between values and actions.",
    "INTJ": "Strategic, independent, and analytical. Often thinks in systems, long-term possibilities, and ways to improve structures.",
    "ISTP": "Observant, pragmatic, and adaptable. Often enjoys understanding how things work and solving problems autonomously.",
    "ISFP": "Sensitive, flexible, and discreet. Often values authenticity, personal freedom, and concrete experiences with meaning.",
    "INFP": "Idealistic, imaginative, and value-driven. Often seeks authenticity and sees many possibilities in people and situations.",
    "INTP": "Curious, analytical, and conceptual. Often explores ideas, models, and inconsistencies with considerable intellectual independence.",
    "ESTP": "Energetic, direct, and adaptable. Often responds quickly to the environment and prefers practical experiences and immediate challenges.",
    "ESFP": "Spontaneous, sociable, and present-focused. Often brings energy to groups and values experiences and personal connections.",
    "ENFP": "Enthusiastic, creative, and possibility-oriented. Often connects ideas and people and values freedom and authenticity.",
    "ENTP": "Inventive, questioning, and flexible. Often enjoys exploring hypotheses, debating ideas, and finding less obvious alternatives.",
    "ESTJ": "Objective, organized, and execution-oriented. Often values clarity, efficiency, responsibility, and concrete decisions.",
    "ESFJ": "Sociable, cooperative, and caring. Often pays close attention to others' needs and values belonging and stability.",
    "ENFJ": "Communicative, empathetic, and people-oriented. Often notices social dynamics and mobilizes groups around shared values.",
    "ENTJ": "Strategic, assertive, and goal-oriented. Often organizes resources, makes decisions, and seeks efficiency in complex projects.",
}


def initial_scores() -> dict[str, int]:
    return {letter: 0 for letter in "EISNTFJP"}


def format_question(index: int, language: str = "en") -> str:
    question = MBTI_QUESTIONS[index]
    if language == "pt":
        text, option_a, option_b = PT_QUESTIONS[index]
        heading, reply = "Pergunta", "Responda com A ou B."
    elif language == "es":
        text, option_a, option_b = ES_QUESTIONS[index]
        heading, reply = "Pregunta", "Responde con A o B."
    else:
        text, option_a, option_b = question.text, question.option_a, question.option_b
        heading, reply = "Question", "Reply with A or B."
    return f"{heading} {index + 1}/{len(MBTI_QUESTIONS)}\n\n{text}\n\nA — {option_a}\n\nB — {option_b}\n\n{reply}"


def score_answer(index: int, answer: str, scores: dict[str, int]) -> dict[str, int]:
    normalized = answer.strip().lower()
    if normalized in {"a", "1"}:
        selected = MBTI_QUESTIONS[index].letter_a
    elif normalized in {"b", "2"}:
        selected = MBTI_QUESTIONS[index].letter_b
    else:
        raise ValueError("Answer must be A or B.")

    updated = initial_scores()
    updated.update({key: int(value) for key, value in scores.items() if key in updated})
    updated[selected] += 1
    return updated


def calculate_mbti(scores: dict[str, int]) -> str:
    return "".join(
        left if scores.get(left, 0) > scores.get(right, 0) else right
        for left, right in (("E", "I"), ("S", "N"), ("T", "F"), ("J", "P"))
    )


def mbti_description(mbti: str, language: str = "en") -> str:
    if language == "pt":
        return {
            "ISTJ": "Reservado, prático e organizado; valoriza responsabilidade, consistência e métodos confiáveis.",
            "ISFJ": "Atencioso, cuidadoso e estável; percebe necessidades concretas e valoriza compromisso e harmonia.",
            "INFJ": "Introspectivo, idealista e orientado por significado; busca padrões profundos e coerência entre valores e ações.",
            "INTJ": "Estratégico, independente e analítico; pensa em sistemas, possibilidades de longo prazo e melhoria de estruturas.",
            "ISTP": "Observador, pragmático e adaptável; gosta de entender como as coisas funcionam e resolver problemas com autonomia.",
            "ISFP": "Sensível, flexível e discreto; valoriza autenticidade, liberdade pessoal e experiências concretas com significado.",
            "INFP": "Idealista, imaginativo e guiado por valores; busca autenticidade e percebe muitas possibilidades em pessoas e situações.",
            "INTP": "Curioso, analítico e conceitual; explora ideias, modelos e inconsistências com independência intelectual.",
            "ESTP": "Energético, direto e adaptável; responde rapidamente ao ambiente e prefere experiências práticas e desafios imediatos.",
            "ESFP": "Espontâneo, sociável e focado no presente; leva energia aos grupos e valoriza experiências e conexões pessoais.",
            "ENFP": "Entusiasmado, criativo e orientado a possibilidades; conecta ideias e pessoas e valoriza liberdade e autenticidade.",
            "ENTP": "Inventivo, questionador e flexível; gosta de explorar hipóteses, debater ideias e encontrar alternativas menos óbvias.",
            "ESTJ": "Objetivo, organizado e voltado à execução; valoriza clareza, eficiência, responsabilidade e decisões concretas.",
            "ESFJ": "Sociável, cooperativo e cuidadoso; presta atenção às necessidades dos outros e valoriza pertencimento e estabilidade.",
            "ENFJ": "Comunicativo, empático e orientado a pessoas; percebe dinâmicas sociais e mobiliza grupos em torno de valores compartilhados.",
            "ENTJ": "Estratégico, assertivo e orientado a objetivos; organiza recursos, toma decisões e busca eficiência em projetos complexos.",
        }[mbti]
    if language == "es":
        return {
            "ISTJ": "Reservado, práctico y organizado; valora la responsabilidad, la consistencia y los métodos fiables.",
            "ISFJ": "Atento, cuidadoso y estable; percibe necesidades concretas y valora el compromiso y la armonía.",
            "INFJ": "Introspectivo, idealista y orientado al significado; busca patrones profundos y coherencia entre valores y acciones.",
            "INTJ": "Estratégico, independiente y analítico; piensa en sistemas, posibilidades a largo plazo y formas de mejorar estructuras.",
            "ISTP": "Observador, pragmático y adaptable; disfruta comprendiendo cómo funcionan las cosas y resolviendo problemas con autonomía.",
            "ISFP": "Sensible, flexible y discreto; valora la autenticidad, la libertad personal y las experiencias concretas con significado.",
            "INFP": "Idealista, imaginativo y guiado por valores; busca autenticidad y ve muchas posibilidades en personas y situaciones.",
            "INTP": "Curioso, analítico y conceptual; explora ideas, modelos e inconsistencias con gran independencia intelectual.",
            "ESTP": "Enérgico, directo y adaptable; responde rápidamente al entorno y prefiere experiencias prácticas y desafíos inmediatos.",
            "ESFP": "Espontáneo, sociable y centrado en el presente; aporta energía a los grupos y valora experiencias y conexiones personales.",
            "ENFP": "Entusiasta, creativo y orientado a posibilidades; conecta ideas y personas y valora la libertad y la autenticidad.",
            "ENTP": "Inventivo, cuestionador y flexible; disfruta explorando hipótesis, debatiendo ideas y encontrando alternativas menos obvias.",
            "ESTJ": "Objetivo, organizado y orientado a la ejecución; valora claridad, eficiencia, responsabilidad y decisiones concretas.",
            "ESFJ": "Sociable, cooperativo y atento; presta mucha atención a las necesidades de los demás y valora pertenencia y estabilidad.",
            "ENFJ": "Comunicativo, empático y orientado a las personas; percibe dinámicas sociales y moviliza grupos alrededor de valores compartidos.",
            "ENTJ": "Estratégico, asertivo y orientado a objetivos; organiza recursos, toma decisiones y busca eficiencia en proyectos complejos.",
        }[mbti]
    return MBTI_DESCRIPTIONS[mbti]
