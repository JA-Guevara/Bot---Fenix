import asyncio
import json
from utils.config import get_credentials, load_selectors
from infrastructure.browser.browser_manager import BrowserManager
from application.actions.sudameris_actions import SudamerisActions
from infrastructure.logger.logging_config import setup_logging

setup_logging()

async def run_login_sudameris():
    print("🌀 Login Banco Sudameris")
    browser_manager = BrowserManager(headless=False)
    page = await browser_manager.get_new_page()

    credentials = get_credentials("sudameris")
    selectors = load_selectors()["sudameris"]

    with open("flows/sudameris.json", "r", encoding="utf-8") as f:
        flow = json.load(f)

    login = SudamerisActions(credentials, selectors, flow)
    await login.login(page)

    print("✅ Login completado.")
    await page.wait_for_timeout(5000)
    await browser_manager.close_browser()

if __name__ == "__main__":
    asyncio.run(run_login_sudameris())
