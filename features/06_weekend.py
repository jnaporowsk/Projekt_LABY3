import matplotlib.pyplot as plt
import pandas as pd

TYTUL = "Weekend vs dni robocze"


def uruchom(dane):
    miasta = dane.miasta

    dni_robocze = miasta[miasta.index.dayofweek < 5]
    weekend = miasta[miasta.index.dayofweek >= 5]

    srednia_robocze = dni_robocze.mean()
    srednia_weekend = weekend.mean()

    roznica = (
        (srednia_weekend - srednia_robocze)
        / srednia_robocze.replace(0, float("nan"))
    ) * 100

    tabela = pd.DataFrame({
        "Dni robocze [µmol/m²]": srednia_robocze,
        "Weekend [µmol/m²]": srednia_weekend,
        "Różnica [%]": roznica
    })

    tabela.index.name = "Miasto"
    tabela = tabela.round(2)

    fig1, ax1 = plt.subplots(figsize=(10, 5))

    tabela[[
        "Dni robocze [µmol/m²]",
        "Weekend [µmol/m²]"
    ]].plot(
        kind="bar",
        ax=ax1,
        color=["#457B9D", "#E9C46A"]
    )

    ax1.set_title("Średnie stężenie NO₂ – dni robocze vs weekend")
    ax1.set_xlabel("Miasto")
    ax1.set_ylabel("NO₂ [µmol/m²]")
    ax1.legend(["Dni robocze", "Weekend"])
    ax1.tick_params(axis="x", rotation=45)
    ax1.grid(axis="y", alpha=0.3)

    fig1.tight_layout()

    srednie_dni = miasta.groupby(miasta.index.dayofweek).mean()

    nazwy_dni = [
        "Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Nd"
    ]

    srednie_dni = srednie_dni.reindex(range(7))
    srednie_dni.index = nazwy_dni

    fig2, ax2 = plt.subplots(figsize=(10, 5))

    srednie_dni.plot(
        kind="line",
        ax=ax2,
        marker="o",
        linewidth=2
    )

    ax2.set_title("Średnie stężenie NO₂ w dniach tygodnia")
    ax2.set_xlabel("Dzień tygodnia")
    ax2.set_ylabel("NO₂ [µmol/m²]")
    ax2.grid(alpha=0.3)
    ax2.legend(title="Miasto")

    fig2.tight_layout()

    return [
        fig1,
        "Porównanie średniego stężenia NO₂ w dni robocze "
        "(poniedziałek–piątek) i weekendy (sobota–niedziela). "
        "Różnica procentowa została obliczona względem dni roboczych. "
        "Wartość ujemna oznacza niższe stężenie NO₂ w weekend.",
        tabela,
        fig2
    ]