"""Convierte HTML de cualquier origen en bloques limpios y los vuelve a
maquetar como XHTML sencillo, pensado para la pantalla de tinta electrónica.

No depende de las clases CSS de cada web: recorre el árbol del documento,
conserva solo lo que importa (párrafos, saltos de verso, cursivas, negritas y
rúbricas en rojo) y después reconoce por el propio texto las partes de la
oración (Himno, Salmodia, antífonas, V./R., etc.).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from html import escape

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

# Etiquetas cuyo contenido nunca forma parte de la oración.
DESCARTAR = {
    "script", "style", "noscript", "svg", "iframe", "form", "button", "input",
    "select", "textarea", "nav", "footer", "img", "picture", "video", "audio",
    "canvas", "template", "head", "meta", "link", "object", "embed", "dialog",
}

BLOQUE = {
    "p", "div", "section", "article", "main", "aside", "header", "li", "ul",
    "ol", "blockquote", "table", "tbody", "thead", "tr", "td", "th", "center",
    "dl", "dd", "dt", "figure", "figcaption", "address", "pre", "hr",
    "h1", "h2", "h3", "h4", "h5", "h6",
}
TITULOS = {"h1", "h2", "h3", "h4", "h5", "h6"}
CURSIVA = {"em", "i", "cite", "var"}
NEGRITA = {"strong", "b"}

_ROJO = re.compile(
    r"#(?:f00|ff0000|c00|cc0000|d00|dd0000|e00|b00|a00|900|800|8b0000|b22222|"
    r"c0392b|ce2029|cf0000|d32f2f|c62828|b71c1c|990000|aa0000|bb0000|ee0000)\b"
    r"|\bred\b|\brgb\(\s*(?:1[3-9]\d|2\d\d)\s*,\s*(?:\d|[1-5]\d)\s*,\s*(?:\d|[1-5]\d)\s*\)",
    re.I,
)
_CLASE_RUBRICA = re.compile(r"rubri|rojo|\bred\b|roja|rubrica|rubric", re.I)


def es_rubrica(tag: Tag) -> bool:
    """¿Este elemento marca texto en rojo (rúbrica litúrgica)?"""
    color = tag.get("color") or ""
    estilo = tag.get("style") or ""
    clases = " ".join(tag.get("class") or [])
    return bool(_ROJO.search(color) or _ROJO.search(estilo) or _CLASE_RUBRICA.search(clases))


# --------------------------------------------------------------------------
# Paso 1: HTML -> lista de bloques (cada bloque, lista de líneas con formato)
# --------------------------------------------------------------------------

@dataclass
class Trozo:
    texto: str
    cursiva: bool = False
    negrita: bool = False
    rubrica: bool = False


@dataclass
class Bloque:
    lineas: list[list[Trozo]] = field(default_factory=lambda: [[]])
    titulo: bool = False
    clase: str = ""  # «salmo», «ref», «nota»… cuando la web lo indica

    def texto(self) -> str:
        return "\n".join(texto_linea(l) for l in self.lineas).strip()


def texto_linea(linea: list[Trozo]) -> str:
    return re.sub(r"\s+", " ", "".join(t.texto for t in linea)).strip()


class _Lector:
    def __init__(self):
        self.bloques: list[Bloque] = []
        self.actual = Bloque()
        self.br_seguidos = 0

    def cerrar(self, titulo: bool = False):
        b = self.actual
        b.lineas = [l for l in (_recortar(l) for l in b.lineas) if l]
        if b.lineas:
            b.titulo = b.titulo or titulo
            self.bloques.append(b)
        self.actual = Bloque()
        self.br_seguidos = 0

    def salto(self):
        self.br_seguidos += 1
        if self.br_seguidos >= 2:
            self.cerrar()
        else:
            self.actual.lineas.append([])

    def texto(self, s: str, estilo: tuple[bool, bool, bool]):
        s = s.replace("\r", " ").replace("\n", " ").replace("\t", " ")
        s = re.sub(r"[ \xa0\u2009\u202f]+", " ", s.replace("\xa0", " "))
        if not s.strip():
            if self.actual.lineas[-1] and not self.actual.lineas[-1][-1].texto.endswith(" "):
                self.actual.lineas[-1].append(Trozo(" ", *estilo))
            return
        self.br_seguidos = 0
        self.actual.lineas[-1].append(Trozo(s, *estilo))

    def recorrer(self, nodo, cursiva=False, negrita=False, rubrica=False):
        for hijo in list(nodo.children):
            if isinstance(hijo, Comment):
                continue
            if isinstance(hijo, NavigableString):
                self.texto(str(hijo), (cursiva, negrita, rubrica))
                continue
            if not isinstance(hijo, Tag):
                continue
            nombre = hijo.name.lower()
            if nombre in DESCARTAR or _oculto(hijo):
                continue
            if nombre == "br":
                self.salto()
                continue
            c = cursiva or nombre in CURSIVA
            n = negrita or nombre in NEGRITA
            r = rubrica or es_rubrica(hijo)
            if nombre in BLOQUE:
                es_titulo = nombre in TITULOS or hijo.get("role") == "heading"
                self.cerrar()
                self.actual.clase = _clase_origen(hijo)
                self.recorrer(hijo, c, n or es_titulo, r)
                self.cerrar(titulo=es_titulo)
            else:
                self.recorrer(hijo, c, n, r)


# Clases de la web que ya dicen qué es cada bloque.
CLASES_ORIGEN = {
    "psalm-ref": "salmo",
    "psalm-title": "salmo",
    "ref": "ref",
    "rubric-note": "nota",
}


def _clase_origen(tag: Tag) -> str:
    for c in tag.get("class") or []:
        if c in CLASES_ORIGEN:
            return CLASES_ORIGEN[c]
    return ""


def _oculto(tag: Tag) -> bool:
    estilo = (tag.get("style") or "").replace(" ", "").lower()
    return (
        "display:none" in estilo
        or "visibility:hidden" in estilo
        or tag.has_attr("hidden")
        or tag.get("aria-hidden") == "true"
    )


def _recortar(linea: list[Trozo]) -> list[Trozo]:
    """Quita espacios sobrantes al principio y al final de una línea."""
    linea = [t for t in linea if t.texto]
    while linea and not linea[0].texto.strip():
        linea.pop(0)
    while linea and not linea[-1].texto.strip():
        linea.pop()
    if not linea:
        return []
    linea[0] = Trozo(linea[0].texto.lstrip(), linea[0].cursiva, linea[0].negrita, linea[0].rubrica)
    linea[-1] = Trozo(linea[-1].texto.rstrip(), linea[-1].cursiva, linea[-1].negrita, linea[-1].rubrica)
    return linea


def html_a_bloques(fragmento) -> list[Bloque]:
    """Acepta HTML (str) o un nodo de BeautifulSoup y devuelve sus bloques."""
    if isinstance(fragmento, str):
        fragmento = BeautifulSoup(fragmento, "lxml")
    lector = _Lector()
    if isinstance(fragmento, Tag) and fragmento.name in BLOQUE:
        lector.recorrer(fragmento)
    else:
        lector.recorrer(fragmento)
    lector.cerrar()
    return lector.bloques


# --------------------------------------------------------------------------
# Paso 2: reconocer la estructura litúrgica y escribir XHTML
# --------------------------------------------------------------------------

def sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def normal(s: str) -> str:
    return re.sub(r"\s+", " ", sin_tildes(s).lower()).strip()


ETIQUETAS_SECCION = [
    "invocacion inicial", "invitatorio", "himno", "salmodia", "lectura breve",
    "lectura biblica", "responsorio breve", "responsorio", "cantico evangelico",
    "preces", "padre nuestro", "oracion", "conclusion", "examen de conciencia",
    "acto penitencial", "antifona final", "antifona de la santisima virgen",
    "antifona mariana", "antifona a la virgen", "bendicion", "despedida",
    "salmo invitatorio", "lectura", "evangelio", "primera lectura",
    "segunda lectura", "salmo responsorial", "aleluya", "versiculo",
]
_RE_SECCION = re.compile(
    r"^(?:" + "|".join(re.escape(e) for e in sorted(ETIQUETAS_SECCION, key=len, reverse=True)) + r")\b"
)
_RE_TITULO_SALMO = re.compile(
    r"^(?:salmo|cantico|cántico|benedictus|magnificat|nunc dimittis|te deum)\b", re.I
)
# «Ant.», «Ant. 1», «Ant 2.», pero nunca palabras como «Antes».
_RE_ANTIFONA = re.compile(r"^(ant\.(?:\s*\d+\.?)?|ant\s+\d+\.?)\s*", re.I)
_RE_VR = re.compile(r"^((?:V|R|℣|℟)\s*[\./:]|℣|℟)\s*")
_RE_ASTERISCO = re.compile(r"^(\*|†)\s*")


def clasificar(b: Bloque) -> str:
    if b.clase == "salmo" and len(b.lineas) == 1:
        return "titulo-salmo"
    if b.clase in ("ref", "nota", "titulo"):
        return b.clase
    t = b.texto()
    n = normal(t)
    una_linea = len(b.lineas) == 1
    if una_linea and len(t) <= 90 and _RE_SECCION.match(n):
        # "LECTURA BREVE   1Co 13, 8-9.13" o "Himno" o "Oración".
        return "seccion"
    if una_linea and len(t) <= 140 and _RE_TITULO_SALMO.match(t) and (
        b.titulo or all(tr.rubrica or tr.negrita for tr in b.lineas[0] if tr.texto.strip())
        or re.match(r"^(salmo|cántico|cantico)\s+[\dIVXLC]", t, re.I)
    ):
        return "titulo-salmo"
    if _RE_ANTIFONA.match(t):
        return "antifona"
    if b.titulo and una_linea and len(t) <= 90:
        return "seccion"
    return "texto"


def _trozo_xhtml(t: Trozo) -> str:
    s = escape(t.texto, quote=False)
    if t.cursiva:
        s = f"<em>{s}</em>"
    if t.negrita:
        s = f"<strong>{s}</strong>"
    if t.rubrica:
        s = f'<span class="r">{s}</span>'
    return s


def _linea_xhtml(linea: list[Trozo], quitar_negrita=False) -> str:
    """Convierte una línea a XHTML marcando en rojo V./R./Ant. del comienzo."""
    if quitar_negrita:
        linea = [Trozo(t.texto, t.cursiva, False, t.rubrica) for t in linea]
    plano = texto_linea(linea)
    for patron in (_RE_VR, _RE_ANTIFONA, _RE_ASTERISCO):
        m = patron.match(plano)
        if m:
            etiqueta = m.group(1).strip()
            resto = _quitar_prefijo(linea, m.group(1))
            cuerpo = "".join(_trozo_xhtml(t) for t in resto).strip()
            return f'<span class="r">{escape(etiqueta, quote=False)}</span> {cuerpo}'.rstrip()
    return "".join(_trozo_xhtml(t) for t in linea).strip()


def _quitar_prefijo(linea: list[Trozo], prefijo: str) -> list[Trozo]:
    """Quita de la línea el prefijo dado («V.», «Ant. 1»…), contando solo los
    caracteres visibles para que los espacios entre etiquetas no descuadren."""
    pendientes = len(re.sub(r"\s+", "", prefijo))
    resto: list[Trozo] = []
    for t in linea:
        if pendientes <= 0:
            resto.append(t)
            continue
        txt = t.texto
        i = 0
        while i < len(txt) and pendientes > 0:
            if not txt[i].isspace():
                pendientes -= 1
            i += 1
        if i < len(txt):
            resto.append(Trozo(txt[i:], t.cursiva, t.negrita, t.rubrica))
    while resto and not resto[0].texto.strip():
        resto.pop(0)
    if resto:
        resto[0] = Trozo(resto[0].texto.lstrip(), resto[0].cursiva, resto[0].negrita, resto[0].rubrica)
    return resto


def bloques_a_xhtml(bloques: list[Bloque]) -> str:
    partes = []
    for b in bloques:
        tipo = clasificar(b)
        if tipo == "seccion":
            partes.append(f"<h3>{_linea_xhtml(b.lineas[0], quitar_negrita=True)}</h3>")
        elif tipo in ("ref", "nota", "titulo"):
            lineas = "<br/>\n".join(_linea_xhtml(l) for l in b.lineas)
            partes.append(f'<p class="{tipo}">{lineas}</p>')
        elif tipo == "titulo-salmo":
            partes.append(f'<p class="salmo">{_linea_xhtml(b.lineas[0], quitar_negrita=True)}</p>')
        else:
            clase = ' class="ant"' if tipo == "antifona" else ""
            lineas = "<br/>\n".join(_linea_xhtml(l) for l in b.lineas)
            partes.append(f"<p{clase}>{lineas}</p>")
    return "\n".join(partes)


def texto_plano(bloques: list[Bloque]) -> str:
    return "\n\n".join(b.texto() for b in bloques)
