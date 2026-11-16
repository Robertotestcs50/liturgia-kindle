"""Pruebas sin conexión: python -m pytest pruebas/  (o python pruebas/test_sin_red.py)

Usan páginas de ejemplo con la misma forma que las reales, para comprobar que
el recorte, las comprobaciones y la maquetación funcionan.
"""

import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from liturgia import epub, fuentes  # noqa: E402
from liturgia.limpieza import bloques_a_xhtml, texto_plano  # noqa: E402

D = dt.date(2026, 11, 4)

SALMO = "<p>" + "<br>".join(f"Verso número {i} del salmo, que alaba al Señor," for i in range(12)) + "</p>"
PAGINA_HORA = f"""<html><body>
<header><a href="/">Salmodiando</a><a>Abrir la app</a></header>
<nav>Oficio de lectura Laudes Tercia Sexta Nona Vísperas Completas Misa Evangelio Santo</nav>
<main>
<h1>Sexta de hoy</h1>
<p>Miércoles 4 de noviembre de 2026, memoria de San Carlos Borromeo, obispo</p>
<a class="btn">Rezar Sexta en la app</a>
<div class="oracion">
<p><span class="rubrica">V.</span> Dios mío, ven en mi auxilio.<br><span class="rubrica">R.</span> Señor, date prisa en socorrerme.</p>
<p>Gloria al Padre...</p>
<p class="titulo">Himno</p>
<p>Este mundo del hombre, en que él se afana<br>tras la felicidad que tanto ansía,</p>
<p class="titulo">Salmodia</p>
<p>Ant. <em>«El que me sigue no camina en tinieblas», dice el Señor.</em></p>
<p class="titulo">Salmo 118, 105-112: XIV (Nun)</p>
{SALMO}
<p>Ant. <em>«El que me sigue no camina en tinieblas», dice el Señor.</em></p>
<p class="titulo">Salmo 69: Dios mío, ven en mi auxilio</p>
{SALMO}
<p class="titulo">Lectura breve</p><p>1 Co 13, 8-9.13</p><p>El amor no pasa nunca...</p>
<p class="titulo">Responsorio breve</p>
<p>V. Que tu misericordia, Señor, venga sobre nosotros.<br>R. Como lo esperamos de ti.</p>
<p class="titulo">Oración</p>
<p>Dios todopoderoso, que a la mitad de nuestra jornada... Por Jesucristo nuestro Señor.<br>R. Amén.</p>
<p>V. Bendigamos al Señor.<br>R. Demos gracias a Dios.</p>
</div>
<h2>Sobre el rezo de este día</h2><p>Texto explicativo que no es oración.</p>
<a>‹ Día anterior</a><a>Día siguiente ›</a>
</main>
<footer>Aviso legal · Política de privacidad</footer>
</body></html>"""

EVANGELIO = """
<p><strong>Primera lectura</strong></p><p>Lectura de la carta del apóstol san Pablo a los Filipenses 2, 12-18</p>
<p>Queridos hermanos: ...</p><p>Palabra de Dios.</p>
<p><strong>Salmo</strong></p><p>Sal 26, 1. 4. 13-14 R. El Señor es mi luz y mi salvación.</p>
<p><strong>Aleluya</strong></p><p>1 Pe 4, 14 R. Aleluya, aleluya, aleluya. Si os ultrajan...</p>
<p><strong>Evangelio</strong></p>
<p><strong>Todo aquel que no renuncia a todos sus bienes no puede ser discípulo mío</strong></p>
<p>Lectura del santo evangelio según san Lucas 14, 25-33</p>
<p>En aquel tiempo, mucha gente acompañaba a Jesús; él se volvió y les dijo:<br>
«Si alguno viene a mí y no pospone a su padre y a su madre, y a su mujer y a sus hijos,
y a sus hermanos y a sus hermanas, e incluso a sí mismo, no puede ser discípulo mío.
Quien no carga con su cruz y viene en pos de mí, no puede ser discípulo mío.
Así pues, ¿quién de vosotros, si quiere construir una torre, no se sienta primero a calcular
los gastos, a ver si tiene para terminarla?»</p>
<p>Palabra del Señor.</p>
"""


def test_hora_se_recorta_bien():
    bloques = fuentes.procesar_hora(PAGINA_HORA, "sexta", D)
    texto = texto_plano(bloques)
    assert texto.startswith("V. Dios mío, ven en mi auxilio")
    assert "Demos gracias a Dios" in texto
    assert "Sobre el rezo" not in texto and "Texto explicativo" not in texto
    assert "Abrir la app" not in texto and "Día anterior" not in texto
    x = bloques_a_xhtml(bloques)
    assert "<h3>Himno</h3>" in x and "<h3>Oración</h3>" in x
    assert '<p class="ant"><span class="r">Ant.</span> <em>' in x
    assert '<p class="salmo">Salmo 69: Dios mío, ven en mi auxilio</p>' in x


