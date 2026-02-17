import os
import json
from dotenv import load_dotenv
from telegram.ext import Updater, MessageHandler, Filters
from playwright.sync_api import sync_playwright

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = int(os.getenv("PORT", "8080"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

FB_EMAIL = os.getenv("FB_EMAIL")
FB_PASSWORD = os.getenv("FB_PASSWORD")
FB_GROUP_URLS = os.getenv("FB_GROUP_URLS", "").split(",")


def post_to_facebook_groups(content: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 1) Intentar login
        print("Entrando a Facebook login...")
        page.goto("https://www.facebook.com/login", wait_until="networkidle")

        page.fill("#email", FB_EMAIL)
        page.fill("#pass", FB_PASSWORD)
        page.click("button[name='login']")
        page.wait_for_timeout(5000)

        # 2) Verificar si la sesión se inició correctamente
        print("Verificando perfil...")
        page.goto("https://www.facebook.com/me", wait_until="networkidle")
        page.wait_for_timeout(4000)

        html = page.content()

        if "Agregar a historia" in html or "Editar perfil" in html:
            login_status = "OK"
            print("LOGIN OK — Sesión iniciada.")
        else:
            login_status = "FAIL"
            print("LOGIN FALLÓ — No se pudo iniciar sesión.")
            browser.close()
            return {"login": "FAIL", "posts": []}

        # 3) Si el login fue exitoso, intentar publicar
        post_results = []

        for group_url in FB_GROUP_URLS:
            group_url = group_url.strip()
            if not group_url:
                continue

            print(f"Publicando en: {group_url}")
            try:
                page.goto(group_url, wait_until="networkidle")
                page.wait_for_timeout(3000)

                textbox = page.query_selector('[role="textbox"]')
                if textbox:
                    textbox.click()
                    page.wait_for_timeout(1000)
                    textbox = page.query_selector('[role="textbox"]')
                    if textbox:
                        textbox.fill(content)
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(5000)
                        post_results.append("Publicado (no se recuperó enlace).")
                    else:
                        post_results.append("No se pudo reencontrar el cuadro de texto.")
                else:
                    post_results.append("No se encontró el cuadro de texto en la página.")

            except Exception as e:
                print(f"Error publicando en {group_url}: {e}")
                post_results.append(f"Error al publicar: {e}")

        browser.close()
        return {"login": login_status, "posts": post_results}


def handle_message(update, context):
    text = update.message.text
    chat_id = update.message.chat_id

    context.bot.send_message(chat_id=chat_id, text="Intentando iniciar sesión en Facebook...")

    try:
        result = post_to_facebook_groups(text)
    except Exception as e:
        print("Error general en post_to_facebook_groups:", e)
        context.bot.send_message(chat_id=chat_id, text="Error al intentar publicar en Facebook.")
        return

    # 1) Reportar estado de login
    if result["login"] == "FAIL":
        context.bot.send_message(chat_id=chat_id, text="❌ No se pudo iniciar sesión en Facebook.")
        return
    else:
        context.bot.send_message(chat_id=chat_id, text="✅ Sesión iniciada correctamente en Facebook.")

    # 2) Reportar resultado de publicaciones
    if not result["posts"]:
        context.bot.send_message(chat_id=chat_id, text="No se intentó publicar en ningún grupo/perfil.")
        return

    respuesta = "📢 Resultado de publicaciones:\n\n"
    for i, r in enumerate(result["posts"]):
        respuesta += f"Destino {i+1}: {r}\n"

    context.bot.send_message(chat_id=chat_id, text=respuesta)


def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TELEGRAM_BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}"
    )

    updater.idle()


if __name__ == "__main__":
    main()

