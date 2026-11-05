"""Descarga de los textos del día desde fuentes de España.

* Liturgia de las Horas: Salmodiando (salmodiando.es), que admite cualquier
  fecha con ``?fecha=AAAA-MM-DD`` y usa para la hora intermedia el salterio
  del día (lo correcto cuando se reza una sola hora menor).
* Evangelio: Oración y Liturgia, de la Archidiócesis de Madrid (leccionario de
  España), a través de la API pública de WordPress de la propia web.

Cada función comprueba que lo descargado es de verdad lo que se pidió (la
fecha correcta, las partes que no pueden faltar) y si no, lanza un error
claro en lugar de meter en el libro algo equivocado.
"""

from __future__ import annotations

import datetime as dt
import html as html_mod
import re
import time
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup, Tag

from .limpieza import Bloque, Trozo, html_a_bloques, normal, texto_plano

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

AGENTE = "liturgia-kindle/1.0 (lectura personal diaria; un acceso al día)"


class FuenteError(Exception):
    """Algo no se pudo descargar o no superó las comprobaciones."""


@dataclass
class Seccion:
    clave: str            # laudes, sexta, visperas, completas, evangelio
    titulo: str           # «Laudes», «Evangelio del día»...
    bloques: list[Bloque]
    origen: str           # URL de donde salió (para citarla en el libro)
    subtitulo: str = ""   # p. ej. referencia del evangelio


def fecha_larga(d: dt.date) -> str:
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]} de {d.year}"


# --------------------------------------------------------------------------
# Red
# --------------------------------------------------------------------------

# Si se indica una carpeta, se guarda copia de cada página descargada
# (útil para revisar qué devolvió la web cuando algo falla).
GUARDAR_EN = None

_sesion = requests.Session()
_sesion.headers.update({"User-Agent": AGENTE, "Accept-Language": "es-ES,es;q=0.9"})


def descargar(url: str, params: dict | None = None, intentos: int = 4) -> requests.Response:
    ultimo: Exception | None = None
    for i in range(intentos):
        try:
            r = _sesion.get(url, params=params, timeout=40)
            if r.status_code == 200:
                if not r.encoding or r.encoding.lower() == "iso-8859-1":
                    r.encoding = r.apparent_encoding or "utf-8"
                if GUARDAR_EN:
                    from pathlib import Path
                    nombre = re.sub(r"[^A-Za-z0-9]+", "_", r.url)[-150:] + ".html"
                    Path(GUARDAR_EN).mkdir(parents=True, exist_ok=True)
                    (Path(GUARDAR_EN) / nombre).write_text(r.text, encoding="utf-8")
                return r
            ultimo = FuenteError(f"{r.status_code} al pedir {r.url}")
            if r.status_code in (400, 401, 403, 404, 410):
                break
        except requests.RequestException as e:  # red caída, DNS, tiempo agotado...
            ultimo = e
        time.sleep(5 * (i + 1))
    raise FuenteError(f"No se pudo descargar {url}: {ultimo}")


# --------------------------------------------------------------------------
# Liturgia de las Horas (Salmodiando)
# --------------------------------------------------------------------------

HORAS = {
    "laudes": ("Laudes", "https://salmodiando.es/laudes-hoy/"),
    "tercia": ("Tercia", "https://salmodiando.es/tercia-hoy/"),
    "sexta": ("Sexta", "https://salmodiando.es/sexta-hoy/"),
    "nona": ("Nona", "https://salmodiando.es/nona-hoy/"),
    "visperas": ("Vísperas", "https://salmodiando.es/visperas-hoy/"),
    "completas": ("Completas", "https://salmodiando.es/completas-hoy/"),
    "oficio": ("Oficio de lectura", "https://salmodiando.es/oficio-de-lectura-hoy/"),
}

# Texto que marca el final de la oración y el comienzo de lo que ya es la web.
_FIN_ORACION = re.compile(
    r"^(sobre el rezo de este dia|como se reza la liturgia|dia anterior|dia siguiente|"
    r"‹ dia anterior|abrir salmodiando|abrir la app|rezar .{0,30} en la app|"
    r"en la app puedes|descarga la app|aviso legal|politica de privacidad|"
    r"comparte|compartir)",
)
# Texto de la web que puede aparecer antes de la oración.
_RUIDO = re.compile(
    r"^(abrir la app|rezar .{0,30} en la app|funciona sin conexion|salmodiando$|"
    r"oficio de lectura laudes tercia|menu|inicio|volver)",
)


