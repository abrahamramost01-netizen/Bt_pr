import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

FB_EMAIL = os.getenv("FB_EMAIL")
FB_PASSWORD = os.getenv("FB_PASSWORD")

def test_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("Entrando a Facebook...")
        page.goto("https://www.facebook.com/login", wait_until="networkidle")

        page.fill("#email", FB_EMAIL)
        page.fill("#pass", FB_PASSWORD)
        page.click("button[name='login']")
        page.wait_for_timeout(5000)

        print("Abriendo tu perfil...")
        page.goto("https://www.facebook.com/me", wait_until="networkidle")
        page.wait_for_timeout(5000)

        html = page.content()

        if FB_EMAIL.split("@")[0] in html or "Editar perfil" in html or "Agregar a historia" in html:
            print("LOGIN OK — Estás dentro de tu cuenta.")
        else:
            print("LOGIN FALLÓ — Facebook no te dejó entrar.")

        browser.close()

if __name__ == "__main__":
    test_login()

