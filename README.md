# 🐱 michicator

> *Michicator - micho dedicator* — Un bot que le hice a mi novia Frida para celebrar un mesversario. Este bot le manda canciones que yo le he querido dedicar y también frases bonitas de manera automatizada, pero escritas y escogidas por uno mismo con la intención de que nunca se me pase el detalle del diario que la pueda hacer sentir amada aunque sea un poquito más. ¿Será esta una buena manera nerd para honrar a este regalo que Dios me dio? 🤔

<p align="center">
  <img src="https://i.pinimg.com/736x/96/db/b0/96dbb065a1beafad294f4f0d97756ad6.jpg" width="380" alt="michicator" />
</p>



---

## ¿Qué hace?

Cada día (o cada N días o configurable), **michicator** le envía por Telegram a esa persona especial:

- 🎵 Una canción de tu lista — sin repetirse nunca
- 💬 Una frase que tú escribiste — sin repetirse nunca
- O ambas cosas a la vez, o alternando
- Con un mensaje de cabecera rotativo que cambia cada envío

Todo configurable desde una hoja de Google Sheets, sin tocar código.

---

## Stack (100% gratis)

| Pieza | Tecnología |
|---|---|
| Scheduler | GitHub Actions (cron) |
| Canciones | Google Sheets (importadas desde CSV de Exportify) |
| Frases + estado | Google Sheets (gspread) |
| Mensajes | Telegram Bot API |
| Lenguaje | Python 3.11+ |

No hay servidor que pagar. GitHub Actions ejecuta el script en la nube gratis.

---

##  Lo que puede hacer hoy

- Enviar una canción aleatoria (o secuencial) por Telegram cada día, sin repetirse
- Enviar frases personalizadas sin repetirse
- Alternar entre canciones y frases, o mandar ambas juntas
- Rotar el mensaje de cabecera aleatoriamente entre varias opciones
- Manejar múltiples destinatarios en modo prueba (tú + amigos que usen telegram y te ayuden a probar la aplicación)
- Manejar múltiples destinatarios en modo producción (tu novia + tú mismo para que veas lo mismo que ella)
- Pausar el bot desde el Sheet (sin tocar código)
- Importar canciones desde un CSV exportado por Exportify
- Correr automáticamente en la nube con GitHub Actions (gratis)
- Dispararse manualmente desde GitHub con un click

## Lo que no puede hacer hoy este bot

