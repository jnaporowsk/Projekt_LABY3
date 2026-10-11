"""Zamienia wyniki feature'ów na stronę HTML. Feature'y nie muszą znać HTML-a.

Feature może zwrócić (pojedynczo albo w liście):
    wykres matplotlib (fig)      -> obrazek
    tekst (str)                  -> akapit (można użyć prostego HTML, np. <b>)
    pandas.DataFrame / Series    -> tabela
    Mapa(siatka, dane)           -> interaktywna mapa; kliknięcie pokazuje wykres NO2 w tym miejscu
    Plik("nazwa.csv", dane)      -> plik do pobrania (tekst, bajty albo tabela pandas -> CSV);
                                    obrazki .png/.gif są od razu wyświetlane
    Html("<div>...</div>")       -> dowolny HTML/JavaScript (interaktywne rzeczy)
"""
import html
import json
import shutil
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

import ustawienia as u

VENDOR = Path(__file__).parent / "vendor"

# Wspólny wygląd wykresów – ustawiany raz, zanim feature'y zaczną rysować
KOLORY = ["#8C3A1B", "#2F6F73", "#C9971C", "#4A5D8F", "#B4654A", "#6E8B3D"]
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#9AA6B1",
    "axes.labelcolor": "#33404D",
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.titlepad": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "axes.prop_cycle": matplotlib.cycler(color=KOLORY),
    "grid.color": "#E1E6EB",
    "grid.linewidth": 0.7,
    "xtick.color": "#4A5663",
    "ytick.color": "#4A5663",
    "legend.frameon": False,
    "savefig.dpi": 150,
})


class Mapa:
    """Mapa NO2 do pokazania na stronie. siatka = 2D numpy, np. dane.mapa()."""

    def __init__(self, siatka, dane, legenda=f"NO₂ [{u.JEDNOSTKA}]", kolory="YlOrRd", vmin=None, vmax=None,
                 wykres_po_kliknieciu=True):
        self.siatka, self.dane, self.legenda, self.kolory = siatka, dane, legenda, kolory
        self.klik = wykres_po_kliknieciu
        lo, hi = np.nanpercentile(siatka, [2, 98])
        self.vmin = lo if vmin is None else vmin
        self.vmax = hi if vmax is None else vmax


class Html(str):
    """Surowy HTML/JS wstawiany bez zmian."""


class Plik:
    """Plik zapisywany obok strony: do pobrania albo (png/gif) do wyświetlenia."""

    def __init__(self, nazwa, zawartosc, opis=None):
        self.nazwa, self.zawartosc, self.opis = nazwa, zawartosc, opis


