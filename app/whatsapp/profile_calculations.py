from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import date


ARCANA = {
    1: ("The Magician", "A mission of initiative and creation. It asks for self-confidence to turn ideas into action; the challenge is usually focusing your energy instead of scattering it."),
    2: ("The High Priestess", "A mission connected to intuition and inner wisdom. It tends to ask you to trust your own voice before seeking external validation."),
    3: ("The Empress", "A mission of creating, nurturing, and generating abundance. The challenge is balancing care for others with care for yourself."),
    4: ("The Emperor", "A mission of structure and leadership. It often asks for firmness while avoiding rigidity."),
    5: ("The Hierophant", "A mission of learning and transmitting knowledge. It tends to value faith and ethics without becoming trapped by dogma."),
    6: ("The Lovers", "A mission of conscious choices and meaningful bonds. The central challenge is clarity in the face of indecision."),
    7: ("The Chariot", "A mission of determination and achievement. It asks for focus to move forward without overriding your own pace."),
    8: ("Justice", "A mission of balance and ethical decisions. It tends to ask you to reconcile reason and sensitivity."),
    9: ("The Hermit", "A mission of reflection and self-knowledge. The challenge is seeking inner silence without becoming excessively isolated."),
    10: ("Wheel of Fortune", "A mission of learning through cycles. It often asks for trust when circumstances change direction."),
    11: ("Strength", "A mission of courage and inner mastery. It tends to work through patience and gentle firmness."),
    12: ("The Hanged Man", "A mission of seeing life from different angles. The challenge is accepting pauses without falling into stagnation."),
    13: ("Death", "A mission of transformation and new beginnings. It asks for courage to close cycles that have already fulfilled their role."),
    14: ("Temperance", "A mission of balance and moderation. It often asks for harmony between extremes and patience with the timing of things."),
    15: ("The Devil", "A mission of dealing with desires and attachments. The challenge is recognizing what binds you and becoming freer with awareness."),
    16: ("The Tower", "A mission of building, breaking, and rebuilding. It tends to ask for resilience in the face of sudden change."),
    17: ("The Star", "A mission of hope and purpose. It often asks you to care for your own light and your aspirations."),
    18: ("The Moon", "A mission of entering deeply into emotion and intuition. The challenge is distinguishing reality from illusion."),
    19: ("The Sun", "A mission of radiating joy and vitality. It tends to ask for depth beyond appearances."),
    20: ("Judgement", "A mission of awakening and renewal. It often asks you to listen to a larger calling and resolve unfinished matters."),
    21: ("The World", "A mission of fulfillment and integration. It asks you to integrate what you have learned and complete major cycles."),
    22: ("The Fool", "A mission of freedom and new beginnings. The challenge is balancing boldness with responsibility."),
}

ARCANA_NAMES_PT = {
    1:"O Mago",2:"A Sacerdotisa",3:"A Imperatriz",4:"O Imperador",5:"O Hierofante",6:"Os Enamorados",7:"O Carro",8:"A Justiça",9:"O Eremita",10:"A Roda da Fortuna",11:"A Força",12:"O Enforcado",13:"A Morte",14:"A Temperança",15:"O Diabo",16:"A Torre",17:"A Estrela",18:"A Lua",19:"O Sol",20:"O Julgamento",21:"O Mundo",22:"O Louco",
}
ARCANA_NAMES_ES = {
    1:"El Mago",2:"La Sacerdotisa",3:"La Emperatriz",4:"El Emperador",5:"El Hierofante",6:"Los Enamorados",7:"El Carro",8:"La Justicia",9:"El Ermitaño",10:"La Rueda de la Fortuna",11:"La Fuerza",12:"El Colgado",13:"La Muerte",14:"La Templanza",15:"El Diablo",16:"La Torre",17:"La Estrella",18:"La Luna",19:"El Sol",20:"El Juicio",21:"El Mundo",22:"El Loco",
}

