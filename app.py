import asyncio
from infrastructure.executors.bank_processor import BankProcessor
 
from infrastructure.logger.logging_config import setup_logging

setup_logging()

async def test_procesar_basa():
    processor = BankProcessor("basa")
    
    print("📌 Fechas generadas:")
    print(f"Fecha inicio: {processor.fecha_inicio}")
    print(f"Fecha fin: {processor.fecha_fin}")
    print(f"Mes: {processor.mes}")
    
    print("\n📌 Cuentas a procesar:")
    for cuenta in processor.cuentas:
        print(cuenta)

    print("\n📁 Probando generación de nombre y ruta por cuenta:")
    for cuenta in processor.cuentas:
        ruta = generar_ruta_archivo(
            base_dir=processor.base_dir,
            banco=processor.nombre_banco,
            tipo_archivo="EXTRACTO",
            tipo_cuenta=cuenta["TIPOCUENTA"],
            nro_cuenta=str(cuenta["NROCUENTA"]),
            tipo_moneda=cuenta["MONEDA"]
        )
        print(f"📄 Ruta completa: {ruta}")

    print("\n🚀 Ejecutando proceso completo (login, descarga, logout)...")
    await processor.ejecutar()

if __name__ == "__main__":
    asyncio.run(test_procesar_basa())
