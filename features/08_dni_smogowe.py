import matplotlib.pyplot as plt

TYTUL = "Top 10 dni z najwyższym stężeniem NO₂ w Krakowie"


def uruchom(dane):
    krakow = dane.miasta["Kraków"]

    top10 = krakow.nlargest(10)

    fig, ax = plt.subplots(figsize=(9, 4))
    top10.sort_values().plot(kind="barh", ax=ax, color="firebrick")
    ax.set_xlabel("NO₂ [µmol/m²]")
    ax.set_title("10 dni z najwyższym zanieczyszczeniem w Krakowie")

    return [
        fig,
        f"<b>Zestawienie top 10 dni smogowych:</b><br>{top10.to_frame(name='NO2').to_html(classes='table table-striped', border=0)}"
    ]
