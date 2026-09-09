from dataclasses import dataclass


@dataclass(frozen=True)
class MBTIQuestion:
    text: str
    option_a: str
    option_b: str
    letter_a: str
    letter_b: str


MBTI_QUESTIONS = [
    MBTIQuestion(
        "Depois de uma semana cansativa, o que tende a recarregar mais sua energia?",
        "Estar com pessoas, conversar e fazer alguma coisa fora de casa.",
        "Ter um tempo sozinho, em silêncio ou fazendo algo mais reservado.",
        "E", "I",
    ),
    MBTIQuestion(
        "Ao aprender algo novo, o que costuma prender mais sua atenção?",
        "Exemplos concretos, fatos e como aquilo funciona na prática.",
        "Ideias gerais, conexões, possibilidades e o que aquilo pode significar.",
        "S", "N",
    ),
    MBTIQuestion(
        "Quando precisa tomar uma decisão difícil, o que normalmente pesa mais?",
        "Coerência, critérios objetivos e consequências lógicas.",
        "Valores pessoais e como a decisão afetará as pessoas envolvidas.",
        "T", "F",
    ),
    MBTIQuestion(
        "Como você se sente melhor organizando uma viagem?",
        "Com roteiro, horários e boa parte das decisões tomadas antes.",
        "Com liberdade para decidir muita coisa na hora e mudar os planos.",
        "J", "P",
    ),
    MBTIQuestion(
        "Em um grupo onde você conhece pouca gente, o que é mais natural?",
        "Começar conversas e ir conhecendo as pessoas enquanto interage.",
        "Observar primeiro e entrar nas conversas quando se sente à vontade.",
        "E", "I",
    ),
    MBTIQuestion(
        "Quando alguém conta uma história, o que você tende a guardar melhor?",
        "Detalhes, acontecimentos específicos e a sequência do que ocorreu.",
        "A ideia principal, padrões e interpretações sobre o que ocorreu.",
        "S", "N",
    ),
    MBTIQuestion(
        "Numa discussão entre amigos, qual atitude parece mais natural para você?",
        "Separar os argumentos e tentar descobrir o que faz mais sentido.",
        "Entender como cada pessoa se sente e buscar preservar a relação.",
        "T", "F",
    ),
    MBTIQuestion(
        "Quando recebe uma tarefa grande com prazo distante, você tende a preferir:",
        "Dividir em etapas e avançar de forma relativamente planejada.",
        "Manter opções abertas e concentrar o esforço conforme a situação evolui.",
        "J", "P",
    ),
    MBTIQuestion(
        "Quando você tem uma ideia que te anima, sua primeira tendência costuma ser:",
        "Compartilhar e desenvolver a ideia conversando com alguém.",
        "Pensar bastante sozinho antes de mostrar para outras pessoas.",
        "E", "I",
    ),
    MBTIQuestion(
        "Qual descrição combina mais com sua forma de resolver problemas?",
        "Partir do que já é conhecido e confiável e adaptar a partir daí.",
        "Experimentar caminhos novos, mesmo que ainda sejam pouco testados.",
        "S", "N",
    ),
    MBTIQuestion(
        "Se uma regra produz um resultado injusto para alguém, você tende primeiro a:",
        "Examinar se a regra ainda é racional e se pode ser aplicada consistentemente.",
        "Considerar a situação particular e o impacto humano daquela aplicação.",
        "T", "F",
    ),
    MBTIQuestion(
        "Sobre compromissos no dia a dia, você geralmente prefere:",
        "Saber com antecedência o que vai acontecer e ter uma estrutura definida.",
        "Ter espaço para improvisar e decidir conforme o dia se desenrola.",
        "J", "P",
    ),
    MBTIQuestion(
        "Após passar muitas horas socializando, você costuma:",
        "Continuar energizado ou sentir vontade de prolongar a interação.",
        "Sentir necessidade de ficar sozinho para recuperar energia.",
        "E", "I",
    ),
    MBTIQuestion(
        "Ao observar uma situação, você confia mais espontaneamente em:",
        "O que pode perceber diretamente e nas informações disponíveis agora.",
        "Intuições sobre padrões, tendências e coisas que ainda podem acontecer.",
        "S", "N",
    ),
    MBTIQuestion(
        "Ao dar um conselho, o que tende a vir primeiro?",
        "Uma análise direta do problema e do que parece funcionar melhor.",
        "A tentativa de compreender a pessoa e o que faz sentido para ela.",
        "T", "F",
    ),
    MBTIQuestion(
        "Qual situação costuma incomodar mais?",
        "Planos importantes ficarem indefinidos até a última hora.",
        "Ter que seguir um plano rígido quando surgem alternativas melhores.",
        "J", "P",
    ),
    MBTIQuestion(
        "Quando precisa organizar seus pensamentos sobre um assunto complexo, você prefere:",
        "Conversar, debater ou pensar em voz alta com alguém.",
        "Refletir internamente e só depois colocar as ideias para fora.",
        "E", "I",
    ),
    MBTIQuestion(
        "O que costuma despertar mais curiosidade em você?",
        "Entender profundamente como coisas reais e específicas funcionam.",
        "Imaginar cenários, teorias e relações entre ideias diferentes.",
        "S", "N",
    ),
    MBTIQuestion(
        "Quando alguém discorda de você, qual critério tende a convencer mais?",
        "Um argumento consistente, mesmo que seja desconfortável emocionalmente.",
        "Uma perspectiva que leve em conta valores, contexto e necessidades humanas.",
        "T", "F",
    ),
    MBTIQuestion(
        "Quando termina uma decisão importante, você geralmente sente mais alívio quando:",
        "A decisão está fechada e você pode seguir para a próxima etapa.",
        "Ainda existe flexibilidade para rever a escolha se aparecer algo novo.",
        "J", "P",
    ),
]


