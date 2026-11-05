# Liturgia diaria en el Kindle

Cada madrugada, este repositorio prepara un libro (EPUB) con **Laudes, Sexta, Vísperas, Completas y el Evangelio del día** y lo envía a tu Kindle. Cuando lo enciendas por la mañana, ya lo tendrás en tu biblioteca.

- **Horas:** [Salmodiando](https://salmodiando.es), con los textos de la Liturgia de las Horas de España. Para Sexta usa el salterio del día, que es lo indicado cuando se reza una sola hora menor.
- **Evangelio:** [Oración y Liturgia](https://oracionyliturgia.archimadrid.org), de la Archidiócesis de Madrid (leccionario de España).
- **Horario:** hacia las 04:17 (invierno) o las 05:17 (verano), hora de España. Si ese envío falla, hay un segundo intento una hora y media después. Si ya se envió, el segundo intento no hace nada, así que nunca recibirás dos copias.
- **Comprobaciones:** antes de meter algo en el libro se comprueba que la página es de la fecha correcta y que la hora tiene todas sus partes. Si algo falla, el libro llega igualmente con lo que sí se pudo preparar, con un aviso en la primera página, y GitHub te manda un correo.

---

## Instalación (unos 10 minutos, una sola vez)

### 1. Contraseña de aplicación de Gmail

El libro sale desde tu Gmail. Google no deja que un programa use tu contraseña normal, así que hay que crear una «contraseña de aplicación»:

1. Activa la **verificación en dos pasos** en tu cuenta de Google, si no la tienes: <https://myaccount.google.com/signinoptions/twosv>
2. Entra en <https://myaccount.google.com/apppasswords>, escribe un nombre (por ejemplo `Kindle liturgia`) y pulsa **Crear**.
3. Copia la contraseña de 16 letras que aparece. Solo se muestra una vez.

### 2. Autorizar tu Gmail en Amazon

1. Entra en Amazon → **Cuenta → Gestionar contenido y dispositivos → Preferencias → Configuración de documentos personales**.
2. Apunta tu **dirección de correo electrónico de Enviar a Kindle** (termina en `@kindle.com`).
3. En **Lista de direcciones de correo electrónico de documentos personales aprobadas**, añade tu Gmail.

### 3. Guardar los datos como «secretos» en GitHub

En este repositorio: **Settings → Secrets and variables → Actions → New repository secret**. Crea estos tres:

| Nombre | Valor |
|---|---|
| `KINDLE_EMAIL` | tu dirección `…@kindle.com` |
| `SMTP_USER` | tu Gmail completo |
| `SMTP_PASSWORD` | la contraseña de aplicación de 16 letras |

Los secretos están cifrados: nadie puede verlos, tampoco desde el código.

### 4. Primera prueba

**Actions → Liturgia diaria al Kindle → Run workflow → Run workflow**. En uno o dos minutos debería aparecer una marca verde ✅. Con el Kindle conectado a la wifi, el libro llega en pocos minutos y aparece en tu biblioteca como «Liturgia · …».

Ya está. Desde ahora llegará solo cada día.

---

## Uso diario y opciones

- **Otro día a mano** (por ejemplo, mañana o una fiesta): *Run workflow* y escribe la fecha `AAAA-MM-DD`.
- **Descargar el EPUB** sin esperar al Kindle: abre cualquier ejecución en *Actions* y baja el archivo del apartado *Artifacts* (se guarda 14 días).
- **Cambiar qué horas y en qué orden**: en **Settings → Secrets and variables → Actions → Variables**, crea la variable `ORDEN`. Por ejemplo: `laudes,evangelio,sexta,visperas,completas`. También admite `oficio`, `tercia` y `nona`.
- **Otro correo que no sea Gmail**: añade los secretos `SMTP_HOST` y `SMTP_PORT` (por ejemplo, Outlook: `smtp-mail.outlook.com` y `587`).
- **Si algo falla**, GitHub te envía un correo. En la ejecución, el resumen explica qué parte falló y por qué.

## Para quien quiera tocar el código

```
python generar.py --fecha 2026-12-25 --no-enviar   # crea el EPUB en ./salida
python pruebas/test_sin_red.py                      # pruebas sin conexión
```

El flujo **Prueba (sin enviar)** genera varias fechas difíciles (Navidad, Ramos, Viernes Santo…) y guarda los libros y las páginas descargadas en la rama `resultados`.

La portada usa la tipografía EB Garamond (licencia SIL OFL, en `liturgia/tipografia/`).
