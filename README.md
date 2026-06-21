# 🐱 michicator

> *micho dedicator* — Un bot que le manda canciones (y frases) a tu michi favorita, cada día.

---

## ¿Qué hace?

Cada día (o cada N días), **michicator** le envía por Telegram a tu novia:

- 🎵 Una canción de tu playlist de Spotify — sin repetirse
- 💬 Una frase que tú escribiste en Google Sheets — sin repetirse
- O ambas cosas a la vez, o alternando

Todo configurable desde una hoja de Google Sheets, sin tocar código.

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

*Hecho con 🐱 y mucho amor.*
