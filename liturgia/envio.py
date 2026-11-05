"""Envía el EPUB a la dirección «Enviar a Kindle» por correo (SMTP)."""

from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path


class EnvioError(Exception):
    pass


def _var(nombre: str, defecto: str | None = None) -> str:
    v = (os.environ.get(nombre) or "").strip()
    if v:
        return v
    if defecto is not None:
        return defecto
    raise EnvioError(f"Falta el secreto {nombre}. Revisa la guía (paso «Secretos»).")


def enviar_a_kindle(ruta: Path, asunto: str) -> str:
    destino = _var("KINDLE_EMAIL")
    usuario = _var("SMTP_USER")
    clave = _var("SMTP_PASSWORD").replace(" ", "")  # las contraseñas de aplicación de Google llevan espacios
    servidor = _var("SMTP_HOST", "smtp.gmail.com")
    puerto = int(_var("SMTP_PORT", "465"))
    remitente = _var("EMAIL_FROM", usuario)

    if not destino.lower().endswith(("@kindle.com", "@free.kindle.com", "@kindle.cn")):
        raise EnvioError(f"KINDLE_EMAIL no parece una dirección de Kindle: {destino}")

    msg = EmailMessage()
    msg["From"] = remitente
    msg["To"] = destino
    msg["Subject"] = asunto
    msg.set_content("Liturgia del día. Que el Señor te bendiga.\n")
    msg.add_attachment(
        ruta.read_bytes(),
        maintype="application",
        subtype="epub+zip",
        filename=ruta.name,
    )

    contexto = ssl.create_default_context()
    try:
        if puerto == 465:
            with smtplib.SMTP_SSL(servidor, puerto, context=contexto, timeout=60) as s:
                s.login(usuario, clave)
                s.send_message(msg)
        else:
            with smtplib.SMTP(servidor, puerto, timeout=60) as s:
                s.starttls(context=contexto)
                s.login(usuario, clave)
                s.send_message(msg)
    except smtplib.SMTPAuthenticationError as e:
        raise EnvioError(
            "El servidor de correo rechazó el usuario o la contraseña. Con Gmail hace falta "
            "una «contraseña de aplicación» (no tu contraseña normal)."
        ) from e
    except (smtplib.SMTPException, OSError) as e:
        raise EnvioError(f"No se pudo enviar el correo: {e}") from e
    return destino