def _contenedor_oracion(soup: BeautifulSoup) -> Tag:
    """El elemento más pequeño que contiene la oración completa."""
    for t in soup(["script", "style", "noscript", "svg", "nav", "footer", "form", "button"]):
        t.decompose()
    candidatos = []
    for el in soup.find_all(["main", "article", "section", "div", "body"]):
        n = normal(el.get_text(" ", strip=True))
        if "himno" in n and "oracion" in n and re.search(r"\bv\.? ", n):
            candidatos.append((len(n), el))
    if not candidatos:
        raise FuenteError("No encuentro la oración en la página (¿ha cambiado la web?)")
    candidatos.sort(key=lambda x: x[0])
    return candidatos[0][1]


def _recortar_oracion(bloques: list[Bloque]) -> list[Bloque]:
    # Empieza en la primera invocación «V. ...» (o en la etiqueta que la precede).
    inicio = None
    for i, b in enumerate(bloques):
        t = b.texto()
        if re.match(r"^(V\.|℣)", t) or re.match(r"^(invocaci[oó]n inicial|invitatorio)\b", normal(t)):
            inicio = i
            break
    if inicio is None:
        raise FuenteError("No encuentro el comienzo de la hora («V. ...»)")
    # Conserva una cabecera breve inmediatamente anterior (p. ej. el título).
    salida = []
    for b in bloques[inicio:]:
        n = normal(b.texto())
        if _FIN_ORACION.match(n):
            break
        if _RUIDO.match(n):
            continue
        salida.append(b)
    return salida


def _comprobar_fecha(texto_pagina: str, d: dt.date):
    """La página debe mostrar la fecha pedida (si no, podría ser otro día)."""
    n = normal(texto_pagina)
    buscado = normal(f"{d.day} de {MESES[d.month - 1]}")
    if buscado not in n:
        raise FuenteError(
            f"La página no corresponde al {fecha_larga(d)} (no aparece «{buscado}»)."
        )


def _comprobar_hora(clave: str, bloques: list[Bloque]):
    n = normal(texto_plano(bloques))
    obligatorio = {
        "laudes": ["himno", "salmodia", "lectura breve", "benedictus|cantico evangelico|bendito sea el senor",
                   "preces|padre nuestro", "oracion"],
        "visperas": ["himno", "salmodia", "lectura breve", "magnificat|cantico evangelico|proclama mi alma",
                     "preces|padre nuestro", "oracion"],
        "completas": ["himno", "salmodia", "lectura breve", "nunc dimittis|cantico evangelico|ahora, senor|simeon",
                      "oracion"],
        "sexta": ["himno", "salmodia", "lectura breve", "oracion"],
        "tercia": ["himno", "salmodia", "lectura breve", "oracion"],
        "nona": ["himno", "salmodia", "lectura breve", "oracion"],
        "oficio": ["himno", "salmodia", "oracion"],
    }[clave]
    faltan = [o for o in obligatorio if not re.search(o, n)]
    if faltan:
        raise FuenteError(f"A {clave} le faltan partes: {', '.join(faltan)}")
    if len(n) < 1200:
        raise FuenteError(f"El texto de {clave} es demasiado corto ({len(n)} caracteres)")


def hora(clave: str, d: dt.date) -> Seccion:
    titulo, base = HORAS[clave]
    r = descargar(base, params={"fecha": d.isoformat()})
    return Seccion(clave, titulo, procesar_hora(r.text, clave, d), r.url)


def procesar_hora(html: str, clave: str, d: dt.date) -> list[Bloque]:
    soup = BeautifulSoup(html, "lxml")
    _comprobar_fecha(soup.get_text(" ", strip=True), d)
    cont = _contenedor_oracion(soup)
    bloques = _recortar_oracion(html_a_bloques(cont))
    _comprobar_hora(clave, bloques)
    return bloques


# --------------------------------------------------------------------------
# Evangelio (Archidiócesis de Madrid)
# --------------------------------------------------------------------------

