import matplotlib.pyplot as plt
import pandas as pd

TYTUL = "Kalendarz smogu w Krakowie (rozkład roczny)"

def uruchom(dane):
    seria = dane.miasta["Kraków"].copy()
    df = pd.DataFrame({"no2": seria})
    df["tydzien"] = df.index.isocalendar().week
    df["dzien_tyg"] = df.index.dayofweek  # 0=Poniedziałek, 6=Niedziela

    # Tworzymy macierz: wiersze = dni tygodnia, kolumny = tygodnie roku
    pivot = df.pivot_table(index="dzien_tyg", columns="tydzien", values="no2")

    fig, ax = plt.subplots(figsize=(12, 3.8))
    cax = ax.imshow(pivot, aspect="auto", cmap="YlOrRd", interpolation="nearest")

    dni_etykiety = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Nd"]
    ax.set_yticks(range(7))
    ax.set_yticklabels(dni_etykiety)
    ax.set_xlabel("Numer tygodnia w roku")
    ax.set_ylabel("Dzień tygodnia")
    ax.set_title("Stężenie NO₂ w Krakowie dzień po dniu w ujęciu tygodniowym")

    cbar = fig.colorbar(cax, ax=ax, orientation="horizontal", pad=0.25, shrink=0.5)
    cbar.set_label("Stężenie NO₂ [µg/m³]")

    fig.tight_layout()
    return fig