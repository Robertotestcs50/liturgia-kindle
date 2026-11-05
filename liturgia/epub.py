"""Construye un EPUB 3 válido (con NCX para lectores antiguos) y su portada."""

from __future__ import annotations

import datetime as dt
import io
import uuid
import zipfile
from html import escape
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .fuentes import MESES, Seccion, fecha_larga
from .limpieza import bloques_a_xhtml

TIPOS = Path(__file__).parent / "tipografia"

CSS = """
@charset "utf-8";
body { font-family: serif; line-height: 1.45; margin: 0 2%; orphans: 2; widows: 2; }
h1 { font-size: 1.6em; font-weight: normal; text-align: center; margin: 1.2em 0 0.2em; }
h2 { font-size: 1.25em; font-weight: normal; text-align: center; margin: 0.4em 0 1.2em; }
h3 { font-size: 0.85em; font-weight: bold; text-transform: uppercase; letter-spacing: 0.08em;
     margin: 1.6em 0 0.5em; page-break-after: avoid; color: #a01010; }
p { margin: 0 0 0.85em; text-indent: 0; text-align: left; }
p.salmo { font-variant: small-caps; font-weight: bold; margin: 1.3em 0 0.4em;
          page-break-after: avoid; color: #a01010; }
p.ant { margin-left: 0; }
.r { color: #a01010; font-weight: bold; }
.cabecera { text-align: center; font-style: italic; margin-bottom: 1.5em; }
.portada { text-align: center; }
.portada .dia { font-size: 1.15em; margin-top: 0.6em; }
.portada .celebracion { font-style: italic; margin: 0.8em 0 1.8em; }
.indice { text-align: center; margin-top: 1em; }
.indice p { margin: 0 0 0.9em; font-size: 1.1em; text-align: center; }
.portada p { text-align: center; }
.indice a { text-decoration: none; }
.aviso { border: 1px solid #888; padding: 0.6em; font-style: italic; }
.fuente { font-size: 0.75em; color: #555; margin-top: 2.5em; text-align: center; }
.cruz { text-align: center; font-size: 1.4em; margin: 0.6em 0; }
"""

XHTML = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="es" lang="es">
<head>
<meta charset="utf-8"/>
<title>{titulo}</title>
<link rel="stylesheet" type="text/css" href="estilo.css"/>
</head>
<body>
{cuerpo}
</body>
</html>
"""


# --------------------------------------------------------------------------
# Portada (imagen) para la biblioteca del Kindle
# --------------------------------------------------------------------------

def _fuente(nombre: str, tam: int):
    return ImageFont.truetype(str(TIPOS / f"EBGaramond-{nombre}.ttf"), tam)


def _centrar(draw, y, texto, fuente, ancho, color=0):
    caja = draw.textbbox((0, 0), texto, font=fuente)
    draw.text(((ancho - (caja[2] - caja[0])) / 2 - caja[0], y), texto, font=fuente, fill=color)
    return y + (caja[3] - caja[1])


def _partir(draw, texto, fuente, ancho_max):
    palabras, lineas, actual = texto.split(), [], ""
    for p in palabras:
        prueba = (actual + " " + p).strip()
        if draw.textlength(prueba, font=fuente) <= ancho_max:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas


def portada_png(d: dt.date, celebracion: str, pie: str) -> bytes:
    W, H = 1264, 1680  # proporción de la pantalla del Kindle
    img = Image.new("L", (W, H), 255)
    dr = ImageDraw.Draw(img)
    m = 70
    dr.rectangle([m, m, W - m, H - m], outline=0, width=4)
    dr.rectangle([m + 16, m + 16, W - m - 16, H - m - 16], outline=0, width=1)

    # Cruz
    cx, cy = W // 2, 330
    dr.rectangle([cx - 9, cy - 95, cx + 9, cy + 125], fill=0)
    dr.rectangle([cx - 70, cy - 35, cx + 70, cy - 17], fill=0)

    y = 540
    y = _centrar(dr, y, "LITURGIA", _fuente("600-normal", 110), W) + 30
    y = _centrar(dr, y, "del día", _fuente("400-italic", 78), W) + 110

    dia = f"{fecha_larga(d)}"
    dia = dia[0].upper() + dia[1:]
    for linea in _partir(dr, dia, _fuente("500-normal", 66), W - 2 * m - 120):
        y = _centrar(dr, y, linea, _fuente("500-normal", 66), W) + 22

    y += 70
    dr.line([W / 2 - 160, y, W / 2 + 160, y], fill=0, width=2)
    y += 60
    f = _fuente("400-italic", 52)
    for linea in _partir(dr, celebracion, f, W - 2 * m - 160)[:6]:
        y = _centrar(dr, y, linea, f, W, color=40) + 18

    fp = _fuente("500-normal", 38)
    lineas_pie = _partir(dr, pie, fp, W - 2 * m - 120)
    yp = H - m - 110 - 50 * len(lineas_pie)
    for linea in lineas_pie:
        yp = _centrar(dr, yp, linea, fp, W, color=60) + 16

    out = io.BytesIO()
    img.save(out, "PNG", optimize=True)
    return out.getvalue()


# --------------------------------------------------------------------------
# Libro
# --------------------------------------------------------------------------

def construir(d: dt.date, celebracion: str, secciones: list[Seccion],
              avisos: list[str], destino: Path) -> Path:
    ident = uuid.uuid5(uuid.NAMESPACE_URL, f"liturgia-kindle:{d.isoformat()}")
    titulo_libro = f"Liturgia · {fecha_larga(d).capitalize()}"
    modificado = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    dia = fecha_larga(d).capitalize()

    archivos: dict[str, bytes] = {}

    # Portada (imagen)
    pie = " · ".join(s.titulo.replace(" del día", "") for s in secciones)
    archivos["OEBPS/portada.png"] = portada_png(d, celebracion or dia, pie)
    archivos["OEBPS/portada.xhtml"] = XHTML.format(
        titulo="Portada",
        cuerpo='<div style="text-align:center"><img src="portada.png" alt="Portada" '
               'style="max-width:100%;height:auto"/></div>',
    ).encode()

    # Página de inicio con índice
    enlaces = "\n".join(
        f'<p><a href="{s.clave}.xhtml">{escape(s.titulo)}</a></p>' for s in secciones
    )
    aviso_html = "".join(f'<p class="aviso">{escape(a)}</p>' for a in avisos)
    archivos["OEBPS/inicio.xhtml"] = XHTML.format(
        titulo=escape(dia),
        cuerpo=f"""<div class="portada">
