import logging

class ActionExecutor:
    def __init__(self, page, selectors: dict, credentials: dict):
        self.page = page
        self.selectors = selectors
        self.credentials = credentials
        self.logger = logging.getLogger(__name__)

    def resolve_variable(self, value):
        """Reemplaza variables tipo $user por el valor real."""
        if isinstance(value, str) and value.startswith("$"):
            key = value[1:]
            return self.credentials.get(key)
        return value

    def get_selector(self, path):
        """Accede a un selector anidado como 'step_1.user_input'."""
        if not path:
            return None
        keys = path.split(".")
        selector = self.selectors
        for key in keys:
            selector = selector.get(key, {})
        return selector if isinstance(selector, str) else None

    async def execute_step(self, step):
        action = step.get("action")

        if action == "goto":
            url = self.resolve_variable(step.get("value"))
            self.logger.info(f"🌍 Navegando a {url}")
            await self.page.goto(url, timeout=60000, wait_until="domcontentloaded")
            
        elif action == "fill":
            selector = self.get_selector(step.get("target"))
            value = self.resolve_variable(step.get("value"))
            self.logger.info(f"📝 Llenando {selector} con '{value}'")
            await self.page.fill(selector, value)
            
        elif action == "type":
            target = step.get("target")
            value = self.resolve_variable(step.get("value"))

            if not target:
                self.logger.error("❌ 'target' es requerido para la acción 'type'")
                raise Exception("'target' es requerido para 'type'")

            selector = self.get_selector(target)
            if not selector:
                self.logger.error(f"❌ Selector no encontrado para target: {target}")
                raise Exception(f"Selector no encontrado: {target}")

            await self.page.click(selector)
            await self.page.fill(selector, "")  # Limpia el campo antes
            await self.page.type(selector, value, delay=100)
            self.logger.info(f"⌨️ Escribiendo (con type) en {selector} el valor: {value}")
        elif action == "click":
            selector = self.get_selector(step.get("target"))
            self.logger.info(f"🖱️ Click en {selector}")
            await self.page.click(selector)

        elif action == "wait_for":
            selector = self.get_selector(step.get("target"))
            self.logger.info(f"⏳ Esperando selector {selector}")
            await self.page.wait_for_selector(selector)

        elif action == "type_virtual_password":
            from application.actions.basa_actions import BasaActions 
            executor = BasaActions(self.credentials, self.selectors, flow={})
            await executor.ingresar_password_virtual(self.page, self.credentials["password"])
        elif action == "wait_time":
            tiempo = step.get("value", 1000)  # por defecto 1 segundo si no hay valor
            self.logger.info(f"⏳ Esperando {tiempo}ms")
            await self.page.wait_for_timeout(tiempo)
        elif action == "type_virtual_pin":
            from application.actions.itau_actions import ItauActions
            executor = ItauActions(self.credentials, self.selectors, flow={})
            await executor.ingresar_pin_virtual(self.page, self.credentials["password"])

        elif action == "keyboard_press":
            key = step.get("value")
            await self.page.keyboard.press(key)
            self.logger.info(f"⌨️ Presionada tecla: {key}")


        else:
            self.logger.warning(f"⚠️ Acción desconocida: {action}")

    async def run_flow(self, flow: list):
        for step in flow:
            action = step.get("action")
            target = step.get("target")
            value = step.get("value")

            print(f"[⚙️] Ejecutando paso: {action} -> {target} con valor: {value}")
            await self.execute_step(step)
