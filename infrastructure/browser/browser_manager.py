import os
import shutil
import json
from playwright.async_api import async_playwright

class BrowserManager:
    """Gestiona las operaciones del navegador."""

    def __init__(self, headless: bool = False):
        """
        :param headless: Indica si el navegador debe ejecutarse en modo headless.
        """
        self.headless = headless
        self.browser = None
        self.context = None
        self.playwright = None  # Guardar la instancia de Playwright
        self.storage_state_path = "user_data.json"

    async def prepare_storage_state(self):
        """
        Verifica y crea un archivo de estado vacío si no existe.
        """
        if not os.path.exists(self.storage_state_path):
            print(f"Archivo {self.storage_state_path} no encontrado. Creando archivo vacío...")
            with open(self.storage_state_path, 'w') as file:
                json.dump({"cookies": [], "origins": []}, file)

    async def create_browser_context(self):
        """
        Crea el navegador y su contexto asociado.
        """
        # Preparar el estado de almacenamiento
        await self.prepare_storage_state()

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)

        # Opciones para el contexto
        storage_options = {"storage_state": self.storage_state_path}

        # Crear el contexto con el estado almacenado
        self.context = await self.browser.new_context(**storage_options)
        return self.context, self.browser

    async def close_browser(self):
        """
        Cierra el navegador y su contexto asociado, guardando el estado de las cookies.
        Si el navegador ya está cerrado, no realiza ninguna acción.
        """
        try:
            if self.context:
                # Guardamos el estado de las cookies antes de cerrar
                await self.context.storage_state(path=self.storage_state_path)
                await self.context.close()
                print("✔ Contexto cerrado correctamente.")

            if self.browser:
                await self.browser.close()
                print("✔ Navegador cerrado correctamente.")

            # Cerrar Playwright
            if self.playwright:
                await self.playwright.stop()
                print("✔ Playwright detenido correctamente.")

            # Resetear el estado de inicialización
            self.is_initialized = False

        except Exception as e:
            print(f"⚠️ Error al cerrar el navegador o contexto: {e}")
            
    async def clear_cookies(self):
        """
        Limpia las cookies y la caché.
        """
        if self.context:
            await self.context.clear_cookies()

        # Limpiar la caché si es necesario
        storage_path = "user_data"
        if os.path.exists(storage_path):
            shutil.rmtree(storage_path, ignore_errors=True)  # Portátil para Windows y Linux/Mac
