import os
import shutil
import json

from playwright.async_api import async_playwright

class BrowserManager:

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.playwright = None

    async def create_browser_context(self, banco=None):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)

        self.cookie_dir = os.path.join("storage", "cookies")
        os.makedirs(self.cookie_dir, exist_ok=True)

        storage_path = f"{self.cookie_dir}/{banco.lower()}.json" if banco else None
        usar_cookies = banco and os.path.exists(storage_path)

        if usar_cookies:
            print(f"🧠 Cargando storage_state para {banco}")
            self.context = await self.browser.new_context(
                storage_state=storage_path,
                accept_downloads=True
            )
        else:
            print(f"🆕 Contexto limpio para {banco or 'sesión anónima'}")
            self.context = await self.browser.new_context(accept_downloads=True)

            # 👉 Cargar cookies solo si es sudameris
            if banco:
                cookies_file = os.path.join(self.cookie_dir, f"cookies_{banco.lower()}.json")
            else:
                cookies_file = None

            if banco and banco.lower() == "sudameris" and cookies_file and os.path.exists(cookies_file):
                print(f"🍪 Cargando cookies manuales desde {cookies_file}")
                with open(cookies_file, "r") as f:
                    cookies = json.load(f)
                for cookie in cookies:
                    # Convertir expires si es int
                    if isinstance(cookie.get("expires"), int):
                        cookie["expires"] = float(cookie["expires"])

                    # Normalizar sameSite si viene como null o inválido
                    same_site = cookie.get("sameSite")
                    if same_site is None or same_site not in ("Lax", "Strict", "None"):
                        cookie["sameSite"] = "Lax"  # valor por defecto seguro

                await self.context.add_cookies(cookies)


        return self.context

            
    async def get_new_page(self):
        banco = getattr(self, "nombre_banco", None)
        context = await self.create_browser_context(banco=banco)
        return await context.new_page()

    
    async def close_browser(self):

        try:
            if self.context:
                await self.context.close()
                print("✔ Contexto cerrado correctamente.")

            if self.browser:
                await self.browser.close()
                print("✔ Navegador cerrado correctamente.")

            if self.playwright:
                await self.playwright.stop()
                print("✔ Playwright detenido correctamente.")

        except Exception as e:
            print(f"⚠️ Error al cerrar navegador/contexto: {e}")

    async def clear_temp_files(self):

        temp_folder = "user_data"
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder, ignore_errors=True)
            print("🧹 Carpeta temporal eliminada.")
