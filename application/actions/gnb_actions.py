# application/actions/gnb_actions.py
import logging
import re
from infrastructure.executors.action_executor import ActionExecutor
from services.ruta_service import generar_clave_cuenta

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
        
        await self.descargar_reportes_gnb(page, self.flow["download"], executor)


    async def logout(self, page):
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["logout"])

    async def descargar_reportes_gnb(self,page,pasos_descarga: list,executor: ActionExecutor):
        self.page = page
        list_selector = self.selectors["step_2"].get("list_selector")  # este debería ser el selector del <em>
        if not list_selector:
            self.logger.error("❌ Falta 'list_selector' en los selectores del paso 2.")
            return

        cuentas_excel = {
            int(re.sub(r"\D", "", str(c.get("NROCUENTA", "")).strip())): c
            for c in executor.contexto.get("cuentas", []) if str(c.get("NROCUENTA", "")).strip().isdigit()
        }

        processed_cuentas = set()

        while True:
            elementos_em = await self.page.query_selector_all(list_selector)
            if not elementos_em:
                self.logger.warning("⚠️ No se encontraron cuentas visibles en el DOM.")
                break

            avanzar = False

            for elemento in elementos_em:
                try:
                    nro_texto = (await elemento.inner_text()).strip()
                    nro_cuenta = int(re.sub(r"\D", "", nro_texto))
                except Exception as e:
                    self.logger.debug(f"❌ Error extrayendo número de cuenta: {e}")
                    continue

                if nro_cuenta in processed_cuentas:
                    continue

                cuenta = cuentas_excel.get(nro_cuenta)
                if not cuenta:
                    processed_cuentas.add(nro_cuenta)
                    continue

                self.logger.info(f"🟢 Coincidencia: UI={nro_cuenta} == Excel={cuenta['NROCUENTA']}")
                clave = generar_clave_cuenta(cuenta)
                rutas_por_cuenta = getattr(self.contexto, "rutas_por_cuenta", {})
                ruta = rutas_por_cuenta.get(clave)

                if not ruta:
                    self.logger.warning(f"⚠️ Ruta no encontrada para clave: {clave}")
                    processed_cuentas.add(nro_cuenta)
                    continue

                executor.contexto["ruta_descarga"] = ruta[0] if isinstance(ruta, tuple) else ruta


                try:
                    # 🔁 Subimos al padre TD (clickable), ya que el <em> no tiene click.
                    contenedor_click = await elemento.evaluate_handle("el => el.closest('td')")
                    await contenedor_click.click()
                    await executor.run_flow(pasos_descarga)

                except Exception as e:
                    self.logger.error(f"❌ Error al procesar cuenta {nro_cuenta}: {e}")
                finally:
                    processed_cuentas.add(nro_cuenta)
                    avanzar = True
                    break  # vuelve al while para actualizar elementos del DOM después del flujo

            if not avanzar:
                break

