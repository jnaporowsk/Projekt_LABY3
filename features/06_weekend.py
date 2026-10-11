import matplotlib.pyplot as plt
import pandas as pd

TYTUL = "Czy weekend wpływa na poziom NO₂?"
SKROT = "Weekend"   # krótka nazwa w menu


def uruchom(dane):
    df = dane.miasta.copy()

    robocze = df.loc[df.index.dayofweek < 5]
    weekendy = df.loc[df.index.dayofweek >= 5]

    sr_robocze = robocze.mean()
    sr_weekendy = weekendy.mean()

    zmiana = (sr_weekendy / sr_robocze.replace(0, float("nan")) - 1) * 100

    wyniki = pd.DataFrame({
        "Dni robocze": sr_robocze,
        "Weekend": sr_weekendy,
        "Zmiana (%)": zmiana
    }).round(2)

    wyniki.index.name = "Miasto"

    fig1, ax1 = plt.subplots(figsize=(9, 5))

    zmiana = zmiana.sort_values()
    kolory = [
        "#319795" if wartosc < 0 else "#D97757"
        for wartosc in zmiana
    ]

    ax1.barh(zmiana.index, zmiana.values, color=kolory)
    ax1.axvline(0, color="black", linewidth=0.8)

    ax1.set_title("Zmiana stężenia NO₂ w weekend")
    ax1.set_xlabel("Zmiana względem dni roboczych (%)")
    ax1.grid(axis="x", alpha=0.2)
    ax1.set_axisbelow(True)

    fig1.tight_layout()

    srednie = df.mean(axis=1)
    tydzien = srednie.groupby(srednie.index.dayofweek).mean()

    dni = ["Pn", "Wt", "Śr", "Cz", "Pt", "Sb", "Nd"]

    fig2, ax2 = plt.subplots(figsize=(9, 4))

    ax2.plot(
        dni,
        tydzien.reindex(range(7)).values,
        color="#263238",
        marker="o",
        markersize=7,
        linewidth=2.5
    )

    ax2.axvspan(4.5, 6.5, color="#319795", alpha=0.12)

    ax2.set_title("Jak zmienia się NO₂ w ciągu tygodnia?")
    ax2.set_ylabel("Średnie NO₂ [µmol/m²]")
    ax2.grid(axis="y", alpha=0.25)

    fig2.tight_layout()

    srednia_zmiana = zmiana.mean()

    if pd.isna(srednia_zmiana):
        opis = "Brak wystarczających danych do porównania."
    elif srednia_zmiana < 0:
        opis = (
            f"W weekendy stężenie NO₂ jest średnio o "
            f"{abs(srednia_zmiana):.1f}% niższe niż w dni robocze."
        )
    else:
        opis = (
            f"W weekendy stężenie NO₂ jest średnio o "
            f"{srednia_zmiana:.1f}% wyższe niż w dni robocze."
        )

    return [opis, fig1, fig2, wyniki]