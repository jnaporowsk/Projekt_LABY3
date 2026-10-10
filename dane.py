"""Wczytanie danych NO2. Feature'y dostają gotowy obiekt Dane – nie trzeba tu nic zmieniać.

Najważniejsze dla feature'ów:
    dane.miasta   – pandas.DataFrame: wiersze = dni, kolumny = miasta, wartości NO2 [µmol/m²]
    dane.mapa()   – średnia mapa NO2 (numpy 2D) z wybranych dni, np. dane.mapa(dane.czas.month == 1)
    dane.no2      – pełna kostka numpy [dzień, wiersz, kolumna] (dla zaawansowanych)
NaN = brak pomiaru (chmury).
"""
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

import ustawienia as u


class Dane:
    def __init__(self, czas, lat, lon, no2, zrodlo):
        self.czas = pd.DatetimeIndex(czas)   # dni
        self.lat = np.asarray(lat)           # malejąco: północ na górze
        self.lon = np.asarray(lon)
        self.no2 = no2                       # [dzień, wiersz, kolumna]
        self.zrodlo = zrodlo
        self.miasta = pd.DataFrame({n: self._punkt(la, lo) for n, (la, lo) in u.MIASTA.items()},
                                   index=self.czas)
        self.miasta.index.name = "data"

    def _punkt(self, lat, lon, promien=1):
        r = int(np.abs(self.lat - lat).argmin())
        c = int(np.abs(self.lon - lon).argmin())
        okno = self.no2[:, max(r - promien, 0): r + promien + 1, max(c - promien, 0): c + promien + 1]
        return _nanmean(okno.reshape(len(self.czas), -1), axis=1)

    def mapa(self, ktore_dni=None):
        """Średnia mapa NO2. ktore_dni: np. dane.czas.month == 1 albo dane.czas.dayofweek >= 5."""
        kostka = self.no2 if ktore_dni is None else self.no2[np.asarray(ktore_dni)]
        return _nanmean(kostka, axis=0)

    def miesiecznie(self):
        """Średnie miesięczne dla każdego piksela: (etykiety 'RRRR-MM', numpy [miesiąc, wiersz, kolumna])."""
        okresy = self.czas.to_period("M")
        etykiety = sorted(set(okresy))
        kostka = np.stack([_nanmean(self.no2[np.asarray(okresy == o)], axis=0) for o in etykiety])
        return [str(o) for o in etykiety], kostka

    @property
    def granice(self):
        dy = abs(self.lat[0] - self.lat[1]) / 2
        dx = abs(self.lon[1] - self.lon[0]) / 2
        return [[float(self.lat.min() - dy), float(self.lon.min() - dx)],
                [float(self.lat.max() + dy), float(self.lon.max() + dx)]]


def _nanmean(a, axis=None):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanmean(a, axis=axis)


def wczytaj(plik):
    """Plik NetCDF z pobierz_dane.py -> Dane."""
    import xarray as xr

    ds = xr.open_dataset(plik)
    try:
        var = ds["NO2"]
        t = next(d for d in var.dims if d in ("t", "time"))
        y = next(d for d in var.dims if d in ("y", "lat", "latitude"))
        x = next(d for d in var.dims if d in ("x", "lon", "longitude"))
    except (KeyError, StopIteration):
        raise ValueError(f"Nieoczekiwana budowa pliku – wklej to prowadzącemu/na czat:\n{ds}")
    var = var.transpose(t, y, x).sortby(y, ascending=False).sortby(x)

    no2 = var.values.astype("float32")
    if "umol" not in str(var.attrs.get("units", "")).lower():
        no2 = no2 * 1e6                      # mol/m² -> µmol/m²
    no2[no2 <= 0] = np.nan
    czas = pd.to_datetime(var[t].values).normalize()
    return Dane(czas, var[y].values, var[x].values, no2, f"Sentinel-5P/TROPOMI ({Path(plik).name})")


def demo(seed=0, rok=2023, krok=0.05):
    """SZTUCZNE dane o realistycznym kształcie – do testowania feature'ów bez pobierania."""
    rng = np.random.default_rng(seed)
    o = u.OBSZAR
    lat = np.arange(o["north"] - krok / 2, o["south"], -krok)
    lon = np.arange(o["west"] + krok / 2, o["east"], krok)
    czas = pd.date_range(f"{rok}-01-01", f"{rok}-12-31", freq="D")
    LA, LO = np.meshgrid(lat, lon, indexing="ij")

    waga = {"Kraków": 90, "Tarnów": 35, "Nowy Sącz": 25, "Oświęcim": 30, "Chrzanów": 25, "Zakopane": 15}
    pole = np.full(LA.shape, 25.0)
    for nazwa, (la, lo) in u.MIASTA.items():
        s = 0.2 if nazwa == "Kraków" else 0.12
        pole += waga.get(nazwa, 20) * np.exp(-((LA - la) ** 2 + ((LO - lo) * 0.64) ** 2) / (2 * s ** 2))

    sezon = 1 + 0.45 * np.cos(2 * np.pi * (czas.dayofyear.values - 15) / 365)
    tydzien = np.select([czas.dayofweek.values == 6, czas.dayofweek.values == 5], [0.7, 0.85], 1.0)
    mnoznik = (sezon * tydzien * rng.lognormal(0, 0.25, len(czas)))[:, None, None]
    no2 = (pole[None] * mnoznik * rng.lognormal(0, 0.15, (len(czas),) + LA.shape)).astype("float32")
    no2[(rng.random((len(czas), 1, 1)) < 0.25) | (rng.random(no2.shape) < 0.25)] = np.nan
    return Dane(czas, lat, lon, no2, "DANE DEMONSTRACYJNE (sztuczne)")
