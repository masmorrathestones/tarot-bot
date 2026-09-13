# Catálogo de símbolos de sonhos

Esta primeira etapa cria a base de conhecimento que será usada pelo futuro
serviço de interpretação de sonhos. Ela ainda não expõe um comando no WhatsApp
nem envia conteúdo para a IA.

## Modelo

Cada registro da tabela `dream_symbols` representa uma interpretação de um
símbolo por uma lente específica. Por isso, `Água` pode possuir uma linha
`MYSTICAL` e outra `PSYCHOANALYTIC`.

Os campos principais são:

- `canonical_key`: identidade estável e independente do idioma;
- `name_pt`, `name_en`, `name_es`: nome localizado do símbolo;
- `meaning_pt`, `meaning_en`, `meaning_es`: interpretação localizada;
- `interpretation_type`: `MYSTICAL` ou `PSYCHOANALYTIC`;
- `tradition`: escola mais específica, como `POPULAR_ESOTERIC` ou `JUNGIAN`;
- `source_book` e `source_reference`: procedência da interpretação;
- `context_note_pt`: ressalvas para o uso contextual;
- `active`: permite retirar uma interpretação de uso sem apagar seu histórico.

## Princípio de interpretação

As entradas místicas resumem as associações diretas de *O Livro dos Sonhos*.
As entradas junguianas são hipóteses de leitura, não traduções fixas. O futuro
motor deverá considerar o sonho completo, as emoções, as associações pessoais
e a situação atual do sonhador antes de selecionar um significado.

## Catálogo inicial

A migration `0023_dream_symbol_catalog` cria a tabela e inclui 26
interpretações trilíngues: 14 místicas e 12 junguianas. Novas entradas devem
manter uma referência verificável e trazer redação resumida própria, em vez de
copiar trechos extensos das obras.
