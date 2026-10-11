import matplotlib.pyplot as plt

TYTUL = "Top 10 dni z najwyższym stężeniem NO₂ w Krakowie"
SKROT = "Najgorsze dni"   # krótka nazwa w menu


def uruchom(dane):
    krakow = dane.miasta["Kraków"]

    top10 = krakow.nlargest(10)

    fig, ax = plt.subplots(figsize=(9, 4))
    top10.sort_values().plot(kind="barh", ax=ax, color="firebrick")
    ax.set_xlabel("NO₂ [µmol/m²]")
    ax.set_title("10 dni z najwyższym zanieczyszczeniem w Krakowie")

    tabela = top10.to_frame(name="NO₂ [µmol/m²]")
    tabela.index.name = "Dzień"
    return [fig, "Zestawienie 10 dni z najwyższym NO₂:", tabela]
