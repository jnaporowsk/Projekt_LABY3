import matplotlib.pyplot as plt

TYTUL = "Szereg czasowy stężenia NO2 w Krakowie"
SKROT = "Szereg czasowy"   # krótka nazwa w menu

def uruchom(dane):
    krakow = dane.miasta["Kraków"]
    srednia_30d = krakow.rolling(window=30, min_periods=1).mean()

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(krakow.index, krakow.values, label="Dzienny NO₂", color="#90caf9", alpha=0.6)
    ax.plot(srednia_30d.index, srednia_30d.values, label="Średnia krocząca (30 dni)", color="#0d47a1", linewidth=2)

    ax.set_ylabel("NO₂ [µmol/m²]")
    ax.set_xlabel("Data")
    ax.set_title("Przebieg dzienny NO₂ w Krakowie")
    ax.legend(loc="upper right")
    ax.grid(True, linestyle="--", alpha=0.5)

    fig.tight_layout()
    return fig