import logging
import re
import os
from services.ruta_service import generar_clave_cuenta

class ActionExecutor:
    def __init__(self, page, selectors: dict, credentials: dict):
        self.page = page
        self.selectors = selectors
        self.credentials = credentials
        self.logger = logging.getLogger(__name__)
        self.contexto = {}
        self.cuentas_indexadas = set()
        self.ruta_salida = ""

    def resolve_variable(self, value):
        if isinstance(value, str) and value.startswith("$"):
            key = value[1:]
            resolved = self.credentials.get(key) or self.contexto.get(key)
            return str(resolved) if resolved is not None else ""
        return value

    def get_selector(self, path):
        if not path:
            return None
        keys = path.split(".")
        selector = self.selectors
        for key in keys:
            selector = selector.get(key, {})
        return selector if isinstance(selector, str) else None

    def set_contexto(self, **kwargs):
        self.contexto = kwargs
        self.cuentas_indexadas.clear()
        for cuenta in self.contexto.get("cuentas", []):
            clave = generar_clave_cuenta(cuenta)
            self.cuentas_indexadas.add(clave)

    async def verificar_cambio_contrasena(self, selector_modal):
        if not selector_modal:
            return
        try:
            modal = await self.page.query_selector(selector_modal)
            if modal:
                texto = await modal.inner_text()
                self.logger.critical(f"🚨 Modal de cambio de contraseña detectado: {texto.strip()}")
                await self.enviar_alerta_critica("CAMBIO DE CONTRASEÑA requerido.")
                raise Exception("⚠️ Cambio de contraseña requerido. Ejecución detenida.")
        except Exception as e:
            self.logger.error(f"❌ Error al verificar modal de contraseña: {e}")
            raise

    async def esperar_y_guardar_descarga(self, selector: str, ruta_destino: str):
        if not ruta_destino or not ruta_destino.strip():
            raise ValueError("❌ La ruta de descarga está vacía o no fue resuelta correctamente.")
        os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
        async with self.page.expect_download() as download_info:
            await self.page.click(selector)
        download = await download_info.value
        try:
            await download.save_as(ruta_destino)
            self.logger.info(f"✅ Archivo guardado como: {ruta_destino}")
        except Exception as e:
            self.logger.error(f"❌ Error al guardar archivo: {e}")
            raise

    async def descargar_reportes(self, pasos_descarga: list):
        selector_lista = self.selectors["step_3"].get("list_selector")
        self.logger.info(f"🔎 Buscando cuentas con selector: {selector_lista}")
        cuentas_en_ui = await self.page.query_selector_all(selector_lista)
        if not cuentas_en_ui:
            self.logger.warning("⚠️ No se encontraron cuentas visibles en la UI.")
            return

        cuentas_excel_limpias = {
            int(re.sub(r"\D", "", str(c.get("NROCUENTA", "")).strip())): c
            for c in self.contexto.get("cuentas", []) if str(c.get("NROCUENTA", "")).strip().isdigit()
        }

        self.logger.info("📄 Cuentas limpias del Excel:")
        for nro in cuentas_excel_limpias:
            self.logger.info(f" - {nro}")

        for cuenta_ui in cuentas_en_ui:
            try:
                texto_ui = (await cuenta_ui.inner_text()).replace("\xa0", " ").replace("\u00a0", " ").strip().upper()
                posibles = re.findall(r"\d{6,}", texto_ui)
                if not posibles:
                    self.logger.debug(f"⚠️ No se detectó número de cuenta en: {texto_ui}")
                    continue
                nro_ui = int(posibles[0])
            except Exception as e:
                self.logger.debug(f"⚠️ Error al procesar UI: {e}")
                continue

            if nro_ui in cuentas_excel_limpias:
                cuenta_excel = cuentas_excel_limpias[nro_ui]
                self.logger.info(f"🟢 Coincidencia: UI={nro_ui} == Excel={cuenta_excel['NROCUENTA']}")
                rutas = self.contexto.get("rutas_por_cuenta", {})
                clave = generar_clave_cuenta(cuenta_excel)
                ruta = rutas.get(clave)
                if ruta:
                    ruta_completa = ruta[0] if isinstance(ruta, tuple) else ruta
                    self.logger.info(f"📁 Ruta para guardar: {ruta_completa}")
                    self.ruta_salida = ruta_completa
                    self.contexto["ruta_descarga"] = ruta_completa
                else:
                    self.logger.error(f"❌ No se encontró una ruta válida para la cuenta: {clave}")
                    continue
                await cuenta_ui.click()
                await self.run_flow(pasos_descarga)
            else:
                self.logger.warning(f"⚠️ Cuenta en UI no encontrada en Excel: {nro_ui}")

    async def execute_step(self, step):
        action = step.get("action")
        try:
            selector = self.get_selector(step.get("target")) if step.get("target") else None
            value = self.resolve_variable(step.get("value")) if step.get("value") else None

            if action == "goto":
                self.logger.info(f"🌍 Navegando a {value}")
                await self.page.goto(value, timeout=60000, wait_until="domcontentloaded")

            elif action == "fill":
                self.logger.info(f"📝 Llenando {selector} con '{value}'")
                await self.page.fill(selector, value)

            elif action == "type":
                await self.page.click(selector)
                await self.page.fill(selector, "")
                await self.page.type(selector, value, delay=100)
                self.logger.info(f"⌨️ Escribiendo (type) en {selector}: {value}")

            elif action == "click":
                self.logger.info(f"🖱️ Click en {selector}")
                await self.page.click(selector)

            elif action == "wait_for":
                self.logger.info(f"⏳ Esperando selector {selector}")
                await self.page.wait_for_selector(selector)

            elif action == "wait_time":
                tiempo = int(value) if value else 1000
                self.logger.info(f"⏳ Esperando {tiempo}ms")
                await self.page.wait_for_timeout(tiempo)

            elif action == "keyboard_press":
                await self.page.keyboard.press(value)
                self.logger.info(f"⌨️ Presionada tecla: {value}")

            elif action == "type_virtual_password":
                from application.actions.basa_actions import BasaActions
                executor = BasaActions(self.credentials, self.selectors, flow={}, contexto=self.contexto)
                await executor.ingresar_password_virtual(self.page, self.credentials["password"])

            elif action == "type_virtual_pin":
                from application.actions.itau_actions import ItauActions
                executor = ItauActions(self.credentials, self.selectors, flow={}, contexto=self.contexto)
                await executor.ingresar_pin_virtual(self.page, self.credentials["password"])

            elif action == "descargar_y_guardar":
                ruta = self.resolve_variable(value)
                if not ruta:
                    raise ValueError("❌ 'ruta_descarga' no está definido o es vacío.")
                self.logger.info(f"⬇️ Esperando descarga en: {ruta}")
                await self.esperar_y_guardar_descarga(selector, ruta)

            else:
                self.logger.warning(f"⚠️ Acción desconocida: {action}")

        except Exception as e:
            self.logger.error(f"❌ Error al ejecutar acción '{action}': {e}")
            raise

    async def run_flow(self, flow: list):
        for step in flow:
            action = step.get("action")
            target = step.get("target")
            value = step.get("value")
            print(f"[⚙️] Ejecutando: {action} -> {target or ''} = {value or ''}")
            await self.execute_step(step)
