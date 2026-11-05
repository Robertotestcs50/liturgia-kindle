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
from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup, Tag

from .limpieza import Bloque, Trozo, html_a_bloques, normal, texto_linea, texto_plano

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
    datos: dict = field(default_factory=dict)  # celebración, semana del salterio…


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


EXAMEN = ("Pausa en silencio para el examen de conciencia. "
          "Puede concluirse con el acto penitencial («Yo confieso…»).")


def _contenedor_oracion(soup: BeautifulSoup) -> tuple[Tag, bool]:
    """Devuelve el elemento con la oración y si es el bloque propio de la web."""
    for t in soup(["script", "style", "noscript", "svg", "nav", "footer", "form", "button"]):
        t.decompose()
    propio = soup.select_one("article.prayer")
    if propio is not None:
        # El examen de conciencia de Completas viene vacío (en la app es interactivo).
        for ex in propio.select(".examen"):
            if not ex.get_text(strip=True):
                ex.string = EXAMEN
                ex["class"] = ["rubric-note"]
        return propio, True
    # Si algún día la web cambia de estructura: el elemento más pequeño que
    # contenga la oración completa.
    candidatos = []
    for el in soup.find_all(["main", "article", "section", "div", "body"]):
        n = normal(el.get_text(" ", strip=True))
        if "himno" in n and "oracion" in n and re.search(r"\bv\.? ", n):
            candidatos.append((len(n), el))
    if not candidatos:
        raise FuenteError("No encuentro la oración en la página (¿ha cambiado la web?)")
    candidatos.sort(key=lambda x: x[0])
    return candidatos[0][1], False


def _recortar_oracion(bloques: list[Bloque], desde_invocacion: bool) -> list[Bloque]:
    inicio = 0
    if desde_invocacion:
        # Empieza en la primera invocación «V. ...» (o en la etiqueta que la precede).
        inicio = None
        for i, b in enumerate(bloques):
            t = b.texto()
            if re.match(r"^(V\.|℣)", t) or re.match(r"^(invocacion inicial|invitatorio)\b", normal(t)):
                inicio = i
                break
        if inicio is None:
            raise FuenteError("No encuentro el comienzo de la hora («V. ...»)")
    salida = []
    for b in bloques[inicio:]:
        n = normal(b.texto())
        if _FIN_ORACION.match(n):
            break
        if _RUIDO.match(n):
            continue
        salida.append(b)
    return salida


def datos_del_dia(html: str) -> dict:
    """Celebración y semana del salterio según la propia página de Salmodiando."""
    soup = BeautifulSoup(html, "lxml")
    datos = {}
    cel = soup.select_one(".day-hero .celebration")
    if cel:
        datos["celebracion"] = cel.get_text(" ", strip=True)
    intro = soup.select_one("aside.hoy-intro p")
    if intro:
        for parte in intro.get_text(" ", strip=True).split("·"):
            if "salterio" in parte.lower():
                datos["salterio"] = parte.strip().rstrip(".")
    return datos


def _comprobar_fecha(soup: BeautifulSoup, d: dt.date):
    """La página debe ser la del día pedido (si no, podría ser otro día)."""
    buscado = f"{d.day} de {MESES[d.month - 1]} de {d.year}"
    marca = soup.select_one(".hoy-h1-fecha")
    texto = marca.get_text(" ", strip=True) if marca else soup.get_text(" ", strip=True)
    # \b evita que «15 de noviembre» pase por «5 de noviembre».
    if not re.search(r"(?<!\d)" + re.escape(normal(buscado)) + r"\b", normal(texto)):
        raise FuenteError(
            f"La página no corresponde al {fecha_larga(d)}; muestra «{texto[:60]}»."
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
    sec = Seccion(clave, titulo, procesar_hora(r.text, clave, d), r.url)
    sec.datos = datos_del_dia(r.text)
    return sec


def procesar_hora(html: str, clave: str, d: dt.date) -> list[Bloque]:
    soup = BeautifulSoup(html, "lxml")
    _comprobar_fecha(soup, d)
    cont, propio = _contenedor_oracion(soup)
    bloques = _recortar_oracion(html_a_bloques(cont), desde_invocacion=not propio)
    _comprobar_hora(clave, bloques)
    return bloques


# --------------------------------------------------------------------------
# Evangelio (Archidiócesis de Madrid)
# --------------------------------------------------------------------------

API_MADRID = "https://oracionyliturgia.archimadrid.org/wp-json/wp/v2/posts"
CATEGORIA_LECTURAS = 10  # «Lecturas de Misa»

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
        Seccion("evangelio", "Evangelio del día", bloques, post.get("link", API_MADRID)),
        celebracion_del_dia(post, d),
    )