ARCANA_DESCRIPTIONS_PT = {
    1:"Uma missão de iniciativa e criação. Pede autoconfiança para transformar ideias em ação e foco para não dispersar sua energia.",
    2:"Uma missão ligada à intuição e à sabedoria interior. Pede confiança na própria voz antes de buscar validação externa.",
    3:"Uma missão de criar, nutrir e gerar abundância. O desafio é equilibrar o cuidado com os outros e consigo mesmo.",
    4:"Uma missão de estrutura e liderança. Pede firmeza sem cair na rigidez.",
    5:"Uma missão de aprender e transmitir conhecimento. Valoriza fé e ética sem aprisionamento pelo dogma.",
    6:"Uma missão de escolhas conscientes e vínculos significativos. O desafio central é ter clareza diante da indecisão.",
    7:"Uma missão de determinação e conquista. Pede foco para avançar sem atropelar seu próprio ritmo.",
    8:"Uma missão de equilíbrio e decisões éticas. Pede conciliar razão e sensibilidade.",
    9:"Uma missão de reflexão e autoconhecimento. O desafio é buscar silêncio interior sem se isolar em excesso.",
    10:"Uma missão de aprender através dos ciclos. Pede confiança quando as circunstâncias mudam de direção.",
    11:"Uma missão de coragem e domínio interior. Trabalha por meio de paciência e firmeza gentil.",
    12:"Uma missão de enxergar a vida por ângulos diferentes. O desafio é aceitar pausas sem cair na estagnação.",
    13:"Uma missão de transformação e recomeços. Pede coragem para encerrar ciclos que já cumpriram seu papel.",
    14:"Uma missão de equilíbrio e moderação. Pede harmonia entre extremos e paciência com o tempo das coisas.",
    15:"Uma missão de lidar com desejos e apegos. O desafio é reconhecer o que prende você e ganhar liberdade com consciência.",
    16:"Uma missão de construir, romper e reconstruir. Pede resiliência diante de mudanças repentinas.",
    17:"Uma missão de esperança e propósito. Pede cuidado com sua própria luz e suas aspirações.",
    18:"Uma missão de mergulho na emoção e na intuição. O desafio é distinguir realidade de ilusão.",
    19:"Uma missão de irradiar alegria e vitalidade. Pede profundidade para além das aparências.",
    20:"Uma missão de despertar e renovação. Pede escutar um chamado maior e resolver assuntos inacabados.",
    21:"Uma missão de realização e integração. Pede integrar o que foi aprendido e concluir grandes ciclos.",
    22:"Uma missão de liberdade e novos começos. O desafio é equilibrar ousadia e responsabilidade.",
}
ARCANA_DESCRIPTIONS_ES = {
    1:"Una misión de iniciativa y creación. Pide confianza para convertir ideas en acción y enfoque para no dispersar tu energía.",
    2:"Una misión ligada a la intuición y la sabiduría interior. Pide confiar en tu propia voz antes de buscar validación externa.",
    3:"Una misión de crear, nutrir y generar abundancia. El desafío es equilibrar el cuidado de los demás con el cuidado propio.",
    4:"Una misión de estructura y liderazgo. Pide firmeza sin caer en la rigidez.",
    5:"Una misión de aprender y transmitir conocimiento. Valora la fe y la ética sin quedar atrapado por el dogma.",
    6:"Una misión de decisiones conscientes y vínculos significativos. El desafío central es la claridad ante la indecisión.",
    7:"Una misión de determinación y logro. Pide enfoque para avanzar sin atropellar tu propio ritmo.",
    8:"Una misión de equilibrio y decisiones éticas. Pide reconciliar razón y sensibilidad.",
    9:"Una misión de reflexión y autoconocimiento. El desafío es buscar silencio interior sin aislarte demasiado.",
    10:"Una misión de aprender a través de los ciclos. Pide confianza cuando las circunstancias cambian de dirección.",
    11:"Una misión de valentía y dominio interior. Trabaja mediante paciencia y firmeza serena.",
    12:"Una misión de ver la vida desde distintos ángulos. El desafío es aceptar las pausas sin caer en el estancamiento.",
    13:"Una misión de transformación y nuevos comienzos. Pide valor para cerrar ciclos que ya cumplieron su función.",
    14:"Una misión de equilibrio y moderación. Pide armonía entre extremos y paciencia con el tiempo de las cosas.",
    15:"Una misión de relacionarte con deseos y apegos. El desafío es reconocer lo que te ata y ganar libertad con conciencia.",
    16:"Una misión de construir, romper y reconstruir. Pide resiliencia ante cambios repentinos.",
    17:"Una misión de esperanza y propósito. Pide cuidar tu propia luz y tus aspiraciones.",
    18:"Una misión de profundizar en la emoción y la intuición. El desafío es distinguir realidad de ilusión.",
    19:"Una misión de irradiar alegría y vitalidad. Pide profundidad más allá de las apariencias.",
    20:"Una misión de despertar y renovación. Pide escuchar un llamado mayor y resolver asuntos pendientes.",
    21:"Una misión de realización e integración. Pide integrar lo aprendido y completar grandes ciclos.",
    22:"Una misión de libertad y nuevos comienzos. El desafío es equilibrar audacia y responsabilidad.",
}

