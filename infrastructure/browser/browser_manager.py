import os
import shutil
from playwright.async_api import async_playwright

class BrowserManager:
    """
    Gestiona el navegador Playwright con enfoque seguro: sin cookies ni almacenamiento persistente.
    """

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.playwright = None

    async def create_browser_context(self):
        """
        Inicia Playwright, lanza un navegador y crea un contexto limpio.
        """
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            accept_downloads=True
        )

        return self.context

    async def get_new_page(self):
        """
        Crea un nuevo contexto y devuelve una página limpia.
        Útil para asegurar sesiones separadas por banco.
        """
        context = await self.create_browser_context()
        return await context.new_page()

    async def close_browser(self):
        """
        Cierra navegador y contexto de forma segura.
        """
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
        """
        Borra manualmente cualquier carpeta temporal que uses (opcional).
        """
        temp_folder = "user_data"
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder, ignore_errors=True)
            print("🧹 Carpeta temporal eliminada.")
