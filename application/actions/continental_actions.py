import logging
from domain.login_interface import LoginStrategy
from infrastructure.executors.action_executor import ActionExecutor
from services.ruta_service import generar_clave_cuenta

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

        await self.descargar_reportes_continental(page, self.flow["download"], executor)
        self.logger.info("✅ Descarga de reportes completada para Banco Continental.")

    async def logout(self, page):
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["logout"])
    
    async def descargar_reportes_continental(self, page, pasos_descarga: list,executor: ActionExecutor):
        self.page = page
        self.logger.info("🧭 Entrando a descargar_reportes_continental()")

        # Selectores
        cuenta_input = self.selectors["step_2"].get("cuenta_input_selector")
        periodo_input = self.selectors["step_2"].get("periodo_input_selector")
        cuenta_button = self.selectors["step_2"].get("cuenta_dropdown_button")
        periodo_button = self.selectors["step_2"].get("periodo_dropdown_button")
        opcion_periodo_texto = self.selectors["step_2"].get("periodo_opcion_text", "Por Periodo")

        if not cuenta_button or not periodo_button:
            self.logger.error("❌ Faltan botones de dropdown.")
            return

        cuentas = getattr(self.contexto, "cuentas", [])
        cuentas_excel = {
            str(c.get("NROCUENTA", "")).strip(): c
            for c in cuentas
            if c.get("NROCUENTA")
        }

        self.logger.info(f"📋 Cuentas Excel detectadas (formato exacto): {list(cuentas_excel.keys())}")

        for nro_original, cuenta in cuentas_excel.items():
            try:
                self.logger.info(f"🔽 Procesando cuenta: {nro_original}")

                # 👉 Abrir dropdown y escribir la cuenta exacta
                await self.page.click(cuenta_button)
                await self.page.wait_for_selector(cuenta_input)
                await self.page.fill(cuenta_input, nro_original)
                await self.page.keyboard.press("Enter")
                self.logger.info(f"🟢 Cuenta escrita y seleccionada: {nro_original}")

                # 👉 Abrir dropdown de período y escribir la opción
                await self.page.click(periodo_button)
                await self.page.wait_for_selector(periodo_input)
                await self.page.fill(periodo_input, opcion_periodo_texto)
                await self.page.keyboard.press("Enter")
                self.logger.info(f"📆 Período escrito y seleccionado: {opcion_periodo_texto}")

                # 👉 Ruta de salida
                clave = generar_clave_cuenta(cuenta)
                rutas_por_cuenta = getattr(self.contexto, "rutas_por_cuenta", {})
                base_dir = getattr(self.contexto, "base_dir", "")
                self.ruta_salida = rutas_por_cuenta.get(clave, base_dir)

                executor.contexto["ruta_descarga"] = self.ruta_salida

                self.logger.info(f"📁 Ruta descarga: {self.ruta_salida}")

                await executor.run_flow(pasos_descarga)


            except Exception as e:
                self.logger.error(f"❌ Error con cuenta {nro_original}: {e}")