ZODIAC_DESCRIPTIONS = {
    "Aries":"Aries is associated with initiative, courage, and the impulse to begin. It tends to act directly and energetically, with the challenge of balancing speed and patience.",
    "Taurus":"Taurus is associated with stability, sensory experience, and perseverance. It values security and consistency, with the challenge of not turning firmness into resistance to change.",
    "Gemini":"Gemini is associated with curiosity, communication, and versatility. It seeks movement and exchange of ideas, with the challenge of maintaining focus and depth.",
    "Cancer":"Cancer is associated with sensitivity, protection, and emotional bonds. It values belonging and memory, with the challenge of caring without retreating behind defenses.",
    "Leo":"Leo is associated with expression, creativity, and vitality. It seeks to radiate presence and affection, with the challenge of balancing external recognition and inner confidence.",
    "Virgo":"Virgo is associated with analysis, organization, and refinement. It tends to notice details and serve in practical ways, with the challenge of softening self-criticism.",
    "Libra":"Libra is associated with harmony, relationships, and a sense of balance. It seeks to reconcile perspectives, with the challenge of not postponing choices merely to avoid conflict.",
    "Scorpio":"Scorpio is associated with intensity, transformation, and emotional depth. It tends to investigate what is hidden, with the challenge of dealing with control and letting go.",
    "Sagittarius":"Sagittarius is associated with expansion, the search for meaning, and freedom. It values experience and broad horizons, with the challenge of balancing enthusiasm and commitment.",
    "Capricorn":"Capricorn is associated with discipline, responsibility, and long-term construction. It seeks consistent results, with the challenge of not reducing life to duties alone.",
    "Aquarius":"Aquarius is associated with independence, originality, and collective vision. It tends to question established patterns, with the challenge of balancing rational distance and emotional connection.",
    "Pisces":"Pisces is associated with imagination, empathy, and symbolic sensitivity. It notices nuances and atmospheres, with the challenge of maintaining boundaries and clarity around emotions.",
}

ZODIAC_PT = {
    "Aries":("Áries","Áries se associa à iniciativa, coragem e impulso para começar. O desafio é equilibrar velocidade e paciência."),
    "Taurus":("Touro","Touro se associa à estabilidade, experiência sensorial e perseverança. O desafio é não transformar firmeza em resistência à mudança."),
    "Gemini":("Gêmeos","Gêmeos se associa à curiosidade, comunicação e versatilidade. O desafio é manter foco e profundidade."),
    "Cancer":("Câncer","Câncer se associa à sensibilidade, proteção e vínculos emocionais. O desafio é cuidar sem se esconder atrás de defesas."),
    "Leo":("Leão","Leão se associa à expressão, criatividade e vitalidade. O desafio é equilibrar reconhecimento externo e confiança interior."),
    "Virgo":("Virgem","Virgem se associa à análise, organização e refinamento. O desafio é suavizar a autocrítica."),
    "Libra":("Libra","Libra se associa à harmonia, relações e equilíbrio. O desafio é não adiar escolhas apenas para evitar conflitos."),
    "Scorpio":("Escorpião","Escorpião se associa à intensidade, transformação e profundidade emocional. O desafio é lidar com controle e desapego."),
    "Sagittarius":("Sagitário","Sagitário se associa à expansão, busca de sentido e liberdade. O desafio é equilibrar entusiasmo e compromisso."),
    "Capricorn":("Capricórnio","Capricórnio se associa à disciplina, responsabilidade e construção de longo prazo. O desafio é não reduzir a vida apenas a deveres."),
    "Aquarius":("Aquário","Aquário se associa à independência, originalidade e visão coletiva. O desafio é equilibrar distância racional e conexão emocional."),
    "Pisces":("Peixes","Peixes se associa à imaginação, empatia e sensibilidade simbólica. O desafio é manter limites e clareza emocional."),
}
ZODIAC_ES = {
    "Aries":("Aries","Aries se asocia con iniciativa, valentía e impulso para comenzar. El desafío es equilibrar velocidad y paciencia."),
    "Taurus":("Tauro","Tauro se asocia con estabilidad, experiencia sensorial y perseverancia. El desafío es no convertir firmeza en resistencia al cambio."),
    "Gemini":("Géminis","Géminis se asocia con curiosidad, comunicación y versatilidad. El desafío es mantener enfoque y profundidad."),
    "Cancer":("Cáncer","Cáncer se asocia con sensibilidad, protección y vínculos emocionales. El desafío es cuidar sin esconderse tras defensas."),
    "Leo":("Leo","Leo se asocia con expresión, creatividad y vitalidad. El desafío es equilibrar reconocimiento externo y confianza interior."),
    "Virgo":("Virgo","Virgo se asocia con análisis, organización y refinamiento. El desafío es suavizar la autocrítica."),
    "Libra":("Libra","Libra se asocia con armonía, relaciones y equilibrio. El desafío es no posponer decisiones solo para evitar conflictos."),
    "Scorpio":("Escorpio","Escorpio se asocia con intensidad, transformación y profundidad emocional. El desafío es manejar el control y soltar."),
    "Sagittarius":("Sagitario","Sagitario se asocia con expansión, búsqueda de sentido y libertad. El desafío es equilibrar entusiasmo y compromiso."),
    "Capricorn":("Capricornio","Capricornio se asocia con disciplina, responsabilidad y construcción a largo plazo. El desafío es no reducir la vida solo a obligaciones."),
    "Aquarius":("Acuario","Acuario se asocia con independencia, originalidad y visión colectiva. El desafío es equilibrar distancia racional y conexión emocional."),
    "Pisces":("Piscis","Piscis se asocia con imaginación, empatía y sensibilidad simbólica. El desafío es mantener límites y claridad emocional."),
}


