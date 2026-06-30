# 🐱 michicator

> *Michicator - micho dedicator* — Un bot que le hice a mi novia Frida para celebrar un mesversario. Este bot le manda canciones que yo le he querido dedicar y también frases bonitas de manera automatizada, pero escritas y escogidas por uno mismo con la intención de que nunca se me pase el detalle del diario que la pueda hacer sentir amada aunque sea un poquito más. ¿Será esta una buena manera nerd para honrar a este regalo que Dios me dio? 🤔

<p align="center">
  <img src="https://i.pinimg.com/736x/96/db/b0/96dbb065a1beafad294f4f0d97756ad6.jpg" width="380" alt="michicator" />
</p>

---

## Hola, Frida 🧡

Si estás leyendo esto es porque Ricardo te compartió este repositorio — o porque eres lo suficientemente curiosa para rastrear de dónde vienen los mensajes que te llegan por Telegram. De cualquier forma, bienvenida.

Este es el código de michicator. Todo lo que ves aquí lo construyó Ricardo pensando en ti: cada frase, cada canción, cada razón detrás de por qué te dedicó esa canción en particular. Yo (Claude Sonnet) solo ayudé con la parte técnica. La intención, el contenido y el amor son completamente suyos.

---

## ¿Qué es michicator?

Un bot de Telegram que te manda, de forma automática:

- 🎵 Una canción — elegida por Ricardo, con la razón personal por la que la escogió para ti
- 💬 Una frase — escrita por él en algún momento en que pensó en ti
- 🌻 Los miércoles: una pregunta especial (los *Miércoles de Garrapata*) Ricardo cree que conocerse es muy divertido.
- Un contador de cuántos días llevan juntos 🧡
- 🗓 **Citas con Frida** — un espacio donde Ricardo guarda ideas de cosas que quiere hacer contigo, que puedes consultar cuando quieras escribiéndole al bot directamente

Lo que lo hace diferente a cualquier bot genérico es que **todo el contenido fue escrito y elegido a mano**. Cada canción viene de una playlist que fue armando contigo en mente. Cada frase la escribió él mismo. El bot solo es el cartero,el remitente siempre es Ricardo.

---

## ¿Por qué automatizarlo y no mandarlo a mano?

Esta fue la pregunta filosófica detrás del proyecto, y vale la pena explicarla porque es importante.

La respuesta corta: el bot no automatiza el *sentimiento*, automatiza el *no olvidarse*.

Ricardo tiene una mente volátil, mil cosas pasan en su mente a velocidad récord y puede no acordarse en ese momento. michicator garantiza que el detalle llegue de todas formas, porque la intención ya estaba puesta desde antes.

Pero hay algo más importante: **las razones de cada canción las escribió cuando le nació hacerlo** — un domingo corriendo, un lunes en la office depot o un viernes cuando te extrañaba. Las guardó. El bot las entrega cuando les toca. No es automatizar la espontaneidad; es preservarla.

La espontaneidad vive en el momento en que él abre el Sheet, escucha una canción y escribe *"esta me recuerda aquella vez que..."*. El bot solo se asegura de que ese momento llegue a ti, aunque ese día él esté ocupado o distraído.

---

## ¿Cómo funciona? (sin tecnicismos)

Tres cosas trabajando juntas:

### 📋 La libreta mágica — Google Sheets

Hay una hoja de cálculo de Google que es el cerebro del bot. Tiene cinco secciones:

- **Config** — los ajustes generales: ¿está activo el bot?, ¿qué día empezaron juntos?, ¿a quién le llegan los mensajes?
- **Canciones** — la lista de canciones que Ricardo eligió para ti, con la razón personal de cada una
- **Frases** — frases que él escribió pensando en ti, en distintos momentos
- **Preguntas** — las preguntas especiales de los miércoles
- **Dates con Frida** — ideas de citas que Ricardo fue guardando: puede ser una cotidiana para el miércoles que se ven, o algo más especial para el finde. Algunas tienen fecha planeada, otras solo esperan el momento indicado

Cada vez que el bot manda algo, marca esa fila como "enviada" para que nunca se repita.

### 💬 El bot que responde — Vercel

Además de mandar mensajes automáticos, michicator ahora también *escucha*. Hay una pequeña función serverless desplegada en Vercel que recibe los mensajes que le escribes al bot y te responde al instante. Sin servidores que pagar, sin nada que mantener prendido — solo se activa cuando tú le escribes algo.

Esto es lo que hace posible los comandos de citas: en cuanto escribes `/cita` en el chat, Telegram le avisa a Vercel, Vercel lee el Sheet, y en segundos tienes una sugerencia.

### ⏰ El reloj automático — GitHub Actions

GitHub es la plataforma donde los programadores guardan su código. Tiene una función que permite ejecutar scripts en horarios definidos, completamente gratis, en servidores en la nube — sin necesitar una computadora prendida ni pagar un servidor.

Michicator vive ahí. Cada miércoles (o con el horario que Ricardo configure), GitHub despierta el bot, este lee la libreta, arma el mensaje y te lo manda. Todo sin que Ricardo tenga que hacer nada ese día específico.