class _Budowniczy:
    def __init__(self, folder: Path):
        self.folder = folder
        self.assets = folder / "assets"
        self.assets.mkdir(parents=True, exist_ok=True)
        self.licznik = 0

    def _nazwa(self, prefiks, ext):
        self.licznik += 1
        return f"{prefiks}_{self.licznik:03d}.{ext}"

    def element(self, el, sekcja):
        if isinstance(el, plt.Figure):
            n = self._nazwa(sekcja, "png")
            el.savefig(self.assets / n, dpi=130, bbox_inches="tight")
            plt.close(el)
            return f'<figure><img src="assets/{n}" alt="Wykres: {html.escape(sekcja)}"></figure>'
        if isinstance(el, Html):
            return str(el)
        if isinstance(el, str):
            return f"<p>{el}</p>"
        if isinstance(el, Plik):
            return self._plik(el)
        if isinstance(el, pd.Series):
            el = el.to_frame()
        if isinstance(el, pd.DataFrame):
            t = el.copy()
            if isinstance(t.index, pd.DatetimeIndex):
                t.index = t.index.strftime("%d.%m.%Y")
            t.index.name = t.index.name or ""
            t = t.reset_index()
            return ('<div class="tabela">' + t.to_html(index=False, border=0, na_rep="–",
                    float_format=lambda v: f"{v:,.1f}".replace(",", " ").replace(".", ",")) + "</div>")
        if isinstance(el, Mapa):
            return self._mapa(el, sekcja)
        return f"<pre>{html.escape(repr(el))}</pre>"

    def _plik(self, f):
        z = f.zawartosc
        if isinstance(z, (pd.DataFrame, pd.Series)):
            z = z.to_csv(encoding=None)
        if isinstance(z, str):
            z = z.encode("utf-8-sig")
        (self.assets / f.nazwa).write_bytes(z)
        if f.nazwa.lower().endswith((".png", ".gif", ".jpg")):
            return f'<figure><img src="assets/{f.nazwa}" alt="{html.escape(f.opis or f.nazwa)}"></figure>'
        return f'<p class="pobierz"><a href="assets/{f.nazwa}" download>Pobierz {html.escape(f.opis or f.nazwa)}</a></p>'

    def _mapa(self, m, sekcja):
        norm = np.clip((m.siatka - m.vmin) / (m.vmax - m.vmin), 0, 1)
        rgba = (plt.get_cmap(m.kolory)(np.nan_to_num(norm)) * 255).astype("uint8")
        rgba[..., 3] = np.where(np.isnan(m.siatka), 0, 200)
        obraz = self._nazwa(sekcja, "png")
        Image.fromarray(rgba).save(self.assets / obraz)

        fig, ax = plt.subplots(figsize=(4.5, 0.5))
        fig.colorbar(plt.cm.ScalarMappable(plt.Normalize(m.vmin, m.vmax), m.kolory), cax=ax,
                     orientation="horizontal", label=m.legenda)
        leg = self._nazwa(sekcja, "png")
        fig.savefig(self.assets / leg, dpi=130, bbox_inches="tight")
        plt.close(fig)

        div = f"mapa_{self.licznik}"
        klik = self._klik_js(m) if m.klik else ""
        miasta = json.dumps([[n, la, lo] for n, (la, lo) in u.MIASTA.items()], ensure_ascii=False)
        return f"""<div id="{div}" class="mapa"></div><img class="legenda" src="assets/{leg}" alt="Legenda: {html.escape(m.legenda)}">
<script>(function() {{
  var map = L.map('{div}'), b = {json.dumps(m.dane.granice)};
  L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{maxZoom: 12, attribution: '&copy; OpenStreetMap'}}).addTo(map);
  L.imageOverlay('assets/{obraz}', b, {{opacity: 0.8}}).addTo(map);
  {miasta}.forEach(function(c) {{
    L.circleMarker([c[1], c[2]], {{radius: 5, color: '#222', weight: 1.5, fillColor: '#fff', fillOpacity: 1}})
      .addTo(map).bindTooltip(c[0], {{permanent: true, direction: 'right'}}); }});
  map.fitBounds(b);
  {klik}
}})();</script>"""

    def _klik_js(self, m):
        """Kliknięcie na mapie -> popup z wykresem średnich miesięcznych NO2 w tym pikselu."""
        etykiety, kostka = m.dane.miesiecznie()
        siatka = [[[None if np.isnan(v) else round(float(v), 1) for v in kostka[:, r, c]]
                   for c in range(kostka.shape[2])] for r in range(kostka.shape[1])]
        region = [None if np.isnan(v) else round(float(v), 1) for v in np.nanmean(kostka, axis=(1, 2))]
        (s, w), (n, e) = m.dane.granice
        return f"""
  var D = {json.dumps(siatka)}, R = {json.dumps(region)}, M = {json.dumps(etykiety)};
  var N = {n}, S = {s}, W = {w}, E = {e}, NY = D.length, NX = D[0].length;
  function linia(v, x0, y0, sx, sy, lo) {{
    return v.map(function(a, i) {{ return a === null ? null : (x0 + i * sx).toFixed(1) + ',' + (y0 - (a - lo) * sy).toFixed(1); }})
            .filter(function(p) {{ return p; }}).join(' ');
  }}
  map.on('click', function(ev) {{
    var r = Math.floor((N - ev.latlng.lat) / (N - S) * NY), c = Math.floor((ev.latlng.lng - W) / (E - W) * NX);
    if (r < 0 || c < 0 || r >= NY || c >= NX) return;
    var v = D[r][c], ok = v.filter(function(a) {{ return a !== null; }});
    if (!ok.length) {{ L.popup().setLatLng(ev.latlng).setContent('Brak pomiarów').openOn(map); return; }}
    var all = ok.concat(R.filter(function(a) {{ return a !== null; }}));
    var lo = Math.min.apply(null, all), hi = Math.max.apply(null, all), W0 = 300, H0 = 140, x0 = 34, y0 = 115;
    var sx = (W0 - x0 - 8) / Math.max(v.length - 1, 1), sy = 95 / Math.max(hi - lo, 1);
    var svg = '<svg width="' + W0 + '" height="' + H0 + '" style="font:10px sans-serif">' +
      '<line x1="' + x0 + '" y1="' + y0 + '" x2="' + (W0 - 8) + '" y2="' + y0 + '" stroke="#999"/>' +
      '<text x="2" y="' + (y0 - 95 + 4) + '">' + hi.toFixed(0) + '</text><text x="2" y="' + y0 + '">' + lo.toFixed(0) + '</text>' +
      '<polyline fill="none" stroke="#aaa" stroke-dasharray="4 3" stroke-width="1.5" points="' + linia(R, x0, y0, sx, sy, lo) + '"/>' +
      '<polyline fill="none" stroke="#c0392b" stroke-width="2.2" points="' + linia(v, x0, y0, sx, sy, lo) + '"/>' +
      '<text x="' + x0 + '" y="' + (y0 + 14) + '">' + M[0] + '</text>' +
      '<text x="' + (W0 - 8) + '" y="' + (y0 + 14) + '" text-anchor="end">' + M[M.length - 1] + '</text></svg>';
    var sr = ok.reduce(function(a, b) {{ return a + b; }}, 0) / ok.length;
    L.popup({{maxWidth: 320}}).setLatLng(ev.latlng).setContent(
      '<b>' + ev.latlng.lat.toFixed(3) + '°N, ' + ev.latlng.lng.toFixed(3) + '°E</b><br>' +
      'Średnio <b>' + sr.toFixed(1) + ' {u.JEDNOSTKA}</b> · <span style="color:#c0392b">■</span> tutaj ' +
      '<span style="color:#aaa">┄</span> średnia regionu<br>' + svg).openOn(map);
  }});"""


