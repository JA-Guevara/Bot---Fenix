import logging
import re
import os
from datetime import datetime
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

        selector_modal = self.selectors["step_3"].get("button_aceptar")

        try:
            # Esperar que el botón esté visible
            await self.page.wait_for_selector(selector, state="visible", timeout=10000)
            self.logger.info(f"🔍 Selector localizado: {selector}")

            # Iniciar escucha de descarga
            async with self.page.expect_download(timeout=15000) as download_info:
                await self.page.click(selector)
                self.logger.info(f"🖱️ Click en botón de descarga: {selector}")

            download = await download_info.value

            # Obtener extensión real del archivo descargado
            suggested_filename = download.suggested_filename
            extension_real = os.path.splitext(suggested_filename)[1].lower()

            # Validar que sea .xls o .xlsx
            if extension_real not in [".xls", ".xlsx"]:
                self.logger.error(f"❌ El archivo descargado tiene una extensión no válida: {extension_real}")
                raise ValueError(f"❌ El archivo descargado no es Excel: {suggested_filename}")

            # Guardar con la extensión correcta
            ruta_base, _ = os.path.splitext(ruta_destino)
            ruta_destino_final = f"{ruta_base}{extension_real}"

            await download.save_as(ruta_destino_final)
            self.logger.info(f"✅ Archivo guardado como: {ruta_destino_final}")
            self.contexto["descarga_exitosa"] = True

        except Exception as descarga_error:
            self.logger.warning("⚠️ No se detectó ninguna descarga. Verificando si apareció el modal de error...")

            try:
                await self.page.wait_for_selector(selector_modal, state="visible", timeout=3000)
                self.logger.warning("⚠️ Modal detectado. Haciendo click en botón aceptar...")
                await self.page.click(selector_modal)
                self.contexto["sin_descarga"] = True
                return
            except Exception:
                self.logger.error("❌ No se detectó el modal de error. Posible fallo inesperado.")
                raise descarga_error



    async def seleccionar_opcion_dropdown(self, target: str, value: str):
        try:
            paso, campo = target.split(".")
            selector = self.selectors.get(paso, {}).get(campo)

            if not selector:
                self.logger.error(f"❌ Selector no encontrado para {target}")
                return

            # Esperar a que esté en el DOM y visible
            try:
                await self.page.wait_for_selector(selector, state="visible", timeout=10000)
            except:
                self.logger.warning(f"⚠️ El selector {selector} no se mostró en 10s, se intenta igual...")

            elemento = await self.page.query_selector(selector)
            if not elemento:
                self.logger.error(f"❌ Elemento no encontrado para selector: {selector}")
                return

            tag_name = (await (await elemento.get_property("tagName")).json_value()).lower()

            # CASO 1: <select> nativo
            if tag_name == "select":
                await self.page.select_option(selector, value=value)
                self.logger.info(f"✅ Valor seleccionado en <select>: {value}")
                return

            # CASO 2: Click en dropdown visual
            try:
                await self.page.click(selector, force=True)
                self.logger.info(f"📂 Dropdown desplegado con {selector}")
            except Exception as e:
                self.logger.warning(f"⚠️ No se pudo hacer click en dropdown: {e}")

            # Estrategias posibles para localizar opción
            posibles_opciones = [
                f"{selector} >> text={value}",
                f"text=\"{value}\"",
                f"li >> text={value}",
                f"div[role='option']:has-text('{value}')",
                f"div.ui-menu-item-wrapper:has-text('{value}')",
                f"button.dropdown-item:has-text('{value}')",
            ]

            for opcion_selector in posibles_opciones:
                try:
                    opcion = self.page.locator(opcion_selector).first
                    await opcion.wait_for(state="visible", timeout=3000)
                    await opcion.click()
                    self.logger.info(f"✅ Opción seleccionada vía: {opcion_selector}")
                    return
                except Exception as e:
                    self.logger.debug(f"🔁 Falló intento con {opcion_selector}: {e}")
                    continue

            # Intento final: buscar por texto directamente en pantalla (menos preciso)
            try:
                elementos = await self.page.locator(f"text={value}").element_handles()
                for el in elementos:
                    try:
                        await el.click()
                        self.logger.info(f"✅ Click final en texto directo: {value}")
                        return
                    except:
                        continue
            except:
                pass

            self.logger.error(f"❌ No se logró seleccionar '{value}' con ninguna estrategia para {target}")

        except Exception as e:
            self.logger.error(f"❌ Error inesperado al seleccionar '{value}' en '{target}': {e}")

             
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

                try:
                    # Esperar a que el selector sea visible
                    elemento = await self.page.wait_for_selector(selector, state="visible", timeout=10000)
                    # Esperar a que el input no esté deshabilitado
                    await self.page.wait_for_function("element => !element.disabled", arg=elemento, timeout=5000)
                    # Hacer scroll hasta el campo por si está fuera de pantalla
                    await elemento.scroll_into_view_if_needed()
                    # Limpiar primero el campo (opcional)
                    await self.page.fill(selector, "")
                    # Finalmente, escribir
                    await self.page.fill(selector, value)
                    self.logger.info(f"✅ Campo llenado correctamente: {selector}")
                except Exception as e:
                    self.logger.error(f"❌ Error al llenar campo {selector}: {e}")


            elif action == "type":
                await self.page.click(selector)
                await self.page.fill(selector, "")
                await self.page.type(selector, value, delay=100)
                self.logger.info(f"⌨️ Escribiendo (type) en {selector}: {value}")

            elif action == "click":
                self.logger.info(f"🖱️ Intentando click en {selector}")
                try:
                    # Esperar a que el selector esté presente en el DOM (aunque no visible aún)
                    await self.page.wait_for_selector(selector, timeout=20000)

                    # Intentar esperar visibilidad y disponibilidad normal
                    try:
                        elemento = await self.page.wait_for_selector(selector, state="visible", timeout=5000)
                        await self.page.wait_for_function("el => !el.disabled", arg=elemento, timeout=2000)
                        await elemento.scroll_into_view_if_needed()
                        await elemento.click(force=True)
                        self.logger.info(f"✅ Click exitoso en {selector}")
                    except Exception as e_visibilidad:
                        self.logger.warning(f"⚠️ Elemento no visible o no interactivo: {e_visibilidad}")
                        self.logger.info(f"🛠️ Intentando forzar click con JavaScript en {selector}...")
                        await self.page.evaluate(f'''
                            const el = document.querySelector("{selector}");
                            if (el) el.click();
                        ''')
                        self.logger.info(f"✅ Click forzado con JS en {selector}")

                except Exception as e:
                    self.logger.error(f"❌ Error al hacer click en {selector}: {e}")

            elif action == "wait_for":
                self.logger.info(f"⏳ Esperando selector {selector}")
                await self.page.wait_for_selector(selector)
                
            elif action == "buscar":
                self.logger.info(f"🔍 Buscando selector {selector} con timeout extendido")
                try:
                    await self.page.wait_for_selector(selector, timeout=30000, state="visible")
                    self.logger.info(f"✅ Selector encontrado: {selector}")
                except Exception as e:
                    self.logger.error(f"❌ No se encontró el selector {selector} en el tiempo esperado: {e}")

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
            
            elif action == "verificar_y_ejecutar":
                mensaje_selector = step.get("target")
                acciones = step.get("acciones", [])

                try:
                    await self.page.wait_for_selector(mensaje_selector, timeout=5000)
                    self.logger.info(f"🔔 Modal detectado: {mensaje_selector}")

                    for substep in acciones:
                        await self.execute_step(substep)  # ✅ Reutiliza tu lógica central
                    self.logger.info("✅ Acciones ejecutadas tras detectar el modal")
                    self.contexto["descarga_finalizada"] = True
                except Exception:
                    self.logger.info("✅ No se detectó modal, flujo continúa normalmente")

                
            elif action == "seleccionar_opcion_dropdown":
                await self.seleccionar_opcion_dropdown(step.get("target"), value)

            else:
                self.logger.warning(f"⚠️ Acción desconocida: {action}")
            

        except Exception as e:
            self.logger.error(f"❌ Error al ejecutar acción '{action}': {e}")
            raise
        
    def _parse_value(self, value: str) -> str:

        if isinstance(value, str) and value.startswith("$"):
            variable_name = value[1:]
            resolved = self.credentials.get(variable_name) or self.contexto.get(variable_name)
            if resolved is None:
                raise ValueError(f"⚠️ Variable '{variable_name}' no encontrada en credentials ni contexto.")
            return str(resolved)
        return value
    

    async def run_flow(self, flow: list):
        for step in flow:
            action = step.get("action")
            target = step.get("target")
            value = step.get("value")
            print(f"[⚙️] Ejecutando: {action} -> {target or ''} = {value or ''}")
            await self.execute_step(step)
