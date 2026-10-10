"""Pobiera dzienne NO2 z Sentinel-5P (Copernicus Data Space Ecosystem, openEO).

Wymaga darmowego konta: https://dataspace.copernicus.eu – logowanie otworzy się w przeglądarce,
hasło nie jest zapisywane w kodzie.

    python pobierz_dane.py                               # okres z ustawienia.py
    python pobierz_dane.py --od 2022-01-01 --do 2022-12-31

Wynik: data/raw/no2_<od>_<do>.nc
"""
import argparse
from pathlib import Path

import ustawienia as u

ROOT = Path(__file__).resolve().parent


def pobierz(od, do):
    import openeo

    folder = ROOT / "data" / "raw"
    folder.mkdir(parents=True, exist_ok=True)
    cel = folder / f"no2_{od}_{do}.nc"

    polaczenie = openeo.connect("openeo.dataspace.copernicus.eu").authenticate_oidc()
    kostka = polaczenie.load_collection("SENTINEL_5P_L2", temporal_extent=[od, do],
                                        spatial_extent=u.OBSZAR, bands=["NO2"])
    kostka = kostka.aggregate_temporal_period(period="day", reducer="mean")   # kilka przelotów -> 1 dzień
    kostka.execute_batch(outputfile=str(cel), out_format="netCDF", title=f"NO2 Malopolska {od}..{do}")
    print("Zapisano:", cel)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--od", default=u.OKRES[0])
    p.add_argument("--do", default=u.OKRES[1])
    a = p.parse_args()
    pobierz(a.od, a.do)
