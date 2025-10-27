#!/usr/bin/env python3
"""
Простой тестовый бот для проверки команды /favorites
"""

import os
import json
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TestBot:
    """Простой тестовый бот."""
    
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.users_file = 'data/users.json'
    
    def _load_data(self, file_path: str):
        """Загрузка данных из JSON файла."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Ошибка загрузки данных из {file_path}: {e}")
            return {}
    
    async def favorites_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /favorites."""
        try:
            user_id = update.effective_user.id
            logger.info(f"Пользователь {user_id} запросил избранные новости")
            
            users_data = self._load_data(self.users_file)
            favorites = users_data.get('favorites', {}).get(str(user_id), [])
            
            if not favorites:
                await update.message.reply_text("❌ У вас нет сохраненных новостей.")
                return
            
            await update.message.reply_text(f"❤️ Ваши избранные новости ({len(favorites)} шт.):")
            
            for i, news in enumerate(favorites, 1):
                news_text = f"""
📰 **{i}. {news['title']}**

📝 {news['description']}

🏷️ Категория: {news['category']}
📰 Источник: {news['source']}
🔗 [Читать далее]({news['url']})
                """
                
                await update.message.reply_text(
                    news_text,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            
        except Exception as e:
            logger.error(f"Ошибка в команде favorites: {e}")
            await update.message.reply_text("❌ Произошла ошибка при загрузке избранных новостей.")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start."""
        await update.message.reply_text("Тестовый бот запущен! Используйте /favorites для проверки.")
    
    def run(self):
        """Запуск тестового бота."""
        application = Application.builder().token(self.token).build()
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("favorites", self.favorites_command))
        
        logger.info("Запуск тестового бота...")
        application.run_polling()

if __name__ == '__main__':
    bot = TestBot()
    bot.run()

