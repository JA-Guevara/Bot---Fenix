import logging
from domain.login_interface import LoginStrategy
from infrastructure.executors.action_executor import ActionExecutor

class BasaActions(LoginStrategy):
    def __init__(self, credentials, selectors, flow):
        self.logger = logging.getLogger(__name__)
        self.credentials = credentials
        self.selectors = selectors
        self.flow = flow

    async def login(self, page):
        self.logger.info("🌐 Login Banco Basa...")
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["login"])

    async def ingresar_password_virtual(self, page, password):
        await page.wait_for_selector('[data-valor]', timeout=10000)

        for char in password:
            teclas = await page.query_selector_all('[data-valor]')
            encontrada = False

            for tecla in teclas:
                texto = await tecla.inner_text()
                texto = texto.strip()

                self.logger.debug(f"[🔎] Visible: '{texto}' esperando: '{char}'")

                if texto == char:
                    await tecla.click()
                    self.logger.info(f"🟢 Presionada: {char}")
                    encontrada = True
                    await page.wait_for_timeout(100)
                    break

            if not encontrada:
                visibles = [(await t.inner_text()).strip() for t in teclas]
                self.logger.error(f"❌ No se encontró tecla con valor visible: {char} | Teclas visibles: {visibles}")
                raise Exception(f"❌ No se pudo ingresar el carácter: {char}")