- **No puede leer la playlist de Spotify directamente**: Spotify bloqueó el endpoint `/playlists/{id}/tracks` para apps en Development Mode desde 2024. El workaround es exportar el CSV desde [exportify.app](https://exportify.app) y usar `scripts/import_csv.py` FUCK YOU SPOTIFY!!!!!
- **GitHub Actions tiene delay**: el cron no es exacto al minuto, puede retrasarse hasta 30 min en horas pico (irrelevante para uso diario)
- **Máximo 5 usuarios testers en Spotify**: restricción de Development Mode (no afecta el funcionamiento del bot)

---

## Estructura del Google Sheet

Crea un Google Sheet con estas pestañas exactas:

### Pestaña: `Config`
| clave | valor | descripción |
|---|---|---|
| `activo` | `true` | Pon `false` para pausar el bot |
| `modo` | `song` | `song`, `phrase`, `both` o `alternate` |
| `orden_canciones` | `random` | `random` o `secuencial` |
| `mensaje_cabecera` | `Para ti, hoy ✨\|Buenos días 🐱\|Pensando en ti 💭` | Separados por `\|`, elige uno al azar |
| `recipient_telegram_id` | `123456789` | Chat ID de ella (o varios separados por `,`) |
| `test_telegram_id` | `123456789,987654321` | Tus IDs de prueba (separados por `,`) |
| `last_mode_sent` | `song` | Lo actualiza el bot automáticamente al alternar |

**Valores de `modo`:**
- `song` — solo canción
- `phrase` — solo frase
- `both` — canción + frase juntas
- `alternate` — va alternando canción / frase cada envío

### Pestaña: `Canciones`
| # | spotify_id | titulo | artista | url | enviada | fecha_envio |
|---|---|---|---|---|---|---|

*(se llena con `scripts/import_csv.py` desde un CSV de Exportify)*

### Pestaña: `Frases`
| # | frase | enviada | fecha_envio |
|---|---|---|---|
| 1 | Frase bonita 1 | FALSE | |
| 2 | Frase bonita 2 | FALSE | |

---

## Configuración de Secrets en GitHub

Ve a tu repo → **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Descripción |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token de BotFather |
| `GOOGLE_SHEET_ID` | ID del Google Sheet (en la URL) |
| `GOOGLE_CREDENTIALS_JSON` | JSON completo de la cuenta de servicio (en una línea) |
| `RECIPIENT_OVERRIDE` | `test` (para pruebas) o `main` (para producción) |

> Los secrets de Spotify (`SPOTIFY_CLIENT_ID`, etc.) son opcionales — solo los necesitas si en el futuro quieres usar el sync directo con la API de Spotify.

---

## Comandos útiles

```bash
# Instalar dependencias
pip install -r requirements.txt

# Importar canciones desde CSV de Exportify
python scripts/import_csv.py ~/Downloads/mi_playlist.csv

# Obtener Spotify refresh token (una sola vez)
python scripts/get_spotify_token.py

# Enviar mensaje de prueba (a ti mismo)
python scripts/send_daily.py   # RECIPIENT_OVERRIDE=test en el .env

# Enviar a ella
# Cambia RECIPIENT_OVERRIDE=main en el .env o en los Secrets de GitHub
python scripts/send_daily.py
```

---

## Cómo importar canciones (flujo actual)

1. Ve a [exportify.app](https://exportify.app)
2. Login con Spotify → selecciona tu playlist → **Export**
3. Descarga el CSV
4. Corre:
   ```bash
   python scripts/import_csv.py ~/Downloads/nombre_playlist.csv
   ```
5. Las canciones nuevas se agregan al Sheet sin duplicar las existentes

---

## Configurar el cron

Edita `.github/workflows/send_message.yml`:

```yaml
# Cada día a las 9am Colombia (UTC-5 → 14:00 UTC)
- cron: '0 14 * * *'

# Cada 2 días a las 9am Colombia
- cron: '0 14 */2 * *'

# Lunes, miércoles, viernes
- cron: '0 14 * * 1,3,5'

# Cada hora (solo para pruebas)
- cron: '0 * * * *'
```

> GitHub Actions tiene un límite de 2,000 minutos/mes gratis. Con envío diario usas ~1% del límite. Con cron cada hora ~18%. (De esto no estoy tan seguro la neta, pero no te los acabas según yo xD)

---

## Cómo cambiar de modo prueba a producción

1. Ve a `github.com/TU_USUARIO/michicator` → **Settings → Secrets → Actions**
2. Edita el secret `RECIPIENT_OVERRIDE`
3. Cambia de `test` a `main`
4. Asegúrate de tener el Chat ID de tu novia en `recipient_telegram_id` en el Sheet

---

## Cómo obtener un Chat ID de Telegram

1. La persona le escribe cualquier cosa a tu bot
2. Abre esta URL en el navegador (con tu token):
   ```
   https://api.telegram.org/botTU_TOKEN/getUpdates
   ```
3. Busca `"chat": {"id": NUMERO}` — ese número es el Chat ID

---

## Formato del mensaje

```
Buenos días, mi michi 🐱

"Eres lo mejor que me ha pasado."

🎵 Hawái — Maluma
https://open.spotify.com/track/...
```

Simple. Elegante. Personal.

---

## Roadmap futuro

- [ ] Sync automático con Spotify (cuando levanten la restricción de Development Mode)
- [ ] Soporte para fotos junto al mensaje
- [ ] Notificación cuando se acaben las canciones o frases


---

## Stack (100% gratis)

| Pieza | Tecnología |
|---|---|
| Scheduler | GitHub Actions (cron) |
| Canciones | Spotify Web API + Spotipy |
| Frases + estado | Google Sheets (gspread) |
| Mensajes | Telegram Bot API |
| Lenguaje | Python 3.11+ |

No hay servidor que pagar. GitHub Actions ejecuta el script en la nube gratis.

---

## Plan de implementación

### Fase 1 — Configuración de servicios (una vez)
- [ ] Crear Telegram Bot via BotFather → obtener `BOT_TOKEN`
- [ ] Obtener tu `CHAT_ID` de Telegram (test) y el de ella (main)
- [ ] Crear app en Spotify Developer → `CLIENT_ID` + `CLIENT_SECRET`
- [ ] Crear Google Sheet con la estructura definida abajo
- [ ] Crear cuenta de servicio en Google Cloud → descargar JSON
- [ ] Hacer fork/clone de este repo y configurar los Secrets en GitHub

### Fase 2 — Llenar contenido
- [ ] Correr `sync_playlist.py` una vez para importar tu playlist de Spotify al Sheet
- [ ] Escribir tus frases en la pestaña "Frases" del Sheet

### Fase 3 — Activar
- [ ] Ajustar el cron en `.github/workflows/send_message.yml`
- [ ] Probar con `RECIPIENT_OVERRIDE=test` (te llega a ti)
- [ ] Cambiar `RECIPIENT_OVERRIDE=main` cuando estés listo

---

## Estructura del Google Sheet

Crea un Google Sheet con estas pestañas exactas:

### Pestaña: `Config`
| clave | valor |
|---|---|
| activo | true |
| modo | song |
| recipient_telegram_id | (chat_id de ella) |
| test_telegram_id | (tu chat_id) |
| last_mode_sent | song |

**Valores de `modo`:**
- `song` — solo canción
- `phrase` — solo frase
- `both` — canción + frase juntas
- `alternate` — va alternando canción / frase cada envío

### Pestaña: `Canciones`
| # | spotify_id | titulo | artista | url | enviada | fecha_envio |
|---|---|---|---|---|---|---|
*(se llena con `sync_playlist.py`)*

### Pestaña: `Frases`
| # | frase | enviada | fecha_envio |
|---|---|---|---|
| 1 | "Eres lo mejor que me ha pasado este año." | FALSE | |
| 2 | "Te admiro más de lo que sé expresar." | FALSE | |

---

## Configuración de Secrets en GitHub

Ve a tu repo → Settings → Secrets → Actions y agrega:

| Secret | Descripción |
|---|---|
| `SPOTIFY_CLIENT_ID` | App ID de Spotify Developer |
| `SPOTIFY_CLIENT_SECRET` | Secret de Spotify Developer |
| `SPOTIFY_PLAYLIST_ID` | ID de la playlist (en la URL de Spotify) |
| `TELEGRAM_BOT_TOKEN` | Token de BotFather |
| `GOOGLE_SHEET_ID` | ID del Google Sheet (en la URL) |
| `GOOGLE_CREDENTIALS_JSON` | JSON completo de la cuenta de servicio |
| `RECIPIENT_OVERRIDE` | `test` (para ti) o `main` (para ella) |

---

## Comandos útiles

```bash
# Instalar dependencias
pip install -r requirements.txt

# Sincronizar playlist de Spotify → Google Sheets (correr una vez)
python scripts/sync_playlist.py

# Enviar mensaje de prueba (a ti mismo)
RECIPIENT_OVERRIDE=test python scripts/send_daily.py

# Enviar a ella
RECIPIENT_OVERRIDE=main python scripts/send_daily.py
```

---

## Configurar el cron

Edita `.github/workflows/send_message.yml`:

```yaml
# Cada día a las 9am (hora Colombia = UTC-5, entonces UTC 14:00)
- cron: '0 14 * * *'

# Cada 2 días
- cron: '0 14 */2 * *'

# Lunes, miércoles, viernes
- cron: '0 14 * * 1,3,5'
```

---

## Setup paso a paso

### 1. Crear el Telegram Bot

1. Abre Telegram, busca `@BotFather`
2. Escribe `/newbot`
3. Dale un nombre: `michicator` y un username: `michicator_bot`
4. Guarda el token que te da

**Obtener tu Chat ID:**
1. Busca `@userinfobot` en Telegram
2. Escríbele `/start`
3. Te dará tu `id` — ese es tu `test_telegram_id`
4. Repite con la cuenta de ella para el `recipient_telegram_id`

---

### 2. Crear app en Spotify

1. Ve a https://developer.spotify.com/dashboard
2. Crea una app (nombre: michicator)
3. Copia `Client ID` y `Client Secret`
4. El ID de tu playlist está en la URL: `spotify.com/playlist/**{ID_AQUI}**`

---

### 3. Crear Google Sheet + cuenta de servicio

1. Crea un Sheet en https://sheets.google.com
2. Nómbralo `michicator`
3. Crea las 3 pestañas: `Config`, `Canciones`, `Frases`
4. Copia el ID del sheet de la URL: `docs.google.com/spreadsheets/d/**{ID_AQUI}**/`

**Cuenta de servicio:**
1. Ve a https://console.cloud.google.com
2. Crea un proyecto nuevo llamado `michicator`
3. Habilita la API: **Google Sheets API**
4. Ve a "Credenciales" → "Crear credenciales" → "Cuenta de servicio"
5. Nombre: `michicator-bot`
6. Descarga el JSON de la clave
7. **Comparte** el Google Sheet con el email de la cuenta de servicio (el que aparece en el JSON, termina en `@...iam.gserviceaccount.com`)

---

## Formato del mensaje

```
Para ti, hoy ✨

"Eres lo mejor que me ha pasado."

🎵 Hawái — Maluma
open.spotify.com/track/...
```

Simple. Elegante. Personal.

---

## Roadmap futuro

- [ ] Soporte para fotos/stickers junto al mensaje
- [ ] Dashboard web para ver el historial de envíos
- [ ] Comando `/siguiente` para ver cuál canción viene
- [ ] Notificación a ti cuando se envíe exitosamente

---

*Con ayuda del buen claude sonnet, pero con todo el amor del mundo, te amo garrapata!!!*