<p class="cruz">†</p>
<h1>{escape(dia)}</h1>
<p class="celebracion">{escape(celebracion)}</p>
</div>
{aviso_html}
<div class="indice">
{enlaces}
</div>""",
    ).encode()

    for s in secciones:
        sub = f'<p class="cabecera">{escape(s.subtitulo)}</p>' if s.subtitulo else ""
        cuerpo = (
            f'<h1 id="inicio">{escape(s.titulo)}</h1>\n<h2>{escape(dia)}</h2>\n{sub}\n'
            f"{bloques_a_xhtml(s.bloques)}\n"
            f'<p class="fuente">Texto: {escape(s.origen)}</p>'
        )
        archivos[f"OEBPS/{s.clave}.xhtml"] = XHTML.format(titulo=escape(s.titulo), cuerpo=cuerpo).encode()

    archivos["OEBPS/estilo.css"] = CSS.encode()

    # Navegación EPUB 3
    nav_items = "\n".join(
        f'<li><a href="{s.clave}.xhtml">{escape(s.titulo)}</a></li>' for s in secciones
    )
    archivos["OEBPS/nav.xhtml"] = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="es" lang="es">
<head><meta charset="utf-8"/><title>Índice</title></head>
<body>
<nav epub:type="toc" id="toc"><h1>Índice</h1>
<ol>
<li><a href="inicio.xhtml">{escape(dia)}</a></li>
{nav_items}
</ol>
</nav>
<nav epub:type="landmarks" hidden="hidden"><ol>
<li><a epub:type="cover" href="portada.xhtml">Portada</a></li>
<li><a epub:type="toc" href="inicio.xhtml">Índice</a></li>
<li><a epub:type="bodymatter" href="inicio.xhtml">Inicio</a></li>
</ol></nav>
</body>
</html>
""".encode()

    # NCX (compatibilidad)
    puntos = [("inicio", dia)] + [(s.clave, s.titulo) for s in secciones]
    nav_points = "\n".join(
        f'<navPoint id="n{i}" playOrder="{i}"><navLabel><text>{escape(t)}</text></navLabel>'
        f'<content src="{c}.xhtml"/></navPoint>'
        for i, (c, t) in enumerate(puntos, start=1)
    )
    archivos["OEBPS/toc.ncx"] = f"""<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="es">
<head><meta name="dtb:uid" content="urn:uuid:{ident}"/><meta name="dtb:depth" content="1"/>
<meta name="dtb:totalPageCount" content="0"/><meta name="dtb:maxPageNumber" content="0"/></head>
<docTitle><text>{escape(titulo_libro)}</text></docTitle>
<navMap>
{nav_points}
</navMap>
</ncx>
""".encode()

    capitulos = ["inicio"] + [s.clave for s in secciones]
    manifest = "\n".join(
        f'<item id="{c}" href="{c}.xhtml" media-type="application/xhtml+xml"/>' for c in capitulos
    )
    spine = "\n".join(f'<itemref idref="{c}"/>' for c in capitulos)
    archivos["OEBPS/content.opf"] = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="es">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="uid">urn:uuid:{ident}</dc:identifier>
<dc:title>{escape(titulo_libro)}</dc:title>
<dc:language>es</dc:language>
<dc:creator>Liturgia de las Horas</dc:creator>
<dc:publisher>Liturgia diaria</dc:publisher>
<dc:date>{d.isoformat()}</dc:date>
<dc:description>{escape(celebracion)}</dc:description>
<meta property="dcterms:modified">{modificado}</meta>
<meta name="cover" content="portada-img"/>
</metadata>
<manifest>
<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
<item id="css" href="estilo.css" media-type="text/css"/>
<item id="portada-img" href="portada.png" media-type="image/png" properties="cover-image"/>
<item id="portada" href="portada.xhtml" media-type="application/xhtml+xml"/>
{manifest}
</manifest>
<spine toc="ncx">
<itemref idref="portada" linear="yes"/>
{spine}
</spine>
<guide>
<reference type="cover" title="Portada" href="portada.xhtml"/>
<reference type="toc" title="Índice" href="inicio.xhtml"/>
<reference type="text" title="Inicio" href="inicio.xhtml"/>
</guide>
</package>
""".encode()

    archivos["META-INF/container.xml"] = b"""<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>
"""

    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), b"application/epub+zip", compress_type=zipfile.ZIP_STORED)
        for nombre, datos in archivos.items():
            z.writestr(nombre, datos, compress_type=zipfile.ZIP_DEFLATED)
    return destino


def nombre_archivo(d: dt.date) -> str:
    return f"Liturgia_{d.isoformat()}_{MESES[d.month - 1]}.epub"
