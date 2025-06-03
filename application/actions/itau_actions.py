import logging
import re
from infrastructure.executors.action_executor import ActionExecutor
from services.ruta_service import generar_clave_cuenta

class ItauActions:
    def __init__(self, credentials, selectors, flow, contexto):
        self.logger = logging.getLogger(__name__)
        self.credentials = credentials
        self.selectors = selectors
        self.flow = flow
        self.contexto = contexto

    async def login(self, page):
        self.logger.info("🌐 Login Banco Itau...")
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["login"])

    async def pre_download(self, page):
        # No es necesario usar este método, la pre-descarga está integrada por cuenta.
        pass

    async def descargar_reportes(self, page):
        executor = ActionExecutor(page, self.selectors, self.credentials)
        executor.set_contexto(**self.contexto.to_dict())
        pasos_descarga = self.flow["download"]  # mismo para ambas

        # 👉 Pre-descarga CUENTAS CORRIENTES
        self.logger.info("🧭 Pre-descarga CUENTAS CORRIENTES")
        await executor.run_flow(self.flow["pre_download_cc"])
        await page.wait_for_timeout(1000)

        # 👉 Descargar CUENTAS CORRIENTES
        self.logger.info("⬇️ Descargando CUENTAS CORRIENTES")
        await self.descargar_reportes_itau(page, pasos_descarga, executor, tipo_cuenta="CC")

        # 👉 Pre-descarga CAJA DE AHORROS
        self.logger.info("🧭 Pre-descarga CAJA DE AHORROS")
        await executor.run_flow(self.flow["pre_download_ca"])
        await page.wait_for_timeout(1000)

        # 👉 Descargar CAJA DE AHORROS
        self.logger.info("⬇️ Descargando CAJA DE AHORROS")
        await self.descargar_reportes_itau(page, pasos_descarga, executor, tipo_cuenta="CA")
 

    async def logout(self, page):
        executor = ActionExecutor(page, self.selectors, self.credentials)
        await executor.run_flow(self.flow["logout"])

    async def ingresar_pin_virtual(self, page, password):
        self.logger.info("🔐 Ingresando PIN virtual...")
        await page.wait_for_selector('#teclado_borrar', timeout=10000)

        for char in password:
            encontrada = False
            teclas = await page.query_selector_all('ul#tecladoBoxDivIdDefault_numeros > li.numeros')

            for tecla in teclas:
                texto = (await tecla.inner_text()).strip()
                if texto == char:
                    await tecla.click()
                    self.logger.info(f"🟢 Presionado: {char}")
                    encontrada = True
                    await page.wait_for_timeout(100)
                    break

            if not encontrada:
                visibles = [(await t.inner_text()).strip() for t in teclas]
                self.logger.error(f"❌ No se encontró tecla con valor: {char} | Visibles: {visibles}")
                raise Exception(f"❌ Fallo al ingresar dígito: {char}")

    async def descargar_reportes_itau(self, page, pasos_descarga: list, executor: ActionExecutor, tipo_cuenta: str):
        cuentas_excel = executor.contexto.get("cuentas", [])
        processed_cuentas = set()

        list_selector = 'button.accountsSlider'  # ✅ Selector común
        elementos = await page.query_selector_all(list_selector)
        if not elementos:
            self.logger.warning(f"⚠️ No se encontraron elementos para tipo: {tipo_cuenta}")
            return

        for elemento in elementos:
            try:
                texto = await elemento.inner_text()
                nro_dom = re.sub(r"\D", "", texto)
                moneda_dom = "USD" if "USD" in texto else "GS"
                clave_dom = f"{nro_dom}-{tipo_cuenta}-{moneda_dom}"

                if not nro_dom or clave_dom in processed_cuentas:
                    continue

                self.logger.info(f"🌐 DOM → NRO: {nro_dom} | TIPO: {tipo_cuenta} | MONEDA: {moneda_dom}")
            except Exception as e:
                self.logger.warning(f"❌ Error extrayendo datos del DOM: {e}")
                continue

            cuenta_match = next(
                (
                    c for c in cuentas_excel
                    if re.sub(r"\D", "", str(c.get("NROCUENTA", "")).strip()) == nro_dom
                    and str(c.get("TIPOCUENTA", "")).strip().upper() == tipo_cuenta
                    and str(c.get("MONEDA", "")).strip().upper() == moneda_dom
                ),
                None
            )

            if not cuenta_match:
                self.logger.info(f"⚪ Cuenta {nro_dom} ({tipo_cuenta}, {moneda_dom}) no coincide con Excel.")
                processed_cuentas.add(clave_dom)
                continue

            clave = generar_clave_cuenta(cuenta_match)
            ruta = executor.contexto.get("rutas_por_cuenta", {}).get(clave)

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
