import logging
from infrastructure.executors.action_executor import ActionExecutor

class ItauActions:
    def __init__(self, credentials, selectors, flow):
        self.credentials = credentials
        self.selectors = selectors
        self.flow = flow
        self.logger = logging.getLogger(__name__)

    async def login(self, page):
        self.logger.info("🌀 Login Banco Itaú...")
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["login"])
        await executor.run_flow(self.flow["logout"])

    async def ingresar_pin_virtual(self, page, password):
        self.logger.info("🔐 Ingresando PIN virtual...")

        await page.wait_for_selector('#teclado_borrar', timeout=10000)

        for char in password:
            encontrada = False
            teclas = await page.query_selector_all('ul#tecladoBoxDivIdDefault_numeros > li.numeros')

            for tecla in teclas:
                texto = await tecla.inner_text()
                texto = texto.strip()

                if texto == char:
                    await tecla.click()
                    self.logger.info(f"🟢 Presionado: {char}")
                    encontrada = True
                    await page.wait_for_timeout(100)  # Delay entre clics
                    break

            if not encontrada:
                visibles = [(await t.inner_text()).strip() for t in teclas]
                self.logger.error(f"❌ No se encontró tecla con valor: {char} | Visibles: {visibles}")
                raise Exception(f"❌ Fallo al ingresar dígito: {char}")