def test_hora_rechaza_otra_fecha():
    try:
        fuentes.procesar_hora(PAGINA_HORA, "sexta", dt.date(2026, 11, 5))
    except fuentes.FuenteError as e:
        assert "5 de noviembre" in str(e)
    else:
        raise AssertionError("debía rechazar una página de otra fecha")


def test_fecha_con_el_formato_nuevo_de_la_web():
    # Desde el 16-11-2026 la web no escribe la fecha: la lleva en data-fecha,
    # en los enlaces de día anterior/siguiente y en el día de la celebración.
    nueva = (PAGINA_HORA
             .replace("<p>Miércoles 4 de noviembre de 2026, memoria de San Carlos Borromeo, obispo</p>",
                      '<section class="day-hero"><div class="celebration">Miércoles de la XXXI semana</div></section>'
                      '<script src="/hoy-pagina.js" data-fecha="2026-11-04"></script>')
             .replace("<a>‹ Día anterior</a><a>Día siguiente ›</a>",
                      '<nav class="hoy-dias"><a href="/sexta-hoy/?fecha=2026-11-03">‹ Día anterior</a>'
                      '<a href="/sexta-hoy/?fecha=2026-11-05">Día siguiente ›</a></nav>'))
    assert "noviembre" not in nueva
    fuentes.procesar_hora(nueva, "sexta", D)
    for otro in (dt.date(2026, 11, 5), dt.date(2026, 11, 11)):  # mañana / mismo día de la semana
        try:
            fuentes.procesar_hora(nueva, "sexta", otro)
        except fuentes.FuenteError:
            continue
        raise AssertionError(f"debía rechazar {otro}")
    sin_fecha = nueva.replace('data-fecha="2026-11-04"', "").replace("Miércoles de la", "De la")
    sin_fecha = re.sub(r'<nav class="hoy-dias">.*?</nav>', "", sin_fecha)
    try:
        fuentes.procesar_hora(sin_fecha, "sexta", D)
    except fuentes.FuenteError as e:
        assert "no indica de qué día" in str(e)
    else:
        raise AssertionError("sin ninguna fecha no debía darse por buena")


def test_hora_rechaza_texto_incompleto():
    roto = PAGINA_HORA.replace("Lectura breve", "Otra cosa")
    try:
        fuentes.procesar_hora(roto, "sexta", D)
    except fuentes.FuenteError as e:
        assert "lectura breve" in str(e)
    else:
        raise AssertionError("debía rechazar una hora sin lectura breve")


def test_evangelio():
    bloques, refs = fuentes.procesar_evangelio(EVANGELIO)
    texto = texto_plano(bloques)
    assert texto.startswith("Todo aquel que no renuncia")
    assert texto.rstrip().endswith("Palabra del Señor.")
    assert "Filipenses" not in texto and "Aleluya" not in texto
    assert refs == ["Lectura del santo evangelio según san Lucas 14, 25-33"]


def test_varios_evangelios():
    doble = EVANGELIO + EVANGELIO.replace("Lucas 14, 25-33", "Juan 1, 1-18")
    bloques, refs = fuentes.procesar_evangelio(doble)
    assert len(refs) == 2 and "* * *" in texto_plano(bloques)


LECTURAS = """
<p><span class="Tit_Negro_Cur">PRIMERA LECTURA</span><br /> <span class="Tit_Lectura">Todo eso que para mí era ganancia</span><br /><span class="Tit_Negro_Normal">Lectura de la carta del apóstol san Pablo a los Filipenses 3, 3-8a</span></p>
<p>Hermanos: nosotros somos los verdaderos circuncisos, que damos culto según el Espíritu de Dios,
y que ponemos nuestra gloria en Cristo Jesús sin confiar en la carne, aunque yo tendría motivos
para confiar en ella. Todo eso que para mí era ganancia, lo consideré pérdida a causa de Cristo.</p>
<p><span class="Tit_Negro_Normal">Palabra de Dios.</p>
<p></span></p>
<p><span class="Tit_Lectura">Sal 104, 2-3. 4-5. 6-7</span><br /><span class="Tit_Negro_Normal">R. Que se alegren los que buscan al Señor.</span></p>
<p>Cantadle al son de instrumentos,<br />hablad de sus maravillas. <br />Gloriaos de su nombre santo, <br />que se alegren los que buscan al Señor. R.</p>
<p><span class="Tit_Lectura">Jn 6, 39</span><br /><span class="Tit_Negro_Normal">R. Aleluya, aleluya, aleluya.</span></p>
<p>Venid a mí todos los que estáis cansados y agobiados, y yo os aliviaré. R. </p>
<p><span class="Tit_Negro_Cur">EVANGELIO</span><br /> <span class="Tit_Lectura">Habrá más alegría en el cielo</span><br /><span class="Tit_Negro_Normal">Lectura del santo Evangelio según san Lucas 15, 1-10</span></p>
<p>En aquel tiempo, solían acercarse a Jesús todos los publicanos y los pecadores a escucharlo.
Y los fariseos y los escribas murmuraban entre ellos.</p>
<p>Entonces Pedro se acordó de la palabra del Señor</p>
<p>«Os digo que así también habrá más alegría en el cielo por un solo pecador que se convierta
que por noventa y nueve justos que no necesitan convertirse».</p>
<p>Palabra del Señor.</p>
<p>Comentario que ya no es parte de las lecturas.</p>
"""


