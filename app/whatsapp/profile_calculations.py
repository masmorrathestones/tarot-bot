from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import date


ARCANA = {
    1: ("O Mago", "Missão de iniciativa e criação. Pede autoconfiança para tirar ideias do papel; o desafio costuma ser focar a energia em vez de dispersá-la."),
    2: ("A Sacerdotisa", "Missão ligada à intuição e à sabedoria interior. Tende a pedir que você confie na própria voz antes de buscar validação externa."),
    3: ("A Imperatriz", "Missão de criar, nutrir e gerar abundância. O desafio é equilibrar o cuidado com os outros e o cuidado consigo."),
    4: ("O Imperador", "Missão de estrutura e liderança. Costuma pedir firmeza, com atenção para não cair na rigidez."),
    5: ("O Papa", "Missão de aprendizado e transmissão de conhecimento. Tende a valorizar a fé e a ética, sem se prender a dogmas."),
    6: ("Os Enamorados", "Missão de escolhas conscientes e vínculos afetivos. O desafio central é a clareza diante da indecisão."),
    7: ("O Carro", "Missão de determinação e conquista. Pede foco para avançar, com cuidado para não atropelar o próprio ritmo."),
    8: ("A Justiça", "Missão de equilíbrio e decisões éticas. Tende a pedir que você concilie razão e sensibilidade."),
    9: ("O Eremita", "Missão de reflexão e autoconhecimento. O desafio é buscar o silêncio interno sem se isolar demais."),
    10: ("A Roda da Fortuna", "Missão de aprender com os ciclos. Costuma pedir confiança diante das mudanças de rota."),
    11: ("A Força", "Missão de coragem e domínio interior. Tende a trabalhar a paciência e a firmeza gentil."),
    12: ("O Enforcado", "Missão de enxergar a vida por outros ângulos. O desafio é aceitar pausas sem cair na estagnação."),
    13: ("A Morte", "Missão de transformação e recomeços. Pede coragem para encerrar ciclos que já cumpriram seu papel."),
    14: ("A Temperança", "Missão de equilíbrio e moderação. Costuma pedir harmonia entre extremos e paciência com o tempo das coisas."),
    15: ("O Diabo", "Missão de lidar com desejos e apegos. O desafio é reconhecer o que aprisiona e se libertar com consciência."),
    16: ("A Torre", "Missão de construir, romper e reconstruir. Tende a pedir resiliência diante de mudanças bruscas."),
    17: ("A Estrela", "Missão de esperança e propósito. Costuma pedir cuidado com o próprio brilho e com os sonhos."),
    18: ("A Lua", "Missão de mergulhar nas emoções e na intuição. O desafio é distinguir a realidade das ilusões."),
    19: ("O Sol", "Missão de irradiar alegria e vitalidade. Tende a pedir profundidade, para além da superfície."),
    20: ("O Julgamento", "Missão de despertar e renovação. Costuma pedir que você ouça um chamado maior e resolva pendências."),
    21: ("O Mundo", "Missão de realização e plenitude. Pede que você integre aprendizados e conclua grandes ciclos."),
    22: ("O Louco", "Missão de liberdade e novos começos. O desafio é equilibrar ousadia com responsabilidade."),
}

ZODIAC_DESCRIPTIONS = {
    "Áries": "Áries é associado à iniciativa, coragem e impulso para começar. Costuma agir com franqueza e energia, com o desafio de equilibrar velocidade e paciência.",
    "Touro": "Touro é associado à estabilidade, sensorialidade e perseverança. Valoriza segurança e constância, com o desafio de não transformar firmeza em resistência à mudança.",
    "Gêmeos": "Gêmeos é associado à curiosidade, comunicação e versatilidade. Busca movimento e troca de ideias, com o desafio de manter foco e profundidade.",
    "Câncer": "Câncer é associado à sensibilidade, proteção e vínculo emocional. Valoriza pertencimento e memória, com o desafio de cuidar sem se fechar em defesas.",
    "Leão": "Leão é associado à expressão, criatividade e vitalidade. Busca irradiar presença e afeto, com o desafio de equilibrar reconhecimento externo e confiança interior.",
    "Virgem": "Virgem é associado à análise, organização e aperfeiçoamento. Tende a observar detalhes e servir de forma prática, com o desafio de suavizar a autocrítica.",
    "Libra": "Libra é associado à harmonia, relações e senso de equilíbrio. Busca conciliar perspectivas, com o desafio de não adiar escolhas para evitar conflito.",
    "Escorpião": "Escorpião é associado à intensidade, transformação e profundidade emocional. Tende a investigar o que está oculto, com o desafio de lidar com controle e desapego.",
    "Sagitário": "Sagitário é associado à expansão, busca de sentido e liberdade. Valoriza experiências e horizontes amplos, com o desafio de equilibrar entusiasmo e compromisso.",
    "Capricórnio": "Capricórnio é associado à disciplina, responsabilidade e construção de longo prazo. Busca resultados consistentes, com o desafio de não reduzir a vida apenas a deveres.",
    "Aquário": "Aquário é associado à independência, originalidade e visão coletiva. Tende a questionar padrões, com o desafio de equilibrar distanciamento racional e vínculo afetivo.",
    "Peixes": "Peixes é associado à imaginação, empatia e sensibilidade simbólica. Percebe nuances e atmosferas, com o desafio de manter limites e clareza diante das emoções.",
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


def calculate_personal_arcana(name: str, birth_date: date, reference_year: int | None = None) -> PersonalArcanaResult:
    year = reference_year or date.today().year
    reduced_name = reduce_to_arcana(name_value(name))
    birth_sum = digit_sum(birth_date.strftime("%d%m%Y"))
    personal_number = reduce_to_arcana(reduced_name + birth_sum)
    year_number = reduce_to_arcana(birth_sum + digit_sum(str(year)))

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


def zodiac_for_birth_date(birth_date: date) -> tuple[str, str]:
    month_day = (birth_date.month, birth_date.day)
    boundaries = [
        ((1, 20), "Aquário"), ((2, 19), "Peixes"), ((3, 21), "Áries"),
        ((4, 20), "Touro"), ((5, 21), "Gêmeos"), ((6, 21), "Câncer"),
        ((7, 23), "Leão"), ((8, 23), "Virgem"), ((9, 23), "Libra"),
        ((10, 23), "Escorpião"), ((11, 22), "Sagitário"), ((12, 22), "Capricórnio"),
    ]
    sign = "Capricórnio"
    for boundary, candidate in boundaries:
        if month_day >= boundary:
            sign = candidate
    return sign, ZODIAC_DESCRIPTIONS[sign]
