#!/usr/bin/env python3
"""
Планировщик для ежедневной рассылки новостей
Запускается отдельно от основного бота
"""

import asyncio
import logging
import os
from datetime import datetime, time
from telegram import Bot
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class NewsScheduler:
    """Планировщик для ежедневной рассылки новостей."""
    
    def __init__(self):
        """Инициализация планировщика."""
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        
        self.bot = Bot(token=self.token)
        self.data_dir = 'data'
        self.users_file = os.path.join(self.data_dir, 'users.json')
        self.news_file = os.path.join(self.data_dir, 'news.json')
    
    def _load_data(self, file_path: str):
        """Загрузка данных из JSON файла."""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Ошибка загрузки данных из {file_path}: {e}")
            return {}
    
    async def send_daily_digest(self):
        """Отправка ежедневного дайджеста подписчикам."""
        try:
            users_data = self._load_data(self.users_file)
            subscribers = users_data.get('subscribers', [])
            
            if not subscribers:
                logger.info("Нет подписчиков для ежедневной рассылки")
                return
            
            # Получаем новости
            news_data = self._load_data(self.news_file)
            news_list = news_data.get('news', [])
            
            if not news_list:
                logger.warning("Нет новостей для ежедневной рассылки")
                return
            
            digest_text = f"""
🌅 **Доброе утро! Ежедневный дайджест новостей**

📰 Сегодня у нас {len(news_list)} свежих новостей:

"""
            
            for i, news in enumerate(news_list[:5], 1):  # Показываем топ-5 новостей
                digest_text += f"**{i}. {news['title']}**\n"
                digest_text += f"📝 {news['description'][:100]}...\n"
                digest_text += f"🏷️ {news['category']} | 📰 {news['source']}\n"
                digest_text += f"🔗 [Читать далее]({news['url']})\n\n"
            
            digest_text += "Используйте /news для просмотра всех новостей или /favorites для избранного!"
            
            # Отправляем дайджест всем подписчикам
            for user_id in subscribers:
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=digest_text,
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                    logger.info(f"Дайджест отправлен пользователю {user_id}")
                except Exception as e:
                    logger.error(f"Ошибка отправки дайджеста пользователю {user_id}: {e}")
            
        except Exception as e:
            logger.error(f"Ошибка отправки ежедневного дайджеста: {e}")
    
    async def run_scheduler(self):
        """Запуск планировщика."""
        logger.info("Запуск планировщика ежедневных рассылок...")
        
        while True:
            try:
                current_time = datetime.now().time()
                target_time = time(9, 0)  # 9:00 утра
                
                # Проверяем, нужно ли отправить рассылку
                if current_time.hour == target_time.hour and current_time.minute == target_time.minute:
                    await self.send_daily_digest()
                    # Ждем минуту, чтобы не отправить повторно
                    await asyncio.sleep(60)
                else:
                    # Ждем 30 секунд перед следующей проверкой
                    await asyncio.sleep(30)
                    
            except Exception as e:
                logger.error(f"Ошибка в планировщике: {e}")
                await asyncio.sleep(60)

def main():
    """Главная функция планировщика."""
    try:
        scheduler = NewsScheduler()
        asyncio.run(scheduler.run_scheduler())
    except Exception as e:
        logger.error(f"Критическая ошибка планировщика: {e}")

if __name__ == '__main__':
    main()

