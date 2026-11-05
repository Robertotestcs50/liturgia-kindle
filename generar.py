#!/usr/bin/env python3
"""Genera el libro de la liturgia del día y lo envía al Kindle.

Uso:
    python generar.py                     # hoy (hora de España), y lo envía
    python generar.py --fecha 2026-12-25  # otro día
    python generar.py --no-enviar         # solo crea el EPUB en ./salida

Variables de entorno (en GitHub van como «secretos»):
    KINDLE_EMAIL, SMTP_USER, SMTP_PASSWORD  obligatorias para enviar
    SMTP_HOST (smtp.gmail.com), SMTP_PORT (465), EMAIL_FROM (= SMTP_USER)
    ORDEN   partes y orden del libro (por defecto
            laudes,sexta,visperas,completas,evangelio). También admite
            tercia, nona y oficio.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
import zipfile
from pathlib import Path
from zoneinfo import ZoneInfo

from lxml import etree

from liturgia import epub, fuentes
from liturgia.envio import EnvioError, enviar_a_kindle

RAIZ = Path(__file__).resolve().parent
ESTADO = RAIZ / "estado" / "ultimo_envio.txt"
ORDEN_POR_DEFECTO = "laudes,sexta,visperas,completas,evangelio"


def hoy_en_espana() -> dt.date:
    return dt.datetime.now(ZoneInfo("Europe/Madrid")).date()


def resumen(texto: str):
    """Escribe en el resumen de la ejecución de GitHub (si existe)."""
    print(texto)
    ruta = os.environ.get("GITHUB_STEP_SUMMARY")
    if ruta:
        with open(ruta, "a", encoding="utf-8") as f:
            f.write(texto + "\n")


def comprobar_epub(ruta: Path):
    """Todo el XHTML/XML del libro debe estar bien formado (si no, Kindle lo rechaza)."""
    with zipfile.ZipFile(ruta) as z:
        nombres = z.namelist()
        if nombres[0] != "mimetype" or z.read("mimetype") != b"application/epub+zip":
            raise RuntimeError("EPUB mal formado: «mimetype» debe ir el primero")
        for n in nombres:
            if n.endswith((".xhtml", ".opf", ".ncx", ".xml")):
                etree.fromstring(z.read(n))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fecha", default=os.environ.get("FECHA", "").strip(), help="AAAA-MM-DD")
    ap.add_argument("--no-enviar", action="store_true")
    ap.add_argument("--salida", default=str(RAIZ / "salida"))
    ap.add_argument("--guardar-html", default="", help="carpeta donde guardar las páginas descargadas")
    args = ap.parse_args()

    d = dt.date.fromisoformat(args.fecha) if args.fecha else hoy_en_espana()
    enviar = not args.no_enviar and os.environ.get("ENVIAR", "true").lower() != "false"
    programado = os.environ.get("EVENTO") == "schedule"
    if args.guardar_html:
        fuentes.GUARDAR_EN = args.guardar_html

    if programado and ESTADO.exists() and ESTADO.read_text().strip() == d.isoformat():
        resumen(f"El libro del {d.isoformat()} ya se envió hoy. Nada que hacer.")
        return 0

    orden = [c.strip().lower() for c in (os.environ.get("ORDEN") or ORDEN_POR_DEFECTO).split(",") if c.strip()]
    validas = set(fuentes.HORAS) | {"evangelio"}
    if any(c not in validas for c in orden):
        resumen(f"ORDEN contiene partes desconocidas: {orden}. Válidas: {sorted(validas)}")
        return 1

    resumen(f"## Liturgia del {fuentes.fecha_larga(d)}\n")
    secciones, avisos = [], []
    celebracion = ""
    for clave in orden:
        try:
            if clave == "evangelio":
                sec, celebracion = fuentes.evangelio(d)
            else:
                sec = fuentes.hora(clave, d)
            secciones.append(sec)
            resumen(f"- ✅ {sec.titulo} ({len(fuentes.texto_plano(sec.bloques))} caracteres)")
        except Exception as e:  # una parte que falla no debe impedir recibir las demás
            nombre = "Evangelio" if clave == "evangelio" else fuentes.HORAS[clave][0]
            avisos.append(f"Hoy no se pudo preparar {nombre}: {e}")
            resumen(f"- ❌ {nombre}: {e}")

    if not secciones:
        resumen("\nNo se pudo descargar nada; no se envía ningún libro.")
        return 1

    ruta = Path(args.salida) / epub.nombre_archivo(d)
    epub.construir(d, celebracion, secciones, avisos, ruta)
    comprobar_epub(ruta)
    resumen(f"\nLibro creado: `{ruta.name}` ({ruta.stat().st_size // 1024} KB)")

    if enviar:
        try:
            destino = enviar_a_kindle(ruta, f"Liturgia {d.isoformat()}")
        except EnvioError as e:
            resumen(f"\n❌ Envío fallido: {e}")
            return 1
        resumen(f"📨 Enviado a {destino[:3]}…@{destino.split('@')[-1]}")
        if not avisos:
            ESTADO.parent.mkdir(exist_ok=True)
            ESTADO.write_text(d.isoformat() + "\n")

    # Si faltó alguna parte, la ejecución termina en error para que GitHub te avise por correo.
    return 2 if avisos else 0


if __name__ == "__main__":
    sys.exit(main())
