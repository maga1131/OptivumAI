# Grupy klasowe

OptivumAI rozróżnia grupę zawsze razem z klasą, np. `3TC / 1/4`.
Ta sama klasa może posiadać wiele równoległych systemów podziału:

- 1/2, 2/2,
- 1/3, 2/3, 3/3,
- 1/4, 2/4, 3/4, 4/4.

## Reguły konfliktów

1. Lekcja całej klasy koliduje z każdą grupą tej klasy.
2. Dwie różne grupy tego samego podziału są rozłączne, np. 1/4 i 2/4.
3. Ta sama grupa zawsze koliduje sama ze sobą.
4. Grupy różnych podziałów, np. 1/3 i 2/4, są uznawane za potencjalnie nakładające się.

Punkt 4 jest celowo zachowawczy. W przyszłości można dodać składy uczniów i wtedy program będzie sprawdzał rzeczywiste nakładanie się grup.
