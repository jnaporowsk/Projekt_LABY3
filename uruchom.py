"""Uruchamia wszystkie feature'y z folderu features/ i buduje stronę outputs/site/index.html.

    python uruchom.py                  # prawdziwe dane z data/raw (najnowszy plik .nc), a jak brak -> demo
    python uruchom.py --demo           # sztuczne dane
    python uruchom.py --tylko 02       # tylko feature'y, których nazwa pliku zawiera "02"

Podgląd: python -m http.server 8000 --directory outputs/site   ->  http://127.0.0.1:8000/
"""
import argparse
import importlib.util
import sys
import traceback
from pathlib import Path

import dane as d
import strona

ROOT = Path(__file__).resolve().parent


def wczytaj_feature(plik: Path):
    spec = importlib.util.spec_from_file_location(plik.stem, plik)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def lista_feature():
    """Wszystkie pliki features/*.py oprócz zaczynających się od "_", w kolejności nazw."""
    return sorted(p for p in (ROOT / "features").glob("*.py") if not p.name.startswith("_"))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--demo", action="store_true", help="użyj sztucznych danych")
    p.add_argument("--dane", type=Path, help="konkretny plik .nc")
    p.add_argument("--tylko", help="fragment nazwy pliku feature'a")
    a = p.parse_args()

    pliki_nc = sorted((ROOT / "data" / "raw").glob("*.nc"))
    if a.dane:
        dane = d.wczytaj(a.dane)
    elif pliki_nc and not a.demo:
        dane = d.wczytaj(pliki_nc[-1])
    else:
        dane = d.demo()
    print(f"Dane: {dane.zrodlo} – {len(dane.czas)} dni, siatka {dane.no2.shape[1]}×{dane.no2.shape[2]}")

    wyniki, bledy = [], 0
    for plik in lista_feature():
        if a.tylko and a.tylko not in plik.stem:
            continue
        try:
            modul = wczytaj_feature(plik)
            tytul = getattr(modul, "TYTUL", plik.stem)
            skrot = getattr(modul, "SKROT", None)
            elementy = modul.uruchom(dane)
            if not isinstance(elementy, (list, tuple)):
                elementy = [elementy]
            print(f"  OK    {plik.name}")
        except Exception:
            bledy += 1
            tytul, skrot = plik.stem, None
            elementy = [f'<span class="blad">{traceback.format_exc()}</span>']
            print(f"  BŁĄD  {plik.name}\n{traceback.format_exc()}")
        wyniki.append((plik.stem, tytul, elementy, skrot))

    cel = strona.zbuduj(wyniki, ROOT / "outputs" / "site", dane.zrodlo, dane)
    print(f"Strona: {cel}")
    sys.exit(1 if bledy else 0)


if __name__ == "__main__":
    main()
