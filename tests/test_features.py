"""Sprawdza, czy każdy feature działa na danych demo:  python -m unittest discover -s tests"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import dane as d                      # noqa: E402
import strona                         # noqa: E402
from uruchom import lista_feature, wczytaj_feature   # noqa: E402


class TestFeatures(unittest.TestCase):
    def test_kazdy_feature(self):
        dane = d.demo()
        wyniki = []
        for plik in lista_feature() + [ROOT / "features" / "_szablon.py"]:
            with self.subTest(feature=plik.name):
                modul = wczytaj_feature(plik)
                self.assertTrue(hasattr(modul, "TYTUL"), "brak TYTUL")
                wynik = modul.uruchom(dane)
                self.assertIsNotNone(wynik, "uruchom() nic nie zwraca – brakuje return?")
                wyniki.append((plik.stem, modul.TYTUL, wynik if isinstance(wynik, list) else [wynik]))
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(strona.zbuduj(wyniki, Path(tmp) / "site", dane.zrodlo).exists())


if __name__ == "__main__":
    unittest.main()
