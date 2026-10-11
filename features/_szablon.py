"""SZABLON – skopiuj ten plik jako np. features/02_szereg_czasowy.py i zmień treść.

Numer na początku nazwy = kolejność na stronie. Pliki z "_" na początku są pomijane.
Sprawdzenie:  python uruchom.py --demo --tylko 02

Co masz w `dane`:
    dane.miasta         tabela pandas: wiersze = dni, kolumny = miasta (Kraków, Tarnów, ...)
    dane.miasta["Kraków"]   jedna kolumna = szereg czasowy dla miasta
    dane.mapa()         średnia mapa NO2; dane.mapa(dane.czas.month == 1) – tylko styczeń
    dane.czas           daty (dane.czas.month, dane.czas.dayofweek ...)

Co możesz zwrócić (pojedynczo albo w liście):
    wykres matplotlib, tekst, tabelę pandas,
    Mapa(siatka, dane)            – interaktywna mapa (from strona import Mapa)
    Plik("wynik.csv", tabela)     – plik do pobrania; Plik("anim.gif", bajty) – obrazek/animacja
    Html("<div>...</div>")        – własny HTML/JavaScript
"""
import matplotlib.pyplot as plt

TYTUL = "Przykład: NO₂ w Krakowie"
SKROT = "Przykład"   # krótka nazwa w menu (1–2 słowa)


def uruchom(dane):
    krakow = dane.miasta["Kraków"]

    fig, ax = plt.subplots(figsize=(9, 3))
    krakow.plot(ax=ax, marker=".", linestyle="none")
    ax.set_ylabel("NO₂ [µmol/m²]")

    return [fig, f"Średnie NO₂ w Krakowie: <b>{krakow.mean():.1f} µmol/m²</b>."]