### 💬 El mensajero — Telegram Bot API

Telegram tiene una API — una "puerta trasera" para programadores — que permite enviar mensajes de forma programática. El bot tiene un token secreto que lo identifica y le da permiso de enviar mensajes. Cuando GitHub Actions corre el script, este usa ese token para mandarte el mensaje directamente a tu chat.

---

## La razón detrás de cada canción — `dedicatoria` 🎵

Esta es la parte más personal del bot. En la pestaña `Canciones` del Sheet hay una columna llamada `dedicatoria` donde Ricardo escribió, para cada canción, la razón por la que te la eligió.

El mensaje que recibes se ve así:

```
Para ti, hoy ✨
Llevamos 163 días juntos 🧡

🎵 Hawái — Maluma
https://open.spotify.com/track/...

_ Ejemplo de dedicatoria: Esta me recuerda cuando fuimos a la playa y no quería que se acabara el día._
```

La dedicatoria es opcional — si una canción no tiene, el bot manda solo el título y el link. Pero cuando la tiene, es el corazón del mensaje.

---

## Los Miércoles de Garrapata 🌻

Los miércoles son especiales. Además del mensaje normal, el bot agrega una pregunta de la pestaña `Preguntas` — preguntas que Ricardo escribió para conocerte más, para que hablen de algo nuevo, o simplemente para que tengas algo en qué pensar ese día.

El header del miércoles es diferente al de los demás días, también configurable desde el Sheet.

Hay una clave `miercoles_garrapata` en la configuración — si en algún momento Ricardo la pone en `false`, las preguntas se desactivan sin tocar ningún código.

---

## El contador de días juntos 🧡

En la configuración hay una clave `fecha_inicio` con la fecha en que empezaron. El bot calcula cuántos días llevan juntos cada vez que corre y lo incluye en el mensaje. Simple, pero es uno de esos detalles que se sienten bien al leerlos.

---

## Las piezas técnicas

Para la curiosidad técnica — el stack completo:

| Pieza | Tecnología | Por qué |
|---|---|---|
| Scheduler | GitHub Actions (cron) | Gratis, confiable, sin servidor propio |
| Comandos interactivos | Vercel (serverless) | Responde al instante, costo $0 cuando no se usa |
| Contenido y estado | Google Sheets (gspread) | Fácil de editar sin tocar código |
| Mensajes | Telegram Bot API | Simple y directo, sin instalar nada |
| Canciones | CSV de [exportify.app](https://exportify.app) | Spotify bloqueó su API en modo dev en 2024 😤 |
| Lenguaje | Python 3.11+ | Limpio, rápido de escribir |

No hay servidor que pagar. Todo corre en la nube de forma gratuita.

### Estructura del proyecto

```
michicator/
├── api/
│   └── webhook.py             # Función serverless (Vercel) — recibe comandos del bot
├── michicator/
│   ├── message_formatter.py   # Arma el texto del mensaje
│   ├── sheets_client.py       # Lee y escribe en Google Sheets
│   ├── telegram_client.py     # Manda el mensaje por Telegram
│   └── spotify_client.py      # Opcional: sync con Spotify (bloqueado hoy)
├── scripts/
│   ├── send_daily.py          # Script principal — el que corre cada miércoles
│   ├── setup_webhook.py       # Registra la URL del webhook en Telegram (una sola vez)
│   ├── import_csv.py          # Importa canciones desde un CSV de Exportify
│   └── get_spotify_token.py   # Obtiene el token de Spotify (una sola vez)
├── vercel.json                # Configuración del deploy en Vercel
└── .github/workflows/
    └── send_message.yml       # Le dice a GitHub cuándo y cómo correr el bot
```

---

## Estructura del Google Sheet

### Pestaña: `Config`

| clave | valor | descripción |
|---|---|---|
| `activo` | `true` | `false` para pausar el bot sin tocar código |
| `modo` | `both` | `song`, `phrase`, `both` o `alternate` |
| `orden_canciones` | `random` | `random` o `secuencial` |
| `mensaje_cabecera` | `Para ti, hoy ✨\|Buenos días 🐱\|Pensando en ti 💭` | Separados por `\|`, elige uno al azar |
| `mensaje_cabecera_miercoles` | `¡Feliz miércoles, garrapata! 🐱` | Header exclusivo de los miércoles |
| `recipient_telegram_id` | `123456789` | Tu Chat ID de Telegram |
| `test_telegram_id` | `987654321` | El Chat ID de Ricardo (para pruebas) |
| `last_mode_sent` | `song` | Lo actualiza el bot automáticamente al usar `alternate` |
| `fecha_inicio` | `2024-01-15` | La fecha en que empezaron (YYYY-MM-DD) |
| `miercoles_garrapata` | `true` | `false` para desactivar las preguntas del miércoles |

### Pestaña: `Canciones`

| # | spotify_id | titulo | artista | url | dedicatoria | enviada | fecha_envio |
|---|---|---|---|---|---|---|---|
| 1 | 4LRPiXqCikLlN15c3yImP7 | Hawái | Maluma | https://open.spotify.com/... | Esta me recuerda... | FALSE | |

### Pestaña: `Frases`

| # | frase | enviada | fecha_envio |
|---|---|---|---|
| 1 | Eres lo mejor que me ha pasado. | FALSE | |

### Pestaña: `Preguntas`

| # | pregunta | enviada | fecha_envio |
|---|---|---|---|
| 1 | ¿Cuál es tu recuerdo favorito de este año? | FALSE | |

### Pestaña: `Dates con Frida`

| # | detalle | tipo | referencia | fecha | realizada | fecha_realizada |
|---|---|---|---|---|---|---|
| 1 | Ir a Chipinque con x amigos| finde | https://maps.google.com/... | 2026-07-12 | FALSE | |
| 2 | Ir por donitas y a caminar | cotidiana | | | FALSE | |
| 3 | Ver el sunset en la loma | cotidiana/finde | https://tiktok.com/... | | FALSE | |

- **tipo** puede ser `cotidiana` (para los miércoles), `finde` (viernes/sábado/domingo) o `cotidiana/finde` (cualquier día sirve)
- **referencia** es opcional — puede ser un link de Google Maps, TikTok, YouTube, o cualquier cosa relevante
- **fecha** es opcional — solo cuando ya tienen algo planeado

---

## Configuración de Secrets en GitHub

Los datos sensibles (tokens, IDs) viven como *secrets* en GitHub — cifrados, nunca expuestos en el código:

| Secret | Descripción |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token del bot (lo da `@BotFather` en Telegram) |
| `GOOGLE_SHEET_ID` | ID del Google Sheet (en la URL) |
| `GOOGLE_CREDENTIALS_JSON` | JSON de la cuenta de servicio de Google Cloud |
| `RECIPIENT_OVERRIDE` | `test` (le llega a Ricardo) o `main` (te llega a ti) |

Y en **Vercel** (para los comandos interactivos):

| Variable | Descripción |
|---|---|
| `TELEGRAM_BOT_TOKEN` | El mismo token del bot |
| `GOOGLE_SHEET_ID` | El mismo ID del Sheet |
| `GOOGLE_CREDENTIALS_JSON` | El mismo JSON de la cuenta de servicio |
| `TELEGRAM_WEBHOOK_SECRET` | Un texto secreto inventado — verifica que los mensajes vengan de Telegram y no de otra fuente |

---

## Citas con Frida — comandos del bot 🗓

Esta es la parte nueva. Puedes escribirle directamente al bot en Telegram y te responde al instante:

| Comando | Qué hace |
|---|---|
| `/cita` | Te sugiere una idea de cita al azar (de las que quedan pendientes) |
| `/cita finde` | Solo ideas para fin de semana |
| `/cita cotidiana` | Solo ideas para un miércoles o día entre semana |
| `/proxima` | Te muestra las próximas citas que ya tienen fecha planeada |
| `/realizada 3` | Marca la cita #3 como hecha ✅ |
| `/help` | Lista todos los comandos disponibles |

Ricardo va llenando la pestaña `Dates con Frida` del Sheet con ideas mientras las va encontrando — un video en TikTok, un lugar que le recomendaron, algo que vio y pensó *"esto le va a gustar a Frida"*. El bot las guarda hasta que ustedes las hagan realidad.

---

## Cómo disparar el bot manualmente

Si Ricardo quiere mandarte algo ahora mismo sin esperar al miércoles, puede ir a GitHub → **Actions** → **michicator 💌** → **Run workflow** → elegir `main`. Un click y en segundos te llega el mensaje.

---

## Cómo agregar canciones nuevas

1. Ve a [exportify.app](https://exportify.app) — login con Spotify, selecciona la playlist, **Export**
2. Corre `python scripts/import_csv.py ~/Downloads/playlist.csv`
3. Las canciones nuevas se agregan al Sheet sin duplicar las existentes
4. Abre el Sheet y escribe la `dedicatoria` de cada una directamente en la columna

---

## Roadmap futuro (por si hay algo que quieras agregarle)
Algunas ideas, por ejemplo:

- [x] **Bot interactivo con comandos** — ya puedes escribirle al bot y te responde 🎉
- [x] **Citas con Frida** — ideas de citas guardadas y consultables desde el chat
- [ ] **Hitos de días juntos** — mensaje especial automático al llegar a 100, 200, 365 días
- [ ] **Recuerdos** — cuando marquen una cita como realizada, el bot les pide una nota corta; en el aniversario hace un recap de todo lo que hicieron
- [ ] **Fechas especiales** — aviso automático antes de cumpleaños de amigos, el aniversario de su primera cita, etc.
- [ ] **Mini retos de pareja** — pestaña `Retos` con desafíos semanales
- [ ] **Notificación a Ricardo** — confirmación de que el mensaje se envió exitosamente
- [ ] **Aviso cuando se acabe el contenido** — alerta antes de que el bot se quede sin canciones o frases
- [ ] **Sync automático con Spotify** — cuando Spotify levante la restricción de Development Mode

---

*Hecho con ayuda del buen claude sonnet, pero con todo el amor del mundo, te amo garrapata!!!*