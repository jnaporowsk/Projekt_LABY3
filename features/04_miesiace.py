import matplotlib.pyplot as plt

TYTUL = "Miesiące - Średnie miesięczne NO₂"

def uruchom(dane):
    srednie_miesieczne = dane.miasta.groupby(dane.miasta.index.month).mean()
    fig, ax = plt.subplots(figsize=(10, 5))
    srednie_miesieczne.plot(ax=ax, marker='o')
    ax.set_xlabel("Miesiąc")
    ax.set_ylabel("NO₂ [µmol/m²]")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(['Sty', 'Lut', 'Mar', 'Kwi', 'Maj', 'Cze', 'Lip', 'Sie', 'Wrz', 'Paź', 'Lis', 'Gru'])
    ax.legend(title="Miasta", bbox_to_anchor=(1.05, 1), loc='upper left')
    fig.tight_layout()

    return [fig, "Wykres przedstawia średnie miesięczne stężenie NO₂ wyliczone dla poszczególnych miast na przestrzeni całego roku."]