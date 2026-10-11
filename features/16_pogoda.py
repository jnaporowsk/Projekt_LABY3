import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

TYTUL = "Wpływ pogody na smog – temperatura i wiatr vs NO2 w Krakowie"
SKROT = "Pogoda"   # krótka nazwa w menu

def uruchom(dane):
    krakow = dane.miasta["Kraków"].dropna()
    start_str = krakow.index.min().strftime("%Y-%m-%d")
    end_str = krakow.index.max().strftime("%Y-%m-%d")

    url = (
        f"https://archive-api.open-meteo.com/v1/archive"
        f"?latitude=50.06&longitude=19.94"
        f"&start_date={start_str}&end_date={end_str}"
        f"&daily=temperature_2m_mean,wind_speed_10m_max"
        f"&timezone=Europe%2FWarsaw"
    )

    try:
        odp = requests.get(url, timeout=6)
        odp.raise_for_status()
        pogoda = odp.json()["daily"]
        df_pogoda = pd.DataFrame({
            "data": pd.to_datetime(pogoda["time"]),
            "temperatura": pogoda["temperature_2m_mean"],
            "wiatr": pogoda["wind_speed_10m_max"],
        }).set_index("data")
        df = pd.DataFrame({"no2": krakow}).join(df_pogoda).dropna()
    except Exception as e:
        return (f"Nie udało się pobrać danych pogodowych z Open-Meteo ({type(e).__name__}). "
                "Ta sekcja potrzebuje internetu – uruchom stronę ponownie, gdy połączenie będzie działać.")

    r_temp = df["temperatura"].corr(df["no2"])
    r_wiatr = df["wiatr"].corr(df["no2"])

    # Tworzymy wykres ze wspólną osią Y
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)

    # --- Wykres 1: Temperatura vs NO2 ---
    ax1.scatter(
        df["temperatura"], df["no2"],
        color="#e53935", alpha=0.55, s=38,
        edgecolors="white", linewidth=0.5, label="Pomiary dobowe"
    )
    # Linia trendu
    fit_temp = np.poly1d(np.polyfit(df["temperatura"], df["no2"], 1))
    x_t = np.linspace(df["temperatura"].min(), df["temperatura"].max(), 100)
    ax1.plot(x_t, fit_temp(x_t), color="#b71c1c", linestyle="--", linewidth=2, label="Trend liniowy")

    ax1.set_xlabel("Średnia temperatura dobowa [°C]", fontsize=10)
    ax1.set_ylabel("NO₂ [µmol/m²]", fontsize=10)
    ax1.set_title(f"Temperatura vs NO₂ (r = {r_temp:.2f})", fontsize=11, fontweight="bold")
    ax1.legend(loc="upper right", frameon=True, framealpha=0.9, fontsize=8.5)

    # --- Wykres 2: Wiatr vs NO2 ---
    ax2.scatter(
        df["wiatr"], df["no2"],
        color="#1e88e5", alpha=0.55, s=38,
        edgecolors="white", linewidth=0.5, label="Pomiary dobowe"
    )
    # Linia trendu
    fit_wiatr = np.poly1d(np.polyfit(df["wiatr"], df["no2"], 1))
    x_w = np.linspace(df["wiatr"].min(), df["wiatr"].max(), 100)
    ax2.plot(x_w, fit_wiatr(x_w), color="#0d47a1", linestyle="--", linewidth=2, label="Trend liniowy")

    ax2.set_xlabel("Maks. prędkość wiatru [km/h]", fontsize=10)
    ax2.set_title(f"Wiatr vs NO₂ (r = {r_wiatr:.2f})", fontsize=11, fontweight="bold")
    ax2.legend(loc="upper right", frameon=True, framealpha=0.9, fontsize=8.5)

    # Stylistyka osi i siatki
    for ax in (ax1, ax2):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, linestyle=":", alpha=0.6, color="#bdbdbd")
        ax.tick_params(labelsize=9)

    fig.tight_layout()

    def sila(r):
        a = abs(r)
        return "silna" if a >= 0.5 else "umiarkowana" if a >= 0.3 else "słaba"

    opis = (f"Dzienne NO₂ w Krakowie zestawione z pogodą z Open-Meteo ({len(df)} dni z pomiarem). "
            f"Zależność od temperatury jest <b>{sila(r_temp)}</b> (r = {r_temp:.2f}), "
            f"od wiatru <b>{sila(r_wiatr)}</b> (r = {r_wiatr:.2f}). "
            f"Ujemne r oznacza, że im cieplej lub im mocniej wieje, tym mniej NO₂.")
    return [opis, fig]