# ✝ Liturgia diaria en tu Kindle

> *«Lámpara es tu palabra para mis pasos, luz en mi sendero.»* (Sal 119, 105)

Este proyecto existe para una cosa sencilla: que cada mañana, al encender tu Kindle, **ya te esté esperando la oración del día**. No hace falta buscar nada, abrir el móvil ni conectarse a internet para rezar. Solo coges el Kindle y rezas.

Cada madrugada se prepara un pequeño libro con:

- **Laudes**, la oración de la mañana
- **Sexta**, la oración del mediodía
- **Vísperas**, la oración de la tarde
- **Completas**, la oración antes de dormir
- **Las lecturas de la misa del día**: primera lectura, salmo, segunda lectura (domingos y solemnidades), aleluya y Evangelio

Todo con los **textos oficiales de España** y llega solo a tu Kindle cada día, también en vacaciones y en los días en que se te olvida.

Ponerlo en marcha lleva unos **20 minutos, una sola vez**. No hace falta saber de informática: esta guía te acompaña paso a paso.

---

## 📖 Qué vas a recibir

Cada día aparece en la biblioteca de tu Kindle un libro llamado, por ejemplo, **«Liturgia · Domingo 15 de noviembre de 2026»**.

- **Una portada** con la fecha y la celebración del día.
- **Una primera página** con la celebración (por ejemplo, *«Domingo de la 33ª semana de Tiempo Ordinario»*), la semana del salterio y un índice para saltar a cada oración.
- **Cada hora completa**: himno, salmodia con sus antífonas, lectura breve, responsorio, cántico evangélico, preces, Padre nuestro y oración.
- **Las rúbricas en rojo**: V., R., Ant. y los títulos de los salmos. En un Kindle en blanco y negro se ven en gris oscuro y en negrita.
- **Las lecturas de la misa** con su título y su cita. Desde el índice o desde el menú **«Ir a»** del Kindle puedes saltar directamente a la Primera lectura, al Salmo o al Evangelio.

El libro respeta el tamaño de letra y la tipografía que elijas en tu Kindle.

---

## 🧰 Qué necesitas

- **Un Kindle** (cualquier modelo) **registrado con tu cuenta de Amazon** y con wifi.
- **Una cuenta de Gmail.** Desde ahí se envía el libro a tu Kindle.
- **Una cuenta de GitHub**, gratuita (github.com). Es el sitio donde vive este programa y donde se ejecuta cada madrugada, sin que tu ordenador tenga que estar encendido.

> 💡 **¿El Kindle está registrado a nombre de otra persona?** En el Kindle, ve a *Configuración → Mi cuenta → Anular el registro del dispositivo* y después regístralo con tu cuenta. No hace falta la contraseña de la otra persona. Avísala antes: sus libros desaparecerán de ese Kindle, aunque los conserva en su cuenta.

---

## 🛠️ Puesta en marcha (una sola vez)

### Paso 0 · Tu propia copia del proyecto

Si alguien te ha compartido este proyecto, necesitas tu propia copia en tu cuenta de GitHub:

1. Entra en la página del proyecto en GitHub.
2. Pulsa el botón verde **«Use this template» → «Create a new repository»**. Ese botón solo aparece si quien te lo comparte lo ha marcado como plantilla (*Settings → Template repository*). Si no aparece, usa **«Fork»**.
3. Ponle un nombre, por ejemplo `liturgia-kindle`, marca **Private** y pulsa **Create**.
4. Si usaste *Fork*, entra en la pestaña **Actions** de tu copia y pulsa el botón que permite activar los flujos de trabajo (*«I understand my workflows, go ahead and enable them»*).

> Si ya tienes tu repositorio, como quien montó este, sáltate este paso.

### Paso 1 · La dirección de correo de tu Kindle

Cada Kindle tiene una dirección de correo propia, terminada en `@kindle.com`. Todo lo que se envía a esa dirección aparece en su biblioteca.

- **En el Kindle:** *Configuración → Mi cuenta → E-mail de Enviar a Kindle*.
- **O en la web:** entra en **amazon.es/myk → Preferencias → Configuración de documentos personales**.

✍️ Apúntala con cuidado: la necesitarás en el paso 4.

### Paso 2 · Decirle a Amazon que confíe en tu Gmail

Para proteger tu Kindle, Amazon solo acepta documentos de remitentes que tú hayas autorizado.

1. Entra en **amazon.es/myk** y abre la pestaña **Preferencias** (*Preferences*).
2. Baja hasta **Configuración de documentos personales** (*Personal Document Settings*) y haz clic en el título para desplegarlo.
3. En **Lista de direcciones de correo electrónico de documentos personales aprobadas** (*Approved Personal Document E-mail List*), pulsa **Añadir una nueva dirección** (*Add a new approved e-mail address*).
4. Escribe tu Gmail y confirma.

### Paso 3 · Una contraseña especial de Gmail

Google no permite que un programa use tu contraseña de siempre. Hay que crear una **contraseña de aplicación**, que solo sirve para esto y puedes borrar cuando quieras.

