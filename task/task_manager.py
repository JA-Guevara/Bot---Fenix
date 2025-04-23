import asyncio
import importlib
from utils.config import get_credentials, load_selectors
from infrastructure.browser.browser_manager import BrowserManager

async def run_login(bank_name: str):
    # 1. Importar dinámicamente la clase de login
    module = importlib.import_module(f"application.logins.login_{bank_name}")
    LoginClass = getattr(module, f"{bank_name.capitalize()}Login")

    # 2. Cargar navegador y página
    browser_manager = BrowserManager(headless=False)
    page = await browser_manager.get_new_page()

    # 3. Cargar credenciales y selectores
    credentials = get_credentials(bank_name)
    selectors = load_selectors()[bank_name]

    # 4. Ejecutar login
    login_instance = LoginClass(credentials, selectors)
    await login_instance.login(page)

    # 5. Esperar unos segundos para ver el resultado y cerrar
    await page.wait_for_timeout(5000)
    await browser_manager.close_browser()

if __name__ == "__main__":
    asyncio.run(run_login("atlas"))
