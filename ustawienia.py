"""Ustawienia projektu – tu zmieniasz obszar, okres i listę miast."""

# Prostokąt obejmujący województwo małopolskie (stopnie, WGS84)
OBSZAR = {"west": 19.0, "south": 49.15, "east": 21.5, "north": 50.55}

# Okres pobierania danych
OKRES = ("2023-01-01", "2023-12-31")

# Miasta: nazwa -> (szerokość, długość geograficzna)
MIASTA = {
    "Kraków": (50.0614, 19.9366),
    "Tarnów": (50.0121, 20.9858),
    "Nowy Sącz": (49.6249, 20.6915),
    "Oświęcim": (50.0344, 19.2098),
    "Chrzanów": (50.1355, 19.4022),
    "Zakopane": (49.2992, 19.9496),
}

JEDNOSTKA = "µmol/m²"