API_MADRID = "https://oracionyliturgia.archimadrid.org/wp-json/wp/v2/posts"
CATEGORIA_LECTURAS = 10  # «Lecturas de Misa»

_INICIO_EVANGELIO = re.compile(
    r"^(lectura|comienzo|conclusion|lectura continuada) del santo evangelio|^lectura de la pasion|"
    r"^\+?\s*lectura del santo evangelio"
)


def _post_del_dia(d: dt.date) -> dict:
    marca = d.strftime("%d/%m/%Y")
    campos = "id,date,link,title,content"
    intentos = [
        {"categories": CATEGORIA_LECTURAS, "search": marca, "per_page": 10, "_fields": campos},
        {"categories": CATEGORIA_LECTURAS,
         "after": (d - dt.timedelta(days=3)).isoformat() + "T00:00:00",
         "before": (d + dt.timedelta(days=1)).isoformat() + "T23:59:59",
         "per_page": 20, "_fields": campos},
    ]
    for params in intentos:
        try:
            posts = descargar(API_MADRID, params=params).json()
        except (FuenteError, ValueError):
            continue
        for p in posts if isinstance(posts, list) else []:
            titulo = html_mod.unescape(re.sub(r"<[^>]+>", "", p.get("title", {}).get("rendered", "")))
            if titulo.strip().startswith(marca):
                p["_titulo"] = titulo.strip()
                return p
    raise FuenteError(f"No encuentro las lecturas del {marca} en la web de la Archidiócesis de Madrid")


def celebracion_del_dia(post: dict, d: dt.date) -> str:
    """«Miércoles de la 31ª semana de Tiempo Ordinario. San Carlos Borromeo...»."""
    t = post.get("_titulo", "")
    t = re.sub(r"^\s*\d{2}/\d{2}/\d{4}\s*[–—\-:]\s*", "", t).strip()
    abreviaturas = {
        r",?\s*M\.\s*O\.?$": " (memoria obligatoria)",
        r",?\s*M\.\s*L\.?$": " (memoria libre)",
    }
    for patron, texto in abreviaturas.items():
        t = re.sub(patron, texto, t)
    return t.strip()


def evangelio(d: dt.date) -> tuple[Seccion, str]:
    post = _post_del_dia(d)
    bloques, referencias = procesar_evangelio(post["content"]["rendered"])
    return (
        Seccion("evangelio", "Evangelio del día", bloques, post.get("link", API_MADRID),
                subtitulo=referencias[0]),
        celebracion_del_dia(post, d),
    )


def procesar_evangelio(html: str) -> tuple[list[Bloque], list[str]]:
    bloques = html_a_bloques(html)
    textos = [normal(b.texto()) for b in bloques]

    segmentos: list[list[Bloque]] = []
    referencias: list[str] = []
    i = 0
    while i < len(bloques):
        if _INICIO_EVANGELIO.match(textos[i]):
            # Incluye el título del evangelio si va justo antes (frase breve).
            ini = i
            if i > 0 and len(textos[i - 1]) < 220 and not re.match(
                r"^(aleluya|evangelio$|palabra de dios|r\.|salmo|segunda lectura|primera lectura)",
                textos[i - 1],
            ) and not textos[i - 1].endswith("palabra de dios."):
                ini = i - 1
            fin = None
            for j in range(i, len(bloques)):
                if "palabra del senor" in textos[j]:
                    fin = j
                    break
            if fin is None:
                raise FuenteError("El evangelio no termina con «Palabra del Señor»")
            segmentos.append(bloques[ini:fin + 1])
            referencias.append(bloques[i].texto().splitlines()[0])
            i = fin + 1
            continue
        i += 1

    if not segmentos:
        raise FuenteError("No encuentro el evangelio en las lecturas del día")
    if sum(len(texto_plano(s)) for s in segmentos) < 250:
        raise FuenteError("El texto del evangelio es demasiado corto")

    todos: list[Bloque] = []
    for k, seg in enumerate(segmentos):
        if k:  # varios evangelios (Navidad, Ramos...): separador visible
            todos.append(Bloque(lineas=[[Trozo("* * *")]]))
        todos.extend(seg)
    return todos, referencias
