# application/actions/gnb_actions.py
import logging
from infrastructure.executors.action_executor import ActionExecutor

class GnbActions:
    def __init__(self, credentials, selectors, flow,contexto):
        self.logger = logging.getLogger(__name__)
        self.credentials = credentials
        self.selectors = selectors
        self.flow = flow
        self.contexto = contexto

    async def login(self, page):
        self.logger.info("🌐 Login Banco GNB...")
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
