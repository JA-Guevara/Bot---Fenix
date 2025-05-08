import logging
from infrastructure.executors.action_executor import ActionExecutor

class ItauActions:
    def __init__(self, credentials, selectors, flow,contexto):
        self.logger = logging.getLogger(__name__)
        self.credentials = credentials
        self.selectors = selectors
        self.flow = flow
        self.contexto = contexto

    async def login(self, page):
        self.logger.info("🌐 Login Banco Itau...")
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["login"])

    async def pre_download(self, page):
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["pre_download"])

    async def descargar_reportes(self, page):
        
        executor = ActionExecutor(page, self.selectors, self.credentials)
        executor.set_contexto(**self.contexto.to_dict())

        await executor.descargar_reportes(
            pasos_descarga=self.flow["download"]
        )

    async def logout(self, page):
        executor = ActionExecutor(page, self.selectors, self.credentials)
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
