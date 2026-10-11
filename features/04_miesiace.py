import matplotlib.pyplot as plt
from strona import Plik

TYTUL = "Miesiące - Średnie miesięczne NO₂"
SKROT = "Miesiące"   # krótka nazwa w menu

def uruchom(dane):
    srednie_miesieczne = dane.miasta.groupby(dane.miasta.index.month).mean()
    fig, ax = plt.subplots(figsize=(10, 5))
    srednie_miesieczne.plot(ax=ax, marker='o')
    ax.set_title("Roczny przebieg stężenia NO₂ w miastach", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Miesiąc")
    ax.set_ylabel("NO₂ [µmol/m²]")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(['Sty', 'Lut', 'Mar', 'Kwi', 'Maj', 'Cze', 'Lip', 'Sie', 'Wrz', 'Paź', 'Lis', 'Gru'])
    ax.legend(title="Miasta", bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.6)
    fig.tight_layout()
    srednia_ogolna = srednie_miesieczne.mean(axis=1)
    najgorszy_miesiac = srednia_ogolna.idxmax()
    najlepszy_miesiac = srednia_ogolna.idxmin()
    max_val = srednia_ogolna.max()
    min_val = srednia_ogolna.min()
    roznica_proc = ((max_val - min_val) / min_val) * 100
    mianownik = {1:'styczeń', 2:'luty', 3:'marzec', 4:'kwiecień', 5:'maj', 6:'czerwiec', 
                 7:'lipiec', 8:'sierpień', 9:'wrzesień', 10:'październik', 11:'listopad', 12:'grudzień'}
    miejscownik = {1:'styczniu', 2:'lutym', 3:'marcu', 4:'kwietniu', 5:'maju', 6:'czerwcu', 
                   7:'lipcu', 8:'sierpniu', 9:'wrześniu', 10:'październiku', 11:'listopadzie', 12:'grudniu'}
    tekst = (f"Wykres przedstawia średnie miesięczne stężenie NO₂ w badanych miastach. "
             f"Analizując cały region, najczystszym miesiącem był <b>{mianownik[najlepszy_miesiac]}</b>, "
             f"natomiast największe zanieczyszczenie odnotowano w <b>{miejscownik[najgorszy_miesiac]}</b>. "
             f"Zanieczyszczenie w tym miesiącu było średnio o <b>{roznica_proc:.0f}% wyższe</b> niż w najczystszym.")
             
    tabela = srednie_miesieczne.copy()
    tabela.index = ['Styczeń', 'Luty', 'Marzec', 'Kwiecień', 'Maj', 'Czerwiec', 
                    'Lipiec', 'Sierpień', 'Wrzesień', 'Październik', 'Listopad', 'Grudzień']
    tabela.index.name = "Miesiąc"
             
    return [
        tekst,
        fig,
        "Poniżej znajduje się tabela z dokładnymi wartościami. Tabela do pobrania:",
        Plik("srednie_miesieczne_miasta.csv", tabela),
        tabela
    ]