MBTI_DESCRIPTIONS = {
    "ISTJ": "Reservado, prático e organizado. Costuma valorizar responsabilidade, consistência e métodos confiáveis.",
    "ISFJ": "Atencioso, cuidadoso e estável. Tende a perceber necessidades concretas das pessoas e valorizar compromisso e harmonia.",
    "INFJ": "Introspectivo, idealista e orientado por significado. Costuma buscar padrões profundos e coerência entre valores e ações.",
    "INTJ": "Estratégico, independente e analítico. Tende a pensar em sistemas, possibilidades de longo prazo e formas de melhorar estruturas.",
    "ISTP": "Observador, pragmático e adaptável. Costuma gostar de entender como as coisas funcionam e resolver problemas com autonomia.",
    "ISFP": "Sensível, flexível e discreto. Tende a valorizar autenticidade, liberdade pessoal e experiências concretas que tenham significado.",
    "INFP": "Idealista, imaginativo e guiado por valores. Costuma buscar autenticidade e enxergar muitas possibilidades nas pessoas e situações.",
    "INTP": "Curioso, analítico e conceitual. Tende a explorar ideias, modelos e inconsistências com bastante independência intelectual.",
    "ESTP": "Energético, direto e adaptável. Costuma reagir rapidamente ao ambiente e preferir experiências práticas e desafios imediatos.",
    "ESFP": "Espontâneo, sociável e atento ao presente. Tende a trazer energia para os ambientes e valorizar experiências e conexões pessoais.",
    "ENFP": "Entusiasmado, criativo e orientado por possibilidades. Costuma conectar ideias e pessoas e valorizar liberdade e autenticidade.",
    "ENTP": "Inventivo, questionador e flexível. Tende a gostar de explorar hipóteses, debater ideias e encontrar alternativas pouco óbvias.",
    "ESTJ": "Objetivo, organizado e orientado à execução. Costuma valorizar clareza, eficiência, responsabilidade e decisões concretas.",
    "ESFJ": "Sociável, cooperativo e cuidadoso. Tende a prestar atenção às necessidades dos outros e valorizar pertencimento e estabilidade.",
    "ENFJ": "Comunicativo, empático e orientado por pessoas. Costuma perceber dinâmicas sociais e mobilizar grupos em torno de valores compartilhados.",
    "ENTJ": "Estratégico, assertivo e orientado a objetivos. Tende a organizar recursos, tomar decisões e buscar eficiência em projetos complexos.",
}


def initial_scores() -> dict[str, int]:
    return {letter: 0 for letter in "EISNTFJP"}


def format_question(index: int) -> str:
    question = MBTI_QUESTIONS[index]
    return (
        f"Pergunta {index + 1}/{len(MBTI_QUESTIONS)}\n\n"
        f"{question.text}\n\n"
        f"A — {question.option_a}\n\n"
        f"B — {question.option_b}\n\n"
        "Responda A ou B."
    )


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
    # There are five questions per axis, so ties are impossible after all 20.
    return "".join(
        left if scores.get(left, 0) > scores.get(right, 0) else right
        for left, right in (("E", "I"), ("S", "N"), ("T", "F"), ("J", "P"))
    )


def mbti_description(mbti: str) -> str:
    return MBTI_DESCRIPTIONS[mbti]