1. Si no la tienes ya, activa la **verificación en dos pasos**: <https://myaccount.google.com/signinoptions/twosv>
2. Entra en <https://myaccount.google.com/apppasswords>.
3. Escribe un nombre, por ejemplo `Kindle liturgia`, y pulsa **Crear**.
4. Copia las **16 letras** que aparecen. Solo se muestran una vez.

### Paso 4 · Guardar tus datos en GitHub (de forma segura)

En tu repositorio de GitHub: **Settings → Secrets and variables → Actions → New repository secret**.

Crea estos **tres secretos**, uno a uno, con el nombre exactamente así, en mayúsculas:

| Nombre | Qué escribir |
|---|---|
| `KINDLE_EMAIL` | La dirección de tu Kindle (paso 1), terminada en `@kindle.com` |
| `SMTP_USER` | Tu Gmail completo, por ejemplo `nombre@gmail.com` |
| `SMTP_PASSWORD` | Las 16 letras del paso 3 (con espacios o sin ellos, da igual) |

🔒 Los secretos se guardan cifrados. Nadie puede verlos: ni otras personas ni el propio programa los muestra nunca.

### Paso 5 · ¡La primera prueba!

1. En tu repositorio, abre la pestaña **Actions**.
2. A la izquierda, elige **«Liturgia diaria al Kindle»**.
3. Pulsa **«Run workflow»** y luego el botón verde **«Run workflow»**.
4. En uno o dos minutos aparecerá una **marca verde ✅**.
5. Con el Kindle conectado a la wifi, el libro llegará en unos minutos. Si tarda, en el Kindle ve a *Configuración → Sincronizar*.

🎉 **Ya está.** Desde mañana llegará solo, cada día.

---

## 🌅 En el día a día

**No tienes que hacer nada.** Cada noche, a partir de las **00:37** (hora de España, también en verano), el libro se prepara y se envía. Está en tu Kindle **antes de las 3 de la mañana**.

- **Si algo falla, lo vuelve a intentar** a la 1:17, a la 1:57 y a las 2:27.
- **Hasta las 2:20 solo se envía el libro completo.** Si a las 2:27 aún falta alguna parte, te llega igualmente con lo que sí se pudo preparar y un aviso en la primera página, para que tengas algo con lo que rezar al levantarte. Además, GitHub te manda un correo.
- **Intentos de rescate a las 4:47 y a las 6:47.** Si solo pudo salir el libro incompleto, en cuanto esté el completo te llega también.
- **Nunca recibirás dos copias iguales** del envío automático. Si el libro completo ya salió, los demás intentos no hacen nada.
- **Deja el wifi del Kindle activado.** Cuando lo enciendas, el libro se descarga en unos segundos. Si no aparece, ve a *Configuración → Sincronizar*.
- **Para reenviar el libro de hoy**, por ejemplo si lo borraste: *Actions → Liturgia diaria al Kindle → Run workflow*.
- **Para descargar el libro sin el Kindle:** abre cualquier ejecución en *Actions* y bájalo del apartado **Artifacts**. Se guarda 14 días.

### Consejos para leer en el Kindle

- **Letra más grande:** toca la parte de arriba de la pantalla, pulsa **«Aa»** y ajusta el tamaño. La **negrita** hace el texto más nítido.
- **Quitar el «tiempo restante» y el porcentaje:** en **«Aa» → Más** (o *Diseño*), desactiva **Progreso de lectura**.
- **Ir directo a una oración o a una lectura:** abre el menú y usa **«Ir a»**.
- **Borrar libros de días anteriores:** mantén el dedo sobre el libro y elige **Quitar del dispositivo**. Cada libro ocupa unos 50 KB, así que tampoco hay prisa.

---

## 🎨 Personalizar

### Elegir qué oraciones y en qué orden

En tu repositorio: **Settings → Secrets and variables → Actions → pestaña Variables → New repository variable**.

- **Nombre:** `ORDEN`
- **Valor:** las partes separadas por comas. Por ejemplo:

```
laudes,lecturas,sexta,visperas,completas
```

Puedes usar `oficio` (Oficio de lectura), `laudes`, `tercia`, `sexta`, `nona`, `visperas`, `completas` y `lecturas`.

### Usar otro correo que no sea Gmail

Añade dos secretos más: `SMTP_HOST` y `SMTP_PORT`. Por ejemplo, para Outlook: `smtp-mail.outlook.com` y `587`.

### Cambiar la hora de envío

Está en el archivo `.github/workflows/diario.yml`, en las líneas `cron`, ya en **hora de España** gracias a `timezone: "Europe/Madrid"`. Por ejemplo, `"37 0 * * *"` significa las 00:37. El primer número son los minutos y el segundo, la hora.

No adelantes el primer intento a antes de medianoche: la web de las lecturas publica el día nuevo a las 00:00.

---

## 🩹 Si algo no funciona

