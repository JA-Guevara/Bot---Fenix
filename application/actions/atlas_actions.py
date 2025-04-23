import logging
from domain.login_interface import LoginStrategy
from infrastructure.executors.action_executor import ActionExecutor

class AtlasActions(LoginStrategy):  # hereda LoginStrategy para mantener el contrato
    def __init__(self, credentials, selectors, flow):
        self.logger = logging.getLogger(__name__)
        self.credentials = credentials
        self.selectors = selectors
        self.flow = flow

    async def login(self, page):
        self.logger.info("🌐 Login Banco Atlas...")
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["login"])
