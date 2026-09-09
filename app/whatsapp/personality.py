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
        "After a tiring week, what tends to recharge your energy more?",
        "Being with people, talking, and doing something outside the house.",
        "Having time alone, in silence, or doing something more private.",
        "E", "I",
    ),
    MBTIQuestion(
        "When learning something new, what usually captures your attention more?",
        "Concrete examples, facts, and how it works in practice.",
        "General ideas, connections, possibilities, and what it might mean.",
        "S", "N",
    ),
    MBTIQuestion(
        "When you need to make a difficult decision, what usually weighs more?",
        "Consistency, objective criteria, and logical consequences.",
        "Personal values and how the decision will affect the people involved.",
        "T", "F",
    ),
    MBTIQuestion(
        "How do you feel most comfortable organizing a trip?",
        "With an itinerary, schedules, and most decisions made in advance.",
        "With freedom to decide many things on the spot and change plans.",
        "J", "P",
    ),
    MBTIQuestion(
        "In a group where you know few people, what feels more natural?",
        "Starting conversations and getting to know people while interacting.",
        "Observing first and joining conversations once you feel comfortable.",
        "E", "I",
    ),
    MBTIQuestion(
        "When someone tells a story, what do you tend to remember better?",
        "Details, specific events, and the sequence of what happened.",
        "The main idea, patterns, and interpretations of what happened.",
        "S", "N",
    ),
    MBTIQuestion(
        "During a disagreement between friends, which response feels more natural?",
        "Separating the arguments and trying to determine what makes the most sense.",
        "Understanding how each person feels and trying to preserve the relationship.",
        "T", "F",
    ),
    MBTIQuestion(
        "When you receive a large task with a distant deadline, you tend to prefer:",
        "Breaking it into stages and progressing in a relatively planned way.",
        "Keeping options open and concentrating effort as the situation develops.",
        "J", "P",
    ),
    MBTIQuestion(
        "When you have an idea that excites you, what is your first tendency?",
        "Sharing it and developing it by talking with someone.",
        "Thinking about it extensively on your own before showing it to others.",
        "E", "I",
    ),
    MBTIQuestion(
        "Which description best matches the way you solve problems?",
        "Starting from what is already known and reliable, then adapting from there.",
        "Trying new paths even when they have not been tested much yet.",
        "S", "N",
    ),
    MBTIQuestion(
        "If a rule produces an unfair result for someone, what do you tend to do first?",
        "Examine whether the rule is still rational and can be applied consistently.",
        "Consider the specific situation and the human impact of applying it.",
        "T", "F",
    ),
    MBTIQuestion(
        "Regarding day-to-day commitments, you generally prefer:",
        "Knowing in advance what will happen and having a defined structure.",
        "Having room to improvise and decide as the day unfolds.",
        "J", "P",
    ),
    MBTIQuestion(
        "After spending many hours socializing, you usually:",
        "Still feel energized or want to keep the interaction going.",
        "Feel a need to be alone to recover your energy.",
        "E", "I",
    ),
    MBTIQuestion(
        "When observing a situation, what do you trust more spontaneously?",
        "What you can directly perceive and the information available right now.",
        "Intuitions about patterns, trends, and things that might still happen.",
        "S", "N",
    ),
    MBTIQuestion(
        "When giving advice, what tends to come first?",
        "A direct analysis of the problem and what seems to work best.",
        "Trying to understand the person and what makes sense for them.",
        "T", "F",
    ),
    MBTIQuestion(
        "Which situation tends to bother you more?",
        "Important plans remaining undefined until the last minute.",
        "Having to follow a rigid plan when better alternatives appear.",
        "J", "P",
    ),
    MBTIQuestion(
        "When you need to organize your thoughts about a complex topic, you prefer:",
        "Talking, debating, or thinking out loud with someone.",
        "Reflecting internally and only then putting your ideas into words.",
        "E", "I",
    ),
    MBTIQuestion(
        "What usually sparks more curiosity in you?",
        "Understanding deeply how real and specific things work.",
        "Imagining scenarios, theories, and relationships between different ideas.",
        "S", "N",
    ),
    MBTIQuestion(
        "When someone disagrees with you, what type of argument tends to persuade you more?",
        "A consistent argument, even if it is emotionally uncomfortable.",
        "A perspective that considers values, context, and human needs.",
        "T", "F",
    ),
    MBTIQuestion(
        "After making an important decision, you generally feel more relieved when:",
        "The decision is settled and you can move on to the next step.",
        "There is still flexibility to reconsider if something new appears.",
        "J", "P",
    ),
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


def format_question(index: int) -> str:
    question = MBTI_QUESTIONS[index]
    return (
        f"Question {index + 1}/{len(MBTI_QUESTIONS)}\n\n"
        f"{question.text}\n\n"
        f"A — {question.option_a}\n\n"
        f"B — {question.option_b}\n\n"
        "Reply with A or B."
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
