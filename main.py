from infrastructure.logger.logging_config import setup_logging
setup_logging()

import asyncio
import logging
from task.task_manager import TaskManager

logger = logging.getLogger(__name__)

bancos = ["atlas"]

async def main():
    logger.info("Iniciando el proceso principal.")
    task = TaskManager()
    logger.info(f"Procesando los siguientes bancos: {bancos}")
    await task.ejecutar_bancos(bancos)
    logger.info("Proceso principal finalizado.")

if __name__ == "__main__":
    logger.info("Ejecutando main.py.")
    asyncio.run(main())