MIESIACE = ["sty", "lut", "mar", "kwi", "maj", "cze", "lip", "sie", "wrz", "paź", "lis", "gru"]


def _paski(dane):
    """Pas dni: każdy pionowy pasek to jeden dzień, kolor = średnie NO2 nad całym regionem."""
    dzienne = np.array([np.nan if np.isnan(d).all() else np.nanmean(d) for d in dane.no2])
    lo, hi = np.nanpercentile(dzienne, [2, 98])
    cmap = plt.get_cmap("YlOrRd")
    rects = []
    for i, (dzien, v) in enumerate(zip(dane.czas, dzienne)):
        if np.isnan(v):
            kolor, opis = "#D5DCE2", "brak pomiaru (chmury)"
        else:
            kolor = matplotlib.colors.to_hex(cmap(float(np.clip((v - lo) / (hi - lo), 0, 1))))
            opis = f"{v:.0f} {u.JEDNOSTKA}"
        rects.append(f'<rect x="{i}" width="1.08" height="1" fill="{kolor}"><title>{dzien:%d.%m.%Y}: {opis}</title></rect>')
    n = len(dzienne)
    miesiace = "".join(
        f'<span style="left:{100 * i / n:.2f}%">{nazwa}</span>'
        for i, d in enumerate(dane.czas) if d.day == 1
        for nazwa in [MIESIACE[d.month - 1]])
    najgorszy = dane.czas[int(np.nanargmax(dzienne))]
    najczystszy = dane.czas[int(np.nanargmin(dzienne))]
    return f"""<div class="paski" role="img" aria-label="Dzienne średnie NO₂ nad regionem, {n} dni">
  <svg viewBox="0 0 {n} 1" preserveAspectRatio="none">{''.join(rects)}</svg>
  <div class="miesiace">{miesiace}</div>
</div>
<p class="podpis">Każdy pasek to jeden dzień, im ciemniejszy, tym więcej NO₂ nad regionem.
Najgorszy dzień: <b>{najgorszy:%d.%m.%Y}</b>, najczystszy: <b>{najczystszy:%d.%m.%Y}</b>.
Szare paski to dni, w których chmury zasłoniły widok satelicie. Najedź na pasek, żeby zobaczyć wartość.</p>"""


