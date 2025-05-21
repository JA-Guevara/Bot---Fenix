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

        # Selectores del modal de error
        selector_modal = self.selectors["step_3"].get("button_aceptar")
        selector_boton = self.selectors["step_3"].get("button_aceptar")
        try:
            # ⏳ Intentar la descarga
            async with self.page.expect_download(timeout=15000) as download_info:
                await self.page.click(selector)
                self.logger.info(f"🖱️ Click en botón de descarga: {selector}")

            download = await download_info.value
            await download.save_as(ruta_destino)
            self.logger.info(f"✅ Archivo guardado como: {ruta_destino}")
            self.contexto["descarga_exitosa"] = True

        except Exception as descarga_error:
            self.logger.warning("⚠️ No se detectó ninguna descarga. Verificando si apareció el modal de error...")

            try:
                await self.page.wait_for_selector(selector_boton, state="visible", timeout=3000)
                self.logger.warning(f"⚠️ Modal detectado. Haciendo click en botón aceptar...")
                await self.page.click(selector_boton)
                self.contexto["sin_descarga"] = True
                return
            except Exception:
                self.logger.error("❌ No se detectó el modal de error. Posible fallo inesperado.")
                raise descarga_error

    async def descargar_reportes(self, pasos_descarga: list, banco: str):
        banco = banco.lower().strip()

        if banco == "continental":
            await self.descargar_reportes_continental(self.page, pasos_descarga)
            return
        elif banco == "basa":
            await self.descargar_reportes_basa(pasos_descarga)
            return
        elif banco == "sudameris":
            await self.descargar_reportes_sudameris(pasos_descarga)
            return
        elif banco == "gnb":
            await self.descargar_reportes_gnb(pasos_descarga)
            return
        elif banco == "atlas":
            await self.descargar_reportes_atlas(pasos_descarga)
            return
        elif banco == "itau":
            await self.descargar_reportes_itau(pasos_descarga)
            return
        else:
            self.logger.warning(f"⚠️ Banco '{banco}' no tiene lógica personalizada. Ejecutando método genérico.")
            await self.descargar_reportes_generico(pasos_descarga)
    

    async def descargar_reportes_gnb(self, pasos_descarga: list):
        list_selector = self.selectors["step_2"].get("list_selector")  # este debería ser el selector del <em>
        if not list_selector:
            self.logger.error("❌ Falta 'list_selector' en los selectores del paso 2.")
            return

        cuentas_excel = {
            int(re.sub(r"\D", "", str(c.get("NROCUENTA", "")).strip())): c
            for c in self.contexto.get("cuentas", []) if str(c.get("NROCUENTA", "")).strip().isdigit()
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
                ruta = self.contexto.get("rutas_por_cuenta", {}).get(clave)
                if not ruta:
                    self.logger.warning(f"⚠️ Ruta no encontrada para clave: {clave}")
                    processed_cuentas.add(nro_cuenta)
                    continue

                self.contexto["ruta_descarga"] = ruta[0] if isinstance(ruta, tuple) else ruta

                try:
                    # 🔁 Subimos al padre TD (clickable), ya que el <em> no tiene click.
                    contenedor_click = await elemento.evaluate_handle("el => el.closest('td')")
                    await contenedor_click.click()
                    await self.run_flow(pasos_descarga)
                except Exception as e:
                    self.logger.error(f"❌ Error al procesar cuenta {nro_cuenta}: {e}")
                finally:
                    processed_cuentas.add(nro_cuenta)
                    avanzar = True
                    break  # vuelve al while para actualizar elementos del DOM después del flujo

            if not avanzar:
                break

        
    async def descargar_reportes_continental(self, page, pasos_descarga: list):
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

        cuentas_excel = {
            str(c.get("NROCUENTA", "")).strip(): c
            for c in self.contexto.get("cuentas", [])
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
                self.ruta_salida = self.contexto.get("rutas_por_cuenta", {}).get(clave, self.contexto.get("base_dir"))
                self.contexto["ruta_descarga"] = self.ruta_salida
                self.logger.info(f"📁 Ruta descarga: {self.ruta_salida}")

                # 👉 Ejecutar pasos
                await self.run_flow(pasos_descarga)

            except Exception as e:
                self.logger.error(f"❌ Error con cuenta {nro_original}: {e}")
                
    async def descargar_reportes_basa(self, pasos_descarga: list):
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
            for c in self.contexto.get("cuentas", []) if str(c.get("NROCUENTA", "")).strip().isdigit()
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
                ruta = self.contexto.get("rutas_por_cuenta", {}).get(clave)
                if not ruta:
                    continue

                self.ruta_salida = ruta[0] if isinstance(ruta, tuple) else ruta
                self.contexto["ruta_descarga"] = self.ruta_salida

                botones = await contenedor.query_selector_all(button_selector)
                for boton in botones:
                    texto_boton = (await boton.inner_text()).strip().lower()
                    if button_text in texto_boton:
                        await boton.click()
                        await self.run_flow(pasos_descarga)
                        break
            except Exception as e:
                self.logger.error(f"❌ Error procesando contenedor: {e}")

    async def descargar_reportes_atlas(self, pasos_descarga: list):
        list_selector = self.selectors["step_2"].get("list_selector")
        button_selector = self.selectors["step_2"].get("action_button_selector")
        button_text = self.selectors["step_2"].get("action_button_text", "").strip().lower()

        if not list_selector or not button_selector or not button_text:
            self.logger.error("❌ Parámetros 'list_selector', 'action_button_selector' o 'action_button_text' están incompletos.")
            return

        cuentas_excel = {
            int(re.sub(r"\D", "", str(c.get("NROCUENTA", "")).strip())): c
            for c in self.contexto.get("cuentas", []) if str(c.get("NROCUENTA", "")).strip().isdigit()
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
                ruta = self.contexto.get("rutas_por_cuenta", {}).get(clave)
                if not ruta:
                    self.logger.warning(f"🚫 No se encontró ruta para {clave}")
                    continue

                self.ruta_salida = ruta[0] if isinstance(ruta, tuple) else ruta
                self.contexto["ruta_descarga"] = self.ruta_salida
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
                        await self.run_flow(pasos_descarga)
                    except Exception as e:
                        self.logger.error(f"❌ Error al hacer click: {e}")
                        continue
                else:
                    self.logger.warning(f"❌ No se encontró botón con texto '{button_text}' en cuenta {nro_cuenta}")

            break


    async def seleccionar_opcion_dropdown(self, target: str, value: str):
        try:
            paso, campo = target.split(".")
            selector = self.selectors.get(paso, {}).get(campo)
            if not selector:
                self.logger.error(f"❌ Selector no encontrado para {target}")
                return

            self.logger.info(f"📅 Abriendo dropdown con selector: {selector}")
            await self.page.click(selector)


            # Esperar que se despliegue y aparezca la opción con el texto deseado
            opcion_selector = f"text={value}"
            await self.page.wait_for_selector(opcion_selector, timeout=12000)
            await self.page.click(opcion_selector)
            self.logger.info(f"✅ Opción seleccionada: {value}")

        except Exception as e:
            self.logger.error(f"❌ Error al seleccionar opción en dropdown para '{target}': {e}")

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
