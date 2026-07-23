# Changelog

## v0.8.0
- Dodano analizę konfliktów planu.
- Dodano ocenę planu na żywo.
- Przenoszenie i zamiana nie zapisują operacji tworzącej nowy konflikt.
- Dodano liczniki okienek nauczycieli, okienek klas i przepełnionych dni.

## 0.4.5 - sale @ i lekcje łączone

- dodano rozpoznawanie sali oznaczonej znakiem `@`,
- dodano odczyt wielu par klasa-grupa w jednej lekcji,
- lekcja łączona jest zapisywana jako jeden wpis powiązany z grupami różnych klas,
- moduł Lekcje pokazuje wszystkie klasy i grupy uczestniczące w zajęciach,
- dodano testy parsera dla obu przypadków.

## 0.4.4 - poprawne odczytywanie sal

- sala jest odczytywana z końca wpisu lekcji,
- obsługiwane są sale rozpoczynające się cyfrą, W, SALA lub CKZ,
- pełna nazwa sali jest usuwana z nazwy przedmiotu,
- dodano testy dla sal: 16A, W10, SALA_GIM1, SALA GIM2 i CKZ_AK.

## 0.4.3 - uniwersalne nazwy grup

- nazwa grupy jest odczytywana jako cały ciąg po znaku `-` do najbliższej spacji,
- obsługa nazw liczbowych, rzymskich i tekstowych, np. `1/2`, `II/1`, `G1`,
- znak `-` jest pomijany i nie trafia do nazwy grupy ani przedmiotu.

## 0.4.2 - poprawka importu grup

- Rozpoznawanie oznaczeń grup `-1/2`, `-2/3` itd. w dowolnym miejscu wpisu.
- Pomijanie znaku `-` w zapisanej nazwie grupy.
- Obsługa oznaczenia grupy bezpośrednio po nazwie klasy, np. `4T_C-3/3`.
- Poprawione rozpoznawanie nazw klas zawierających znak `_`.
- Dodane testy parsera grup.

# Changelog

## 0.4.0 - Sprint 1
- Dodano niezależny model domenowy planu lekcji.
- Dodano klasy Teacher, SchoolClass, Room i Lesson.
- Dodano klasę Timetable z indeksami, okienkami i obciążeniem dziennym.
- Dodano adapter SQLAlchemy do ładowania planu z istniejącej bazy.
- Dodano testy pytest i dokumentację architektury.

## v0.3.0

- baza SQLite i SQLAlchemy,
- modele nauczycieli, klas, sal i lekcji,
- parser eksportu HTML,
- zapis importu do bazy,
- tabela lekcji i statystyki w interfejsie.

## 0.4.0 Sprint 2
- Dodano wielostronicowy interfejs z lewą nawigacją.
- Dodano strony Projekt, Nauczyciele, Klasy, Sale i Lekcje.
- Dodano wyszukiwanie oraz automatyczne odświeżanie widoków po imporcie.

## Sprint 3 – obsługa grup klasowych
- dodano encję `ClassGroup`,
- rozpoznawanie podziałów 1/2, 1/3, 1/4 itd.,
- zapis grup w tabeli `class_groups`,
- powiązanie lekcji z grupami,
- obsługa wielu różnych podziałów w jednej klasie,
- zachowawcze wykrywanie konfliktów między różnymi podziałami,
- licznik grup na stronie Projekt.

## 0.5.1
- odświeżony wygląd komórek planu,
- pastelowe kolory lekcji zależne od przedmiotu,
- grupy wyświetlane poziomo z czytelnymi separatorami,
- dodane oznaczenia nauczyciela, sali i godziny,
- zwiększona wysokość komórek planu.

## v0.8.0
- panel „Dlaczego?” analizujący wybraną lekcję,
- wyszukiwanie do 5 najlepszych bezkonfliktowych przeniesień i zamian,
- porównanie oceny planu przed i po proponowanej zmianie,
- opis korzyści: redukcja konfliktów, okienek i przepełnionych dni,
- zastosowanie podpowiedzi jednym kliknięciem z potwierdzeniem.