@dataclass(frozen=True)
class PersonalArcanaResult:
    personal_number: int
    personal_arcana_name: str
    personal_arcana_description: str
    year_arcana_number: int
    year_arcana_name: str
    year_arcana_description: str
    reference_year: int


def reduce_to_arcana(value: int) -> int:
    while value > 22:
        value = sum(int(digit) for digit in str(value))
    return value


def name_value(name: str) -> int:
    normalized = unicodedata.normalize("NFKD", name)
    letters = [c.upper() for c in normalized if c.isascii() and c.isalpha()]
    return sum(ord(letter) - ord("A") + 1 for letter in letters)


def digit_sum(value: str) -> int:
    return sum(int(char) for char in value if char.isdigit())


def calculate_personal_arcana(name: str, birth_date: date, reference_year: int | None = None, language: str = "en") -> PersonalArcanaResult:
    year = reference_year or date.today().year
    reduced_name = reduce_to_arcana(name_value(name))
    birth_sum = digit_sum(birth_date.strftime("%d%m%Y"))
    personal_number = reduce_to_arcana(reduced_name + birth_sum)
    year_number = reduce_to_arcana(birth_sum + digit_sum(str(year)))

    if language == "pt":
        personal_name, personal_description = ARCANA_NAMES_PT[personal_number], ARCANA_DESCRIPTIONS_PT[personal_number]
        year_name, year_description = ARCANA_NAMES_PT[year_number], ARCANA_DESCRIPTIONS_PT[year_number]
    elif language == "es":
        personal_name, personal_description = ARCANA_NAMES_ES[personal_number], ARCANA_DESCRIPTIONS_ES[personal_number]
        year_name, year_description = ARCANA_NAMES_ES[year_number], ARCANA_DESCRIPTIONS_ES[year_number]
    else:
        personal_name, personal_description = ARCANA[personal_number]
        year_name, year_description = ARCANA[year_number]

    return PersonalArcanaResult(
        personal_number=personal_number,
        personal_arcana_name=personal_name,
        personal_arcana_description=personal_description,
        year_arcana_number=year_number,
        year_arcana_name=year_name,
        year_arcana_description=year_description,
        reference_year=year,
    )


def zodiac_for_birth_date(birth_date: date, language: str = "en") -> tuple[str, str]:
    month_day = (birth_date.month, birth_date.day)
    boundaries = [
        ((1, 20), "Aquarius"), ((2, 19), "Pisces"), ((3, 21), "Aries"),
        ((4, 20), "Taurus"), ((5, 21), "Gemini"), ((6, 21), "Cancer"),
        ((7, 23), "Leo"), ((8, 23), "Virgo"), ((9, 23), "Libra"),
        ((10, 23), "Scorpio"), ((11, 22), "Sagittarius"), ((12, 22), "Capricorn"),
    ]
    sign = "Capricorn"
    for boundary, candidate in boundaries:
        if month_day >= boundary:
            sign = candidate
    if language == "pt":
        return ZODIAC_PT[sign]
    if language == "es":
        return ZODIAC_ES[sign]
    return sign, ZODIAC_DESCRIPTIONS[sign]
