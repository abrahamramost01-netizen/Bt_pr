# Bot Telegram → Facebook (Railway)

Este bot recibe mensajes en Telegram y los publica automáticamente en grupos de Facebook usando Playwright + cookies.

## Variables de entorno necesarias

- TELEGRAM_BOT_TOKEN
- FB_GROUP_URLS  (separadas por comas)
- FB_COOKIES_JSON (JSON completo en una sola línea)

## Despliegue en Railway

1. Crear un proyecto nuevo desde GitHub
2. Añadir las variables de entorno
3. Railway instalará Playwright automáticamente
4. El bot quedará activo 24/7