_ETIQUETA_EVANGELIO = re.compile(r"^evangelio\b")
_REFERENCIA_EVANGELIO = re.compile(
    r"^(lectura|comienzo|conclusion) del santo evangelio|^lectura de la pasion|"
    r"^pasion de nuestro senor jesucristo segun"
)
_SOBRANTE = re.compile(r"^(forma larga y forma breve|forma larga|forma breve)\.?$")


def procesar_evangelio(html: str) -> tuple[list[Bloque], list[str]]:
    """Extrae el evangelio de las lecturas del día.

    En la web de Madrid el evangelio empieza con un párrafo cuya primera línea
    es «EVANGELIO» (seguida del título y de la referencia) y termina con
    «Palabra del Señor.». Si hay forma larga y breve (Ramos), se queda con la
    larga, que contiene a la breve.
    """
    bloques = html_a_bloques(html)
    primera = [normal(texto_linea(b.lineas[0])) for b in bloques]

    inicios = [i for i, t in enumerate(primera) if _ETIQUETA_EVANGELIO.match(t)]
    if not inicios:  # por si algún día falta la etiqueta: buscar la referencia
        inicios = [i for i, t in enumerate(primera) if _REFERENCIA_EVANGELIO.match(t)]

    segmentos: list[tuple[str, list[Bloque]]] = []
    fin_anterior = -1
    for ini in inicios:
        if ini <= fin_anterior:
            continue  # etiqueta interior («EVANGELIO (forma larga)»)
        fin = next((j for j in range(ini, len(bloques))
                    if "palabra del senor" in normal(bloques[j].texto())), None)
        if fin is None:
            raise FuenteError("El evangelio no termina con «Palabra del Señor»")
        segmentos.append((primera[ini], bloques[ini:fin + 1]))
        fin_anterior = fin

    if len(segmentos) > 1:
        largos = [s for s in segmentos if "forma breve" not in s[0]]
        segmentos = largos or segmentos[:1]
    if not segmentos:
        raise FuenteError("No encuentro el evangelio en las lecturas del día")

    todos: list[Bloque] = []
    referencias: list[str] = []
    for k, (_, seg) in enumerate(segmentos):
        if k:  # varios evangelios (p. ej. misas distintas): separador visible
            todos.append(Bloque(lineas=[[Trozo("* * *")]], clase="nota"))
        referencia = ""
        for b in seg:
            cuerpo: list = []

            def soltar():
                if cuerpo:
                    todos.append(Bloque(lineas=list(cuerpo)))
                    cuerpo.clear()

            for linea in b.lineas:
                t = normal(texto_linea(linea))
                if _ETIQUETA_EVANGELIO.match(t) or _SOBRANTE.match(t):
                    continue  # «EVANGELIO», «Forma larga y forma breve»…
                if _REFERENCIA_EVANGELIO.match(t):
                    soltar()
                    if referencia and t == normal(referencia):
                        continue  # referencia repetida
                    referencia = referencia or texto_linea(linea)
                    todos.append(Bloque(lineas=[linea], clase="ref"))
                elif not referencia:
                    soltar()  # lo que va antes de la referencia es el título
                    todos.append(Bloque(lineas=[linea], clase="titulo"))
                else:
                    cuerpo.append(linea)
            soltar()
        if not referencia:
            raise FuenteError("No encuentro la referencia del evangelio («Lectura del santo Evangelio…»)")
        referencias.append(referencia)

    if len(texto_plano(todos)) < 250:
        raise FuenteError("El texto del evangelio es demasiado corto")
    return todos, referencias
