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
            return f'<img src="assets/{n}" alt="">'
        if isinstance(el, Html):
            return str(el)
        if isinstance(el, str):
            return f"<p>{el}</p>"
        if isinstance(el, Plik):
            return self._plik(el)
        if isinstance(el, pd.Series):
            el = el.to_frame()
        if isinstance(el, pd.DataFrame):
            return el.to_html(float_format=lambda v: f"{v:.1f}", na_rep="–", border=0)
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
            return f'<img src="assets/{f.nazwa}" alt="{html.escape(f.opis or f.nazwa)}">'
        return f'<p>⬇ <a href="assets/{f.nazwa}" download>{html.escape(f.opis or f.nazwa)}</a></p>'

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
        return f"""<div id="{div}" class="mapa"></div><img class="legenda" src="assets/{leg}" alt="">
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


def zbuduj(wyniki, folder: Path, zrodlo: str) -> Path:
    """wyniki: lista (id, tytuł, lista elementów)."""
    folder = Path(folder)
    if folder.exists():
        shutil.rmtree(folder)
    b = _Budowniczy(folder)
    shutil.copytree(VENDOR, folder / "vendor")
    sekcje, nawigacja = [], []
    for ident, tytul, elementy in wyniki:
        tresc = "\n".join(b.element(e, ident) for e in elementy)
        sekcje.append(f'<section id="{ident}"><h2>{html.escape(tytul)}</h2>{tresc}</section>')
        nawigacja.append(f'<a href="#{ident}">{html.escape(tytul)}</a>')
    (folder / "index.html").write_text(SZABLON.format(
        zrodlo=html.escape(zrodlo), nawigacja="".join(nawigacja), sekcje="\n".join(sekcje),
        data=datetime.now().strftime("%d.%m.%Y %H:%M")), encoding="utf-8")
    return folder / "index.html"


SZABLON = """<!doctype html>
<html lang="pl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Smog NO₂ nad Małopolską</title>
<link rel="stylesheet" href="vendor/leaflet.css"><script src="vendor/leaflet.js"></script>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; color: #222; background: #fafafa; }}
  header {{ background: #3b2f2f; color: #fff; padding: 1.2rem 1.5rem; }}
  header h1 {{ margin: 0 0 .3rem; font-size: 1.5rem; }} header p {{ margin: 0; opacity: .85; }}
  nav {{ background: #fff; border-bottom: 1px solid #ddd; padding: .6rem 1.5rem; }}
  nav a {{ margin-right: 1rem; color: #8a3b12; text-decoration: none; }}
  main {{ max-width: 1000px; margin: 0 auto; padding: 0 1rem 3rem; }}
  section {{ background: #fff; border: 1px solid #e3e3e3; border-radius: 8px; padding: 1rem 1.3rem; margin-top: 1.5rem; overflow-x: auto; }}
  section h2 {{ margin-top: 0; font-size: 1.2rem; }}
  .mapa {{ height: 480px; border-radius: 6px; }} img {{ max-width: 100%; }}
  table {{ border-collapse: collapse; margin: .8rem 0; }}
  td, th {{ border-bottom: 1px solid #eee; padding: .3rem .8rem; text-align: right; }}
  .blad {{ color: #a00; white-space: pre-wrap; font-family: monospace; font-size: .85rem; }}
  footer {{ text-align: center; color: #777; font-size: .85rem; padding: 1rem; }}
</style></head><body>
<header><h1>Smog NO₂ nad Małopolską</h1>
<p>Sentinel-5P / TROPOMI · troposferyczna kolumna NO₂ · dane: {zrodlo}</p></header>
<nav>{nawigacja}</nav>
<main>
{sekcje}
</main>
<footer>Wygenerowano {data} · Projekt 3, Przetwarzanie i analiza danych cyfrowych, AGH</footer>
</body></html>
"""