| Lo que ves | Qué significa | Qué hacer |
|---|---|---|
| ❌ *«Falta el secreto KINDLE_EMAIL»* (u otro) | Falta uno de los tres secretos o tiene otro nombre | Revisa el paso 4: los nombres van exactos y en mayúsculas |
| ❌ *«El servidor de correo rechazó el usuario o la contraseña»* | Gmail no acepta la contraseña | Usa una **contraseña de aplicación** (paso 3), no la tuya normal. Si dudas, crea otra y actualiza `SMTP_PASSWORD` |
| ❌ *«KINDLE_EMAIL no parece una dirección de Kindle»* | La dirección está mal copiada | Debe terminar en `@kindle.com` |
| ✅ en GitHub, pero el libro no llega | Amazon no reconoce el remitente o el Kindle no ha sincronizado | Revisa el paso 2 (tu Gmail aprobado en la cuenta del **mismo** Kindle), conecta la wifi y pulsa *Sincronizar*. Mira también si Amazon te ha escrito al Gmail |
| Aviso *«La página no corresponde al…»* | La web aún mostraba el día anterior | Nada: se reintenta solo más tarde |
| Aviso *«La página no indica de qué día es»* | La web de las Horas ha cambiado su diseño | Hay que ajustar el programa (`liturgia/fuentes.py`, función `_comprobar_fecha`) |
| Aviso *«Hoy no se pudo preparar…»* | Una web no respondía o ha cambiado | Si se repite varios días, quizá la web ha cambiado de formato y hay que ajustar el programa |
| Dos libros iguales hoy | Lanzaste el envío a mano después del automático | Borra uno: mantén el dedo sobre él y elige *Quitar del dispositivo* |

En cada ejecución de **Actions**, el **resumen** explica qué partes salieron bien (✅) y cuáles no (❌), y por qué.

---

## ❓ Preguntas frecuentes

**¿Cuesta dinero?**
No. Enviar documentos a tu Kindle es gratuito, y GitHub incluye cada mes más tiempo del que este programa necesita: un par de minutos al día.

**¿Necesito tener el ordenador encendido?**
No. Todo funciona en los servidores de GitHub.

**¿Puedo pedir el libro de otro día, por ejemplo de mañana?**
No. La web de la que salen las Horas solo ofrece el día en curso, así que el libro siempre es el de hoy.

**¿Es seguro?**
Tus contraseñas se guardan cifradas como secretos de GitHub y solo se usan para enviar el correo a tu Kindle. La contraseña de aplicación de Gmail puedes borrarla cuando quieras desde tu cuenta de Google. Te recomendamos que tu repositorio sea **privado**.

**¿Puedo tenerlo en dos Kindles, por ejemplo uno para mi madre?**
Lo más sencillo es que cada persona tenga su propia copia (paso 0) con sus propios secretos.

**¿Y si un día no llega?**
Mira en la pestaña **Actions** qué pasó ese día, o lanza el envío a mano con *Run workflow*.

---

## 🙏 De dónde salen los textos

- **Liturgia de las Horas:** [Salmodiando](https://salmodiando.es), con los textos de la Liturgia de las Horas en uso en España.
- **Lecturas de la misa:** [Oración y Liturgia](https://oracionyliturgia.archimadrid.org), de la Archidiócesis de Madrid, con el Leccionario de España.

Este programa recoge los textos de esas webs cada día, con una única visita, para tu **oración personal**, y cita su procedencia al final de cada capítulo. No los publica. Solo guarda una copia, de forma privada en tu repositorio, para poder revisar qué pasó si algo falla. Por respeto a quienes tienen los derechos de estos textos, **mantén tu repositorio privado**. Antes de meter nada en el libro comprueba que la página es del día correcto y que cada oración trae todas sus partes. Así, si algo no cuadra, prefiere avisarte a darte un texto equivocado.

Gracias de corazón a quienes sostienen esas webs y ponen la oración de la Iglesia al alcance de todos.

---

## 🔧 Para quien quiera mirar por dentro

```
generar.py                      Programa principal: descarga, prepara el libro y lo envía
liturgia/fuentes.py             Descarga y comprobación de los textos
liturgia/limpieza.py            Convierte las páginas web en texto limpio para el Kindle
liturgia/epub.py                Construye el libro (EPUB) y su portada
liturgia/envio.py               Envío por correo a tu Kindle
.github/workflows/diario.yml    El envío diario automático
.github/workflows/prueba.yml    Prueba con varias fechas, sin enviar nada
pruebas/                        Pruebas automáticas
```

Para probarlo en tu ordenador (con Python 3.10 o posterior):

```
pip install -r requirements.txt
python generar.py --no-enviar          # crea el libro de hoy en ./salida
python pruebas/test_sin_red.py         # pruebas sin conexión
```

El flujo **Prueba (sin enviar)** genera el libro de hoy y prueba las lecturas de días difíciles (Navidad, Ramos, Viernes Santo, la Vigilia Pascual…). Cada libro se valida con [EPUBCheck](https://www.w3.org/publishing/epubcheck/), el validador oficial de EPUB.

La portada usa la tipografía EB Garamond (licencia SIL OFL, en `liturgia/tipografia/`).

---

<p align="center"><em>Que cada mañana, al encender tu Kindle, te encuentres con Él.</em><br/>Paz y bien. 🕊️</p>
