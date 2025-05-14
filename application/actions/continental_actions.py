import logging
from domain.login_interface import LoginStrategy
from infrastructure.executors.action_executor import ActionExecutor

class ContinentalActions(LoginStrategy):
    def __init__(self, credentials, selectors, flow,contexto):
        self.logger = logging.getLogger(__name__)
        self.credentials = credentials
        self.selectors = selectors
        self.flow = flow
        self.contexto = contexto

    async def login(self, page):
        self.logger.info("🌐 Login Banco Continental...")
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["login"])

    async def pre_download(self, page):
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["pre_download"])

    async def descargar_reportes(self, page):
        self.logger.info("📥 Iniciando descarga de reportes para Banco Continental...")
        executor = ActionExecutor(page, self.selectors, self.credentials)
        executor.set_contexto(**self.contexto.to_dict())

        self.logger.debug(f"📋 Pasos de descarga: {self.flow['download']}")
        self.logger.debug(f"🏦 Banco: {self.contexto.banco}")

        await executor.descargar_reportes(
            pasos_descarga=self.flow["download"],
            banco=self.contexto.banco
        )
        self.logger.info("✅ Descarga de reportes completada para Banco Continental.")

    async def logout(self, page):
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["logout"])