def zbuduj(wyniki, folder: Path, zrodlo: str, dane=None) -> Path:
    """wyniki: lista (id, tytuł, lista elementów[, skrót do menu]). dane – opcjonalnie, do paska dni."""
    folder = Path(folder)
    if folder.exists():
        shutil.rmtree(folder)
    b = _Budowniczy(folder)
    shutil.copytree(VENDOR, folder / "vendor")
    sekcje, nawigacja = [], []
    for wpis in wyniki:
        ident, tytul, elementy = wpis[:3]
        skrot = wpis[3] if len(wpis) > 3 and wpis[3] else tytul
        tresc = "\n".join(b.element(e, ident) for e in elementy)
        sekcje.append(f'<section id="{ident}"><h2>{html.escape(tytul)}</h2>\n{tresc}\n</section>')
        nawigacja.append(f'<a href="#{ident}" title="{html.escape(tytul)}">{html.escape(skrot)}</a>')
    if dane is not None:
        okres = f"od {dane.czas[0]:%d.%m.%Y} do {dane.czas[-1]:%d.%m.%Y}"
        paski = _paski(dane)
    else:
        okres, paski = "", ""
    (folder / "index.html").write_text(SZABLON.format(
        zrodlo=html.escape(zrodlo), okres=okres, paski=paski, nawigacja="".join(nawigacja),
        sekcje="\n".join(sekcje), data=datetime.now().strftime("%d.%m.%Y")), encoding="utf-8")
    return folder / "index.html"


