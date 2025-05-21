import logging
from datetime import datetime
from utils.config import (
    get_credentials,
    load_selectors,
    load_flow,
    BASE_DIR
)
from services.periodo_services import generar_periodo
from services.ruta_service import generar_ruta_archivo, generar_clave_cuenta
from services.context_service import ContextoEjecucion
from services.cuentas_services import obtener_cuentas_por_banco
from infrastructure.browser.browser_manager import BrowserManager
from domain.strategy_factory import get_strategy

class BankProcessor:
    def __init__(self, nombre_banco):
        self.logger = logging.getLogger(__name__)
        self.nombre_banco = nombre_banco.lower()
        self.credentials = get_credentials(self.nombre_banco)
        self.selectors = load_selectors().get(self.nombre_banco)
        self.flow = load_flow(self.nombre_banco)
        self.cuentas = obtener_cuentas_por_banco(self.nombre_banco)
        self.fecha_inicio, self.fecha_fin, self.mes = generar_periodo()
        self.logger.info(f"Fecha calculada para fecha_fin: {self.fecha_fin}")
        self.base_dir = BASE_DIR

        if not self.selectors:
            raise ValueError(f"❌ Selectores no definidos para banco: {self.nombre_banco}")

    async def ejecutar(self):
        self.logger.info(f"🚀 Iniciando procesamiento para banco: {self.nombre_banco.upper()}")
        browser = BrowserManager(headless=False)
        browser.nombre_banco = self.nombre_banco

        page = await browser.get_new_page()

        try:
            rutas_por_cuenta = {}
            for cuenta in self.cuentas:
                clave = generar_clave_cuenta(cuenta)
                rutas_por_cuenta[clave] = generar_ruta_archivo(
                    base_dir=self.base_dir,
                    banco=self.nombre_banco,
                    tipo_archivo="EXTRACTO",
                    tipo_cuenta=cuenta.get("TIPOCUENTA", ""),
                    nro_cuenta=cuenta.get("NROCUENTA", ""),
                    tipo_moneda=cuenta.get("MONEDA", ""),
                    fecha=self.fecha_fin
                )

            contexto = ContextoEjecucion(
                cuentas=self.cuentas,
                fecha_inicio=self.fecha_inicio.strftime("%Y-%m-%d"),
                fecha_fin=self.fecha_fin.strftime("%Y-%m-%d"),
                fecha_inicio2=self.fecha_inicio.strftime("%d/%m/%Y"),  # <- NUEVO
                fecha_fin2=self.fecha_fin.strftime("%d/%m/%Y"),        # <- NUEVO
                mes=self.mes,
                banco=self.nombre_banco,
                base_dir=self.base_dir,
                rutas_por_cuenta=rutas_por_cuenta,
                dia_inicio=str(self.fecha_inicio.day),
                dia_fin=str(self.fecha_fin.day)
            )

            self.logger.info("Obteniendo estrategia para el banco.")
            strategy = get_strategy(
                self.nombre_banco,
                self.credentials,
                self.selectors,
                self.flow,
                contexto
            )

            if hasattr(strategy, "set_contexto"):
                self.logger.info("Configurando contexto en la estrategia.")
                strategy.set_contexto(**contexto.to_dict())

            self.logger.info("Iniciando login.")

            if self.nombre_banco in ["sudameris"]:
                await strategy.login(page, browser)
            else:
                await strategy.login(page)

            self.logger.info("Login completado.")

            self.logger.info("Ejecutando pre-descarga.")
            await strategy.pre_download(page)
            self.logger.info("Pre-descarga completada.")

            self.logger.info("Iniciando descarga de reportes.")
            await strategy.descargar_reportes(page)
            self.logger.info("Descarga de reportes completada.")

            self.logger.info("Iniciando logout.")
            await strategy.logout(page)
            self.logger.info("Logout completado.")

            self.logger.info(f"✅ Procesamiento finalizado para banco: {self.nombre_banco.upper()}")

        except Exception as e:
            self.logger.exception(f"❌ Error durante ejecución del banco {self.nombre_banco.upper()}: {e}")

        finally:
            self.logger.info("Cerrando navegador.")
            await browser.close_browser()
