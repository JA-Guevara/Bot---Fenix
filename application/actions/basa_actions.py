import logging
import re
from domain.login_interface import LoginStrategy
from infrastructure.executors.action_executor import ActionExecutor
from services.ruta_service import generar_clave_cuenta

class BasaActions(LoginStrategy):
    def __init__(self, credentials, selectors, flow,contexto):
        self.logger = logging.getLogger(__name__)
        self.credentials = credentials
        self.selectors = selectors
        self.flow = flow
        self.contexto = contexto

    async def login(self, page):
        self.logger.info("🌐 Login Banco Basa...")
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["login"])

    
    async def pre_download(self, page):
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["pre_download"])

    async def descargar_reportes(self, page):
        
        executor = ActionExecutor(page, self.selectors, self.credentials)
        executor.set_contexto(**self.contexto.to_dict())

        await self.descargar_reportes_basa(page, self.flow["download"], executor)


    async def logout(self, page):
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["logout"])


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
                    await page.wait_for_timeout(50)
                    break

            if not encontrada:
                visibles = [(await t.inner_text()).strip() for t in teclas]
                self.logger.error(f"❌ No se encontró tecla con valor visible: {char} | Teclas visibles: {visibles}")
                raise Exception(f"❌ No se pudo ingresar el carácter: {char}")
            
            
    async def descargar_reportes_basa(self, page,pasos_descarga: list,executor: ActionExecutor):
        self.page = page
        list_selector = self.selectors["step_2"].get("list_selector")
        button_selector = self.selectors["step_2"].get("action_button_selector")
        button_text = self.selectors["step_2"].get("action_button_text", "").strip().lower()

        if not list_selector or not button_selector or not button_text:
            self.logger.error("❌ Faltan selectores necesarios.")
            return

        contenedores = await self.page.query_selector_all(list_selector)
        if not contenedores:
            self.logger.warning("⚠️ No se encontraron contenedores.")
            return

        cuentas_excel = {
            int(re.sub(r"\D", "", str(c.get("NROCUENTA", "")).strip())): c
            for c in (getattr(self.contexto, "cuentas", []) or []) if str(c.get("NROCUENTA", "")).strip().isdigit()
        }

        for contenedor in contenedores:
            try:
                texto = (await contenedor.inner_text()).replace("\xa0", " ").upper()
                posibles = re.findall(r"\d{6,}", texto)
                if not posibles:
                    continue
                nro_cuenta = int(posibles[0])
                cuenta = cuentas_excel.get(nro_cuenta)
                if not cuenta:
                    continue

                self.logger.info(f"✅ Coincidencia: UI={nro_cuenta} == Excel={cuenta['NROCUENTA']}")
                clave = generar_clave_cuenta(cuenta)
                rutas_por_cuenta = getattr(self.contexto, "rutas_por_cuenta", {}) or {}
                ruta = rutas_por_cuenta.get(clave)
                if not ruta:
                    continue

                self.ruta_salida = ruta[0] if isinstance(ruta, tuple) else ruta
                executor.contexto["ruta_descarga"] = self.ruta_salida



                botones = await contenedor.query_selector_all(button_selector)
                for boton in botones:
                    texto_boton = (await boton.inner_text()).strip().lower()
                    if button_text in texto_boton:
                        await boton.click()
                        await executor.run_flow(pasos_descarga)
                        break
            except Exception as e:
                self.logger.error(f"❌ Error procesando contenedor: {e}")