SZABLON = """<!doctype html>
<html lang="pl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Smog NO₂ nad Małopolską</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800&display=swap">
<link rel="stylesheet" href="vendor/leaflet.css"><script src="vendor/leaflet.js"></script>
<style>
  :root {{
    --niebo: #E9EEF2; --papier: #FFFFFF; --atrament: #1D2733; --mgla: #5B6876;
    --linia: #C8D1D9; --tlenek: #8C3A1B; --szer: 880px;
  }}
  * {{ box-sizing: border-box; }}
  html {{ scroll-behavior: smooth; scroll-padding-top: 5rem; }}
  @media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior: auto; }} }}
  body {{ margin: 0; background: var(--niebo); color: var(--atrament);
    font: 400 1.0625rem/1.6 "Archivo", system-ui, sans-serif; }}
  a {{ color: var(--tlenek); }}
  a:focus-visible {{ outline: 2px solid var(--tlenek); outline-offset: 3px; border-radius: 2px; }}

  header {{ max-width: var(--szer); margin: 0 auto; padding: 3.5rem 1rem 1.5rem; }}
  h1 {{ font-stretch: 68%; font-weight: 800; font-size: clamp(2.6rem, 8vw, 5rem); line-height: .95;
    letter-spacing: -.01em; margin: 0 0 1.1rem; }}
  .lede {{ font-size: 1.2rem; max-width: 36em; margin: 0; color: var(--atrament); }}
  .zrodlo {{ color: var(--mgla); font-size: .9rem; margin: .7rem 0 0; }}

  .paski {{ position: relative; margin: 2rem 0 0; padding: 0 0 1.4rem; }}
  .paski svg {{ display: block; width: 100%; height: clamp(90px, 16vw, 170px); }}
  .miesiace {{ position: absolute; left: 0; right: 0; bottom: 0; height: 1.2rem;
    font-size: .75rem; color: var(--mgla); }}
  .miesiace span {{ position: absolute; padding-left: 3px; border-left: 1px solid var(--linia); }}
  @media (max-width: 520px) {{ .miesiace {{ font-size: .62rem; }} }}
  .podpis {{ max-width: var(--szer); margin: .6rem auto 0; padding: 0 1rem; font-size: .9rem; color: var(--mgla); }}

  nav {{ position: sticky; top: 0; z-index: 1000; background: var(--atrament); margin-top: 2.5rem;
    box-shadow: 0 1px 0 rgba(0,0,0,.25); }}
  nav div {{ max-width: calc(var(--szer) + 2rem); margin: 0 auto; padding: .55rem 1rem; display: flex;
    flex-wrap: wrap; gap: .35rem; }}
  nav a {{ display: inline-flex; align-items: center; min-height: 2.6rem; padding: 0 .8rem; border-radius: 4px;
    color: #E9EEF2; text-decoration: none; font-size: .95rem; font-weight: 600; white-space: nowrap;
    background: rgba(255,255,255,.08); }}
  nav a:hover {{ background: rgba(255,255,255,.18); color: #fff; }}
  nav a.aktywny {{ background: var(--tlenek); color: #fff; }}
  nav a:focus-visible {{ outline: 2px solid #fff; outline-offset: 2px; }}
  @media (max-width: 700px) {{
    nav div {{ flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; padding: .5rem 1rem; }}
    nav div::-webkit-scrollbar {{ display: none; }}
    nav a {{ flex: none; }}
  }}
  main {{ max-width: var(--szer); margin: 0 auto; padding: 0 1rem 4rem; }}
  section {{ padding: 3rem 0 0; }}
  section + section {{ margin-top: 1rem; border-top: 1px solid var(--linia); }}
  h2 {{ font-stretch: 80%; font-weight: 700; font-size: 1.75rem; line-height: 1.15; margin: 0 0 1rem; max-width: 26em; }}
  p {{ max-width: 40em; }}
  figure {{ margin: 1.4rem 0; background: var(--papier); padding: .8rem; border: 1px solid var(--linia); border-radius: 4px; }}
  figure img {{ display: block; width: 100%; height: auto; }}
  .mapa {{ height: min(520px, 70vh); border: 1px solid var(--linia); border-radius: 4px; margin: 1.4rem 0 .4rem; }}
  .legenda {{ display: block; width: min(360px, 100%); margin: 0 0 1rem; }}

  .tabela {{ overflow-x: auto; margin: 1.2rem 0; }}
  table {{ border-collapse: collapse; font-size: .92rem; font-variant-numeric: tabular-nums; background: var(--papier); }}
  th {{ text-align: right; font-weight: 600; padding: .55rem .9rem; border-bottom: 2px solid var(--atrament); vertical-align: bottom; }}
  td {{ text-align: right; padding: .45rem .9rem; border-bottom: 1px solid #E3E8EC; }}
  th:first-child, td:first-child {{ text-align: left; }}
  tbody tr:hover {{ background: #F4F7F9; }}
  .pobierz a {{ display: inline-block; padding: .45rem .9rem; border: 1px solid var(--tlenek); border-radius: 4px;
    text-decoration: none; font-weight: 600; }}
  .pobierz a:hover {{ background: var(--tlenek); color: #fff; }}
  .blad {{ display: block; color: #9B1C1C; background: #FBEDED; padding: 1rem; white-space: pre-wrap;
    font: .82rem/1.45 ui-monospace, Consolas, monospace; border-radius: 4px; }}

  footer {{ border-top: 1px solid var(--linia); color: var(--mgla); font-size: .88rem; }}
  footer div {{ max-width: var(--szer); margin: 0 auto; padding: 1.5rem 1rem 3rem; }}
  footer p {{ margin: .3rem 0; }}
</style></head><body>
<header>
  <h1>Smog NO₂ nad Małopolską</h1>
  <p class="lede">Dwutlenek azotu nad województwem małopolskim, dzień po dniu, widziany z satelity Sentinel-5P.
  Pochodzi głównie ze spalin samochodów, elektrowni i ogrzewania domów.</p>
  <p class="zrodlo">Dane: {zrodlo}. Okres: {okres}.</p>
</header>
{paski}
<nav aria-label="Spis analiz"><div>{nawigacja}</div></nav>
<main>
{sekcje}
</main>
<footer><div>
  <p>Dane satelitarne: Sentinel-5P/TROPOMI (Copernicus, ESA), pobrane z Copernicus Data Space Ecosystem. Troposferyczna kolumna NO₂ w µmol/m².</p>
  <p>Podkład mapy: OpenStreetMap. Mapy: Leaflet.</p>
  <p>Projekt 3, Przetwarzanie i analiza danych cyfrowych, AGH. Wygenerowano {data}.</p>
</div></footer>
<script>
  // podświetlenie w menu sekcji, która jest właśnie na ekranie
  (function() {{
    var linki = document.querySelectorAll('nav a'), pasek = document.querySelector('nav div');
    if (!('IntersectionObserver' in window)) return;
    var obs = new IntersectionObserver(function(wpisy) {{
      wpisy.forEach(function(w) {{
        if (!w.isIntersecting) return;
        linki.forEach(function(a) {{
          var on = a.getAttribute('href') === '#' + w.target.id;
          a.classList.toggle('aktywny', on);
          if (on && pasek.scrollWidth > pasek.clientWidth)   // na telefonie: przewiń menu do aktywnej pozycji
            pasek.scrollLeft = a.offsetLeft - (pasek.clientWidth - a.offsetWidth) / 2;
        }});
      }});
    }}, {{ rootMargin: '-30% 0px -60% 0px' }});
    document.querySelectorAll('main section').forEach(function(s) {{ obs.observe(s); }});
  }})();
</script>
</body></html>
"""
