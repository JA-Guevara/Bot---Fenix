from domain.login_interface import LoginStrategy
import re
import logging

from infrastructure.executors.action_executor import ActionExecutor
from services.ruta_service import generar_clave_cuenta

import logging

class SudamerisActions(LoginStrategy):
    def __init__(self, credentials, selectors, flow,contexto):
        self.logger = logging.getLogger(__name__)
        self.credentials = credentials
        self.selectors = selectors
        self.flow = flow
        self.contexto = contexto

    async def login(self, page,browser):
        self.logger.info("🌐 Login Banco Sudameris...")
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["login"])

        
    async def pre_download(self, page):
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["pre_download"])

    async def descargar_reportes(self, page):
        
        executor = ActionExecutor(page, self.selectors, self.credentials)
        executor.set_contexto(**self.contexto.to_dict())

        await self.descargar_reportes_sudameris(page, self.flow["download"], executor)

    async def logout(self, page):
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["logout"])
        
    
    async def descargar_reportes_sudameris(self, page, pasos_descarga: list, executor: ActionExecutor):
        self.page = page
        list_selector = self.selectors["step_2"].get("list_selector")
        cuenta_selector = self.selectors["step_2"].get("cuenta_selector")
        tipo_selector = self.selectors["step_2"].get("tipo_selector")
        moneda_selector = self.selectors["step_2"].get("moneda_selector")

        if not list_selector or not cuenta_selector or not tipo_selector or not moneda_selector:
            self.logger.error("❌ Faltan selectores necesarios para cuenta, tipo o moneda.")
            return

        tipo_map = {
            "CUENTAS CORRIENTES": "CC",
            "CAJA DE AHORROS": "CA"
        }

        moneda_map = {
            "USD": "USD",
            "GS": "GS",
            "PYG": "GS"
        }

        cuentas_excel = executor.contexto.get("cuentas", [])
        processed_cuentas = set()

        while True:
            elementos = await self.page.query_selector_all(list_selector)
            if not elementos:
                self.logger.warning("⚠️ No se encontraron cuentas visibles en el DOM.")
                break

            avanzar = False

            for elemento in elementos:
                try:
                    nodo_cuenta = await elemento.query_selector(cuenta_selector)
                    nodo_tipo = await elemento.query_selector(tipo_selector)
                    nodo_moneda = await elemento.query_selector(moneda_selector)

                    nro_dom = re.sub(r"\D", "", await nodo_cuenta.inner_text())
                    tipo_ui = (await nodo_tipo.inner_text()).strip().upper()
                    moneda_ui = (await nodo_moneda.inner_text()).strip().upper()

                    tipo_dom = tipo_map.get(tipo_ui, "")
                    moneda_dom = moneda_map.get(moneda_ui, "")

                    clave_dom = f"{nro_dom}-{tipo_dom}-{moneda_dom}"
                    if not nro_dom or clave_dom in processed_cuentas:
                        continue

                    self.logger.info(f"🌐 DOM extraído → NRO: {nro_dom} | TIPO: {tipo_ui} ({tipo_dom}) | MONEDA: {moneda_ui} ({moneda_dom})")

                except Exception as e:
                    self.logger.info(f"❌ Error extrayendo datos del DOM: {e}")
                    continue

                for c in cuentas_excel:
                    log_nro = re.sub(r"\D", "", str(c.get("NROCUENTA", "")).strip())
                    log_tipo = str(c.get("TIPOCUENTA", "")).strip().upper()
                    log_moneda = str(c.get("MONEDA", "")).strip().upper()
                    self.logger.info(f"📄 EXCEL row → NRO: {log_nro} | TIPO: {log_tipo} | MONEDA: {log_moneda}")
                    self.logger.info(f"🔍 Comparando: DOM({nro_dom}, {tipo_dom}, {moneda_dom}) == Excel({log_nro}, {log_tipo}, {log_moneda})")

                cuenta_match = next(
                    (
                        c for c in cuentas_excel
                        if re.sub(r"\D", "", str(c.get("NROCUENTA", "")).strip()) == nro_dom
                        and str(c.get("TIPOCUENTA", "")).strip().upper() == tipo_dom
                        and str(c.get("MONEDA", "")).strip().upper() == moneda_dom
                    ),
                    None
                )

                if not cuenta_match:
                    self.logger.info(f"⚪ Cuenta {nro_dom} con tipo {tipo_ui} y moneda {moneda_ui} no coincide con Excel.")
                    processed_cuentas.add(clave_dom)
                    continue

                clave = generar_clave_cuenta(cuenta_match)
                rutas_por_cuenta = executor.contexto.get("rutas_por_cuenta", {})
                ruta = rutas_por_cuenta.get(clave)

                if not ruta:
                    self.logger.warning(f"⚠️ Ruta no encontrada para clave: {clave}")
                    processed_cuentas.add(clave_dom)
                    continue

                executor.contexto["ruta_descarga"] = ruta[0] if isinstance(ruta, tuple) else ruta
                self.logger.info(f"🟢 Coincidencia completa DOM={nro_dom} → Excel={cuenta_match['NROCUENTA']}")

                try:
                    await elemento.click()
                    await executor.run_flow(pasos_descarga)

                except Exception as e:
                    self.logger.error(f"❌ Error al procesar cuenta {nro_dom}: {e}")
                finally:
                    processed_cuentas.add(clave_dom)
                    avanzar = True
                    break

            if not avanzar:
                break
