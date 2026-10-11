"""Rdzeń projektu: interaktywna mapa NO2 – kliknij w dowolne miejsce, żeby zobaczyć przebieg w roku."""
from strona import Mapa

TYTUL = "Mapa NO₂ – kliknij, żeby zobaczyć przebieg w czasie"
SKROT = "Mapa"   # krótka nazwa w menu


def uruchom(dane):
    ranking = dane.miasta.mean().sort_values(ascending=False).rename("Średnie NO₂ [µmol/m²]")
    return [
        "Kliknij w dowolny punkt mapy: pojawi się wykres średnich miesięcznych NO₂ w tym miejscu "
        "na tle średniej całego regionu.",
        Mapa(dane.mapa(), dane),
        f"Średnia z {len(dane.czas)} dni ({dane.czas[0]:%d.%m.%Y}–{dane.czas[-1]:%d.%m.%Y}). "
        f"Najwyższe NO₂: <b>{ranking.index[0]}</b>, najniższe: <b>{ranking.index[-1]}</b>.",
        ranking,
    ]