def test_lecturas_completas():
    bloques, apartados = fuentes.procesar_lecturas(LECTURAS)
    assert [t for _, t in apartados] == [
        "Primera lectura", "Salmo responsorial", "Aleluya", "Evangelio"]
    texto = texto_plano(bloques)
    # No corta el Evangelio por «la palabra del Señor» en mitad del texto.
    assert "noventa y nueve justos" in texto
    assert texto.rstrip().endswith("Palabra del Señor.")
    assert "Comentario" not in texto
    x = bloques_a_xhtml(bloques)
    assert '<h3 id="l1">Primera lectura</h3>' in x
    assert '<p class="ref">Lectura del santo Evangelio según san Lucas 15, 1-10</p>' in x
    assert 'buscan al Señor. <span class="r">R.</span>' in x  # «R.» final en rojo


def test_lecturas_sin_formato_dan_el_evangelio():
    # Si la web cambiara y no hubiera etiquetas, no se pierde el Evangelio.
    try:
        fuentes.procesar_lecturas(EVANGELIO)
    except fuentes.FuenteError:
        pass
    else:
        raise AssertionError("sin etiquetas debía fallar para usar el plan B")
    bloques, refs = fuentes.procesar_evangelio(EVANGELIO)
    assert refs and "Palabra del Señor" in texto_plano(bloques)


def test_libro_completo(tmp_path=Path("/tmp")):
    secs = [
        fuentes.Seccion("sexta", "Sexta", fuentes.procesar_hora(PAGINA_HORA, "sexta", D), "https://x"),
        fuentes.Seccion("lecturas", "Lecturas del día", fuentes.procesar_lecturas(LECTURAS)[0], "https://y",
                        apartados=fuentes.procesar_lecturas(LECTURAS)[1]),
    ]
    ruta = epub.construir(D, "San Carlos Borromeo", secs, ["aviso de prueba"], Path(tmp_path) / "t.epub")
    import generar
    generar.comprobar_epub(ruta)


def test_decisiones_de_envio():
    """Cuándo se envía según la hora, si el libro está completo y lo ya enviado."""
    import os
    import tempfile
    import generar

    enviados = []
    seccion = fuentes.Seccion("sexta", "Sexta", fuentes.procesar_hora(PAGINA_HORA, "sexta", D), "x")

    def probar(hora, completo, estado_previo, evento="schedule"):
        with tempfile.TemporaryDirectory() as tmp:
            generar.ESTADO = Path(tmp) / "estado" / "ultimo_envio.txt"
            if estado_previo:
                generar.ESTADO.parent.mkdir()
                generar.ESTADO.write_text(estado_previo + "\n")
            generar.ahora_en_espana = lambda: dt.datetime(2026, 11, 4, *hora)
            generar.hoy_en_espana = lambda: D

            def hora_falsa(clave, d):
                if not completo:
                    raise fuentes.FuenteError("web caída")
                return seccion
            fuentes.hora = hora_falsa
            fuentes.lecturas = lambda d: (seccion, "San Carlos", "")
            generar.enviar_a_kindle = lambda ruta, asunto: enviados.append(asunto) or "x@kindle.com"
            os.environ.update(EVENTO=evento, ORDEN="sexta,lecturas", ENVIAR="true")
            antes = len(enviados)
            sys.argv = ["generar.py", "--salida", tmp]
            codigo = generar.main()
            estado = generar.ESTADO.read_text().strip() if generar.ESTADO.exists() else ""
            return len(enviados) - antes, codigo, estado

    hoy = D.isoformat()
    # (hora, completo, estado previo) -> (envíos, estado final)
    casos = [
        ((0, 37), True, "", 1, hoy),                        # completo a las 00:37: se envía
        ((1, 17), True, hoy, 0, hoy),                       # ya enviado: nada
        ((0, 37), False, "", 0, ""),                        # incompleto antes de 2:20: espera
        ((2, 27), False, "", 1, hoy + " parcial"),          # incompleto a las 2:27: se envía
        ((4, 47), False, hoy + " parcial", 0, hoy + " parcial"),  # no repite el incompleto
        ((4, 47), True, hoy + " parcial", 1, hoy),          # rescate: llega el completo
        ((6, 47), True, hoy, 0, hoy),                       # y no se repite
        ((1, 0), True, "2026-11-03", 1, hoy),               # estado de ayer no cuenta
    ]
    for hora, completo, previo, envios_esperados, estado_esperado in casos:
        envios, _, estado = probar(hora, completo, previo)
        assert (envios, estado) == (envios_esperados, estado_esperado), (hora, completo, previo, envios, estado)
    # A mano siempre se envía, aunque ya se hubiera enviado.
    assert probar((10, 0), True, hoy, evento="workflow_dispatch")[0] == 1


if __name__ == "__main__":
    for nombre, f in list(globals().items()):
        if nombre.startswith("test_"):
            f()
            print("✓", nombre)
