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

def extract_post_url(page, group_url):
    try:
        page.wait_for_timeout(4000)

        post_element = page.query_selector("div[data-ft]")
        if not post_element:
            print("No se encontró el post recién creado.")
            return None

        data_ft = post_element.get_attribute("data-ft")
        if not data_ft:
            return None

        data = json.loads(data_ft)
        story_id = data.get("mf_story_key")

        if not story_id:
            return None

        group_id = group_url.split("/")[-1]
        return f"https://www.facebook.com/groups/{group_id}/posts/{story_id}/"

    except Exception as e:
        print("Error extrayendo URL del post:", e)
        return None


def post_to_facebook_groups(content: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://www.facebook.com/login", wait_until="networkidle")
        page.fill("#email", FB_EMAIL)
        page.fill("#pass", FB_PASSWORD)
        page.click("button[name='login']")
        page.wait_for_timeout(5000)

        post_links = []

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

                    post_url = extract_post_url(page, group_url)
                    post_links.append(post_url)

                else:
                    print("No se encontró el cuadro de texto.")
                    post_links.append(None)

            except Exception as e:
                print(f"Error en {group_url}: {e}")
                post_links.append(None)

        browser.close()
        return post_links


def handle_message(update, context):
    text = update.message.text
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text="Publicando en Facebook...")

    try:
        links = post_to_facebook_groups(text)

        response = "Publicación enviada.\n\n"
        for i, link in enumerate(links):
            if link:
                response += f"Grupo {i+1}: {link}\n"
            else:
                response += f"Grupo {i+1}: No se pudo obtener el enlace.\n"

        context.bot.send_message(chat_id=chat_id, text=response)

    except Exception as e:
        print("Error:", e)
        context.bot.send_message(chat_id=chat_id, text="Error al publicar.")


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
