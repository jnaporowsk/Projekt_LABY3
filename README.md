# Smog NO₂ nad Małopolską

Projekt 3 z przedmiotu *Przetwarzanie i analiza danych cyfrowych* (AGH).

Analiza dwutlenku azotu (NO₂) nad województwem małopolskim na podstawie zdjęć satelity
**Sentinel-5P** (instrument TROPOMI) z 2023 roku. Dane pobieramy automatycznie z Copernicus
Data Space Ecosystem, analizujemy w Pythonie, a wynik publikujemy jako stronę WWW.

NO₂ powstaje głównie przy spalaniu: w silnikach samochodów, elektrowniach i piecach domowych,
dlatego najwięcej go nad miastami, zimą i w dni robocze. Strona pokazuje to na mapach, wykresach i tabelach.

## Co jest na stronie

| Sekcja | Plik | Autor |
|---|---|---|
| Pasek dni – każdy dzień roku jako kolorowy pasek (nagłówek strony) | `strona.py` | jnaporowsk |
| Interaktywna mapa NO₂ – kliknięcie pokazuje przebieg w roku w danym miejscu | `features/01_mapa_no2.py` | jnaporowsk |
| Szereg czasowy NO₂ w Krakowie ze średnią kroczącą 30 dni | `features/03_szereg_czasowy.py` | SMYRDACK |
| Średnie miesięczne w miastach + tabela CSV do pobrania | `features/04_miesiace.py` | kajtekgaweda |
| Zima vs lato | `features/05_zima_lato.py` | nberest |
| Czy weekend wpływa na poziom NO₂? | `features/06_weekend.py` | madziapuzio |
| 10 dni z najwyższym NO₂ w Krakowie | `features/08_dni_smogowe.py` | Madzia1505 |
| Kalendarz smogu – tygodnie × dni tygodnia | `features/11_kalendarz.py` | SMYRDACK |
| Pogoda a smog – temperatura i wiatr z Open-Meteo | `features/16_pogoda.py` | SMYRDACK |

## Uruchomienie

Wymagany Python 3.11 lub nowszy.

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python uruchom.py
python -m http.server 8000 --directory outputs\site
```

Otwórz http://127.0.0.1:8000/. Serwer zatrzymasz przez Ctrl+C.

`uruchom.py` bierze najnowszy plik z `data/raw/`. Jeśli go nie ma, używa **danych demonstracyjnych** –
sztucznych, o realistycznym kształcie – co wystarcza do pracy nad kodem. Sekcja o pogodzie potrzebuje internetu.

### Prawdziwe dane

Potrzebne jest darmowe konto na https://dataspace.copernicus.eu (logowanie otwiera się w przeglądarce,
hasło nie trafia do kodu):

```bat
python pobierz_dane.py --od 2023-01-01 --do 2023-12-31
```

Plik zapisuje się w `data/raw/` (folder nie trafia do repozytorium). Obszar, okres i listę miast
zmienia się w `ustawienia.py`.

## Struktura

```
uruchom.py          uruchamia wszystkie feature'y i buduje outputs/site/index.html
pobierz_dane.py     pobiera NO₂ z Sentinel-5P (openEO, kolekcja SENTINEL_5P_L2)
ustawienia.py       obszar, okres, miasta
dane.py             wczytanie danych + dane demonstracyjne
strona.py           wygląd strony, zamiana wyników na HTML
features/           jeden plik = jedna sekcja strony
tests/              test sprawdzający wszystkie feature'y
vendor/             Leaflet (biblioteka map)
```

## Jak dodać nową sekcję

1. `copy features\_szablon.py features\NN_nazwa.py` – numer ustala kolejność na stronie.
2. Zmień `TYTUL` (nagłówek sekcji), `SKROT` (1–2 słowa w menu) i napisz funkcję `uruchom(dane)`. Najważniejsze dane:
   - `dane.miasta` – tabela pandas: wiersze = dni, kolumny = miasta,
   - `dane.mapa()` – średnia mapa NO₂, np. `dane.mapa(dane.czas.month == 1)` dla stycznia.
3. Zwróć to, co ma się pokazać: wykres matplotlib, tekst, tabelę pandas, `Mapa(...)`, `Plik(...)` albo `Html(...)`.
4. Sprawdź: `python uruchom.py --demo --tylko NN` oraz `python -m unittest discover -s tests`.

Każdy pracuje na swojej gałęzi i wysyła zmiany przez pull request do `main`.

## Publikacja na koncie AGH

Przy włączonym VPN AGH (`LOGIN` – login do konta Unix):

```bat
ssh LOGIN@student.agh.edu.pl "mkdir -p public_html/smog_no2"
scp -r outputs\site\* LOGIN@student.agh.edu.pl:public_html/smog_no2/
ssh LOGIN@student.agh.edu.pl "find public_html/smog_no2 -type d -exec chmod 755 {} + ; find public_html/smog_no2 -type f -exec chmod 644 {} + ; chmod o+x ~"
```

Adres: `https://student.agh.edu.pl/~LOGIN/smog_no2/` (dostępny z sieci AGH lub przez VPN).

## Ograniczenia

- Satelita mierzy całą kolumnę NO₂ nad ziemią (µmol/m²), a nie stężenie przy ziemi (µg/m³) jak stacje GIOŚ –
  te wartości można porównywać co do przebiegu, nie liczbowo.
- W dni pochmurne pomiaru nie ma; zimą braków jest więcej.
- Rozdzielczość ok. 5 km – widać miasta, ale nie pojedyncze ulice.

## Źródła

- Sentinel-5P/TROPOMI, Copernicus (ESA) – Copernicus Data Space Ecosystem, openEO.
- Dane pogodowe: Open-Meteo Historical Weather API.
- Mapy: Leaflet (licencja BSD-2), podkład © OpenStreetMap.
