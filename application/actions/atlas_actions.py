import logging
import re
from domain.login_interface import LoginStrategy
from infrastructure.executors.action_executor import ActionExecutor
from services.ruta_service import generar_clave_cuenta

class AtlasActions(LoginStrategy):  # hereda LoginStrategy para mantener el contrato
    def __init__(self, credentials, selectors, flow,contexto):
        self.logger = logging.getLogger(__name__)
        self.credentials = credentials
        self.selectors = selectors
        self.flow = flow
        self.contexto = contexto

    async def login(self, page):
        self.logger.info("🌐 Login Banco Atlas...")
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["login"])

    async def pre_download(self, page):
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["pre_download"])

    async def descargar_reportes(self, page):
        
        executor = ActionExecutor(page, self.selectors, self.credentials)
        executor.set_contexto(**self.contexto.to_dict())
        await self.descargar_reportes_atlas(page, self.flow["download"], executor)

    async def logout(self, page):
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["logout"])
        
    async def descargar_reportes_atlas(self, page,pasos_descarga: list,executor: ActionExecutor):
        self.page = page
        list_selector = self.selectors["step_2"].get("list_selector")
        button_selector = self.selectors["step_2"].get("action_button_selector")
        button_text = self.selectors["step_2"].get("action_button_text", "").strip().lower()

        if not list_selector or not button_selector or not button_text:
            self.logger.error("❌ Parámetros 'list_selector', 'action_button_selector' o 'action_button_text' están incompletos.")
            return

        cuentas_excel = {
            int(re.sub(r"\D", "", str(c.get("NROCUENTA", "")).strip())): c
            for c in executor.contexto.get("cuentas", []) if str(c.get("NROCUENTA", "")).strip().isdigit()
        }


        while True:
            contenedores = await self.page.query_selector_all(list_selector)
            if not contenedores:
                self.logger.warning("⚠️ No se encontraron contenedores de cuentas.")
                return

            cuentas_en_ui = []
            for contenedor in contenedores:
                try:
                    texto_contenedor = (await contenedor.inner_text()).replace("\xa0", " ").upper()
                    posibles = re.findall(r"\d{6,}", texto_contenedor)
                    if not posibles:
                        continue
                    nro_cuenta = int(posibles[0])
                    cuentas_en_ui.append((nro_cuenta, contenedor))
                except:
                    continue

            if not cuentas_en_ui:
                self.logger.warning("⚠️ No se detectaron cuentas en el DOM.")
                return

            for nro_cuenta, _ in cuentas_en_ui:
                # Recarga la vista para evitar referencias inválidas
                await self.page.goto("https://secure.atlas.com.py/atlasdigital/account/list")
                await self.page.wait_for_selector(list_selector)
                await self.page.wait_for_timeout(1000)

                contenedores_actualizados = await self.page.query_selector_all(list_selector)

                contenedor_objetivo = None
                for contenedor in contenedores_actualizados:
                    texto_contenedor = (await contenedor.inner_text()).replace("\xa0", " ").upper()
                    if str(nro_cuenta) in texto_contenedor:
                        contenedor_objetivo = contenedor
                        break

                if not contenedor_objetivo:
                    self.logger.warning(f"❌ Contenedor no encontrado para cuenta {nro_cuenta}")
                    continue

                cuenta = cuentas_excel.get(nro_cuenta)
                if not cuenta:
                    self.logger.info(f"🔸 Cuenta {nro_cuenta} no encontrada en Excel.")
                    continue

                clave = generar_clave_cuenta(cuenta)
                ruta = executor.contexto.get("rutas_por_cuenta", {}).get(clave)

                if not ruta:
                    self.logger.warning(f"🚫 No se encontró ruta para {clave}")
                    continue

                self.ruta_salida = ruta[0] if isinstance(ruta, tuple) else ruta
                executor.contexto["ruta_descarga"] = self.ruta_salida

                self.logger.info(f"📁 Usando ruta: {self.ruta_salida}")

                botones = await contenedor_objetivo.query_selector_all(button_selector)
                boton_clickable = None
                for boton in botones:
                    try:
                        texto_boton = (await boton.inner_text()).strip().lower()
                        if button_text in texto_boton:
                            boton_clickable = boton
                            break
                    except:
                        continue

                if boton_clickable:
                    try:
                        await boton_clickable.click()
                        await executor.run_flow(pasos_descarga)

                    except Exception as e:
                        self.logger.error(f"❌ Error al hacer click: {e}")
                        continue
                else:
                    self.logger.warning(f"❌ No se encontró botón con texto '{button_text}' en cuenta {nro_cuenta}")

            break

