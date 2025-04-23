# application/logins/login_atlas.py

from domain.login_interface import LoginStrategy

class AtlasLogin(LoginStrategy):
    def __init__(self, credentials: dict, selectors: dict):
        self.credentials = credentials
        self.selectors = selectors

    async def login(self, page):
        await page.goto(self.credentials["url"])

        # Paso 1: ingresar usuario
        if self.credentials["user"]:  # por si viene vacío
            await page.fill(self.selectors["step_1"]["user_input"], self.credentials["user"])

        # Paso 2: ingresar contraseña
        await page.fill(self.selectors["step_1"]["password_input"], self.credentials["password"])

        # Paso 3: clic en botón ingresar
        await page.click(self.selectors["step_1"]["login_button"])
