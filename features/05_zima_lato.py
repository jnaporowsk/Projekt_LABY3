import matplotlib.pyplot as plt
import pandas as pd

TYTUL = "Zima vs Lato"

def uruchom(dane):
    miasta = dane.miasta

    zima = miasta[miasta.index.month.isin([12, 1, 2])]
    lato = miasta[miasta.index.month.isin([6, 7, 8])]

    srednia_zima = zima.mean()
    srednia_lato = lato.mean()

    roznica = (
        (srednia_zima - srednia_lato)
        / srednia_lato.replace(0, float("nan"))
    ) * 100

    tabela = pd.DataFrame({
        "Zima [µmol/m²]": srednia_zima,
        "Lato [µmol/m²]": srednia_lato,
        "Różnica [%]": roznica
    })

    tabela.index.name = "Miasto"
    tabela = tabela.round(2)

    fig, ax = plt.subplots(figsize=(10, 5))

    tabela[["Zima [µmol/m²]", "Lato [µmol/m²]"]].plot(
        kind="bar",
        ax=ax,
        color=["#457B9D", "#E9C46A"]
    )

    ax.set_title("Średnie stężenie NO₂ – zima vs lato")
    ax.set_xlabel("Miasto")
    ax.set_ylabel("NO₂ [µmol/m²]")
    ax.legend(["Zima (XII–II)", "Lato (VI–VIII)"])
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()

    return [
        fig,
        "Porównanie średniego stężenia NO₂ w miesiącach "
        "zimowych (grudzień–luty) i letnich (czerwiec–sierpień). "
        "Różnica procentowa została obliczona względem lata.",
        tabela
    ]
