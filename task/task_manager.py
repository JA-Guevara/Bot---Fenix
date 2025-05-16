from infrastructure.executors.bank_processor import BankProcessor

class TaskManager:
    async def ejecutar_bancos(self, bancos: list):
        for nombre_banco in bancos:
            print(f"🚀 Procesando banco: {nombre_banco.upper()}")
            processor = BankProcessor(nombre_banco)
            await processor.ejecutar()
