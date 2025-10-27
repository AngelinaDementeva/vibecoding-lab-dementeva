#!/usr/bin/env python3
"""
Скрипт для запуска бота с планировщиком ежедневных рассылок
"""

import asyncio
import logging
import signal
import sys
from bot import NewsBot
from scheduler import NewsScheduler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class BotRunner:
    """Класс для запуска бота и планировщика."""
    
    def __init__(self):
        """Инициализация."""
        self.bot = None
        self.scheduler = None
        self.running = False
    
    async def start_services(self):
        """Запуск всех сервисов."""
        try:
            # Создаем экземпляры
            self.bot = NewsBot()
            self.scheduler = NewsScheduler()
            
            # Запускаем планировщик в фоне
            scheduler_task = asyncio.create_task(self.scheduler.run_scheduler())
            
            # Запускаем бота
            await self.bot.run_async()
            
        except Exception as e:
            logger.error(f"Ошибка запуска сервисов: {e}")
            raise
    
    def signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения."""
        logger.info("Получен сигнал завершения, останавливаем сервисы...")
        self.running = False
        sys.exit(0)
    
    def run(self):
        """Запуск всех сервисов."""
        # Настраиваем обработчики сигналов
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            self.running = True
            asyncio.run(self.start_services())
        except KeyboardInterrupt:
            logger.info("Получен сигнал прерывания")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
        finally:
            logger.info("Завершение работы...")

def main():
    """Главная функция."""
    runner = BotRunner()
    runner.run()

if __name__ == '__main__':
    main()

