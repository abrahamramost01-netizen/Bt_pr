import os
import json
from dotenv import load_dotenv
from telegram.ext import Updater, MessageHandler, Filters
from playwright.sync_api import sync_playwright

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = int(os.getenv("PORT", "8080"))  # Railway usa 8080
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # tu dominio Railway
FB_GROUP_URLS = os.getenv("FB_GROUP_URLS", "").split(",")
FB_COOKIES_JSON = os.getenv("FB_COOKIES_JSON", "")

def post_to_facebook_groups(content: str):
    if not FB_COOKIES_JSON:
        print("ERROR: No hay cookies configuradas.")
        return

    cookies = json.loads(FB_COOKIES_JSON)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.add_cookies(cookies)
        page = context.new_page()

        for group_url in FB_GROUP_URLS:
            group_url = group_url.strip()
            if not group_url:
                continue
            print(f"Publicando en: {group_url}")
            page.goto(group_url, wait_until="networkidle")
            page.wait_for_timeout(3000)
            try:
                textbox = page.query_selector('[role="textbox"]')
                if textbox:
                    textbox.click()
                    page.wait_for_timeout(1000)
                    textbox = page.query_selector('[role="textbox"]')
                    textbox.fill(content)
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(5000)
                else:
                    print("No se encontró el cuadro de texto.")
            except Exception as e:
                print(f"Error en {group_url}: {e}")

        browser.close()

def handle_message(update, context):
    text = update.message.text
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text="Publicando en Facebook...")
    try:
        post_to_facebook_groups(text)
        context.bot.send_message(chat_id=chat_id, text="Publicación enviada.")
    except Exception as e:
        print("Error:", e)
        context.bot.send_message(chat_id=chat_id, text="Error al publicar.")

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Configurar webhook
    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TELEGRAM_BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}"
    )

    updater.idle()

if __name__ == "__main__":
    main()